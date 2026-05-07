"""Step 6 — 음성 콘텐츠 분석 (필러 워드 + 발음 정확성).

──────────────────────── 필러 워드 ────────────────────────
유형 분류
  그룹 A — STT 단어 매칭 (Whisper 토큰 단위)
    발성: 음, 어, 아            (0.3s 미만이면 에너지 검증 생략)
    단어: 그, 뭐, 막, 좀, 약간
    문구: 그러니까, 이제, 뭔가
  그룹 B — 정규식 어미 매칭 (Whisper 토큰들을 이어붙인 텍스트에 적용)
    ~이잖아요, ~거든요, ~인데요
  그룹 C — librosa.effects.split 침묵
    2초 이상 무음 → step7 GPT 피드백에만 전달, 점수 미반영

전처리
  Whisper 단어: re.sub(r"[.,!?…\\s]", "", word).strip()  로 특수문자·공백 제거
  Whisper 신뢰도 임계 0.4 (재현율 향상)
  0.3초 미만 짧은 발성은 RMS 에너지 검증 생략 (Whisper 출력 그대로 신뢰)

점수 (config.SCORE_FILLER_WORD = 15 만점, 분당 개수 기준)
  분당 ≤ 2개 → 15점 (good)
  분당 ≤ 5개 →  9점 (warn)
  분당  > 5개 →  3점 (danger)

──────────────────────── 발음 정확성 ────────────────────────
측정 방식
  스크립트 있음 (ctx.script) → jiwer 로 WER 직접 산출
  스크립트 없음               → Whisper word probability 평균 → 추정 WER = 1 - avg_conf

WER 기준
  WER ≤ 10% → good
  WER ≤ 20% → warn
  WER  > 20% → danger

점수 (config.SCORE_PRONUNCIATION = 10 만점)
  score = (1 - WER) × 10                  (0~10 클램프)

신뢰도 flag (점수 무관, low_confidence 표시용)
  step2 SNR 15~20dB 경고 시         → "snr_low_confidence"
  스크립트 없이 추정으로 산출 시    → "estimated_low_confidence"
  → 추정은 신뢰도가 낮으므로 사용자에게 스크립트 입력을 강하게 권장.

레퍼런스 (참고용)
  필러: PubMed (2024) 영어 기준 분당 5개 이하 허용 가능
  발음: 한국어 전용 레퍼런스 없음 — 자체 실측 검증 예정
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

import jiwer
import librosa
import numpy as np

from app.services.analysis.context import PipelineContext, StepResult
from app.services.analysis.scoring import TimelineEntry
from app.utils.logger import logger


STEP_KEY = "speech"

# 그룹 A — STT 단어 매칭
GROUP_A_VOCALS = frozenset({"음", "어", "아"})
GROUP_A_WORDS = frozenset({"그", "뭐", "막", "좀", "약간"})
GROUP_A_PHRASES = frozenset({"그러니까", "이제", "뭔가"})

# 그룹 B — 정규식 어미
GROUP_B_PATTERN = re.compile(r"(이잖아요|거든요|인데요)")

# 그룹 C — 침묵
SILENCE_MIN_DURATION_SEC: float = 2.0
SILENCE_TOP_DB: float = 30.0  # 실측 후 조정 예정

# Whisper 후처리
WORD_CLEAN_PATTERN = re.compile(r"[.,!?…\s]")
WHISPER_CONFIDENCE_MIN: float = 0.4    # 재현율 향상 — 기본 0.5 에서 하향
SHORT_VOCAL_DURATION_SEC: float = 0.3  # 이 미만 짧은 발성은 RMS 검증 생략
ENERGY_RMS_MIN: float = 0.005          # 짧지 않은 발성 검증 시 RMS 임계
SAMPLE_RATE: int = 16000

# 점수 — 분당 개수
FILLER_PER_MIN_GOOD: float = 2.0
FILLER_PER_MIN_WARN: float = 5.0
FILLER_SCORE_GOOD: float = 15.0
FILLER_SCORE_WARN: float = 9.0
FILLER_SCORE_DANGER: float = 3.0

# 발음 정확성 (config.SCORE_PRONUNCIATION = 10 만점)
PRONUNCIATION_GOOD_MAX: float = 0.10   # WER ≤ 10% → good
PRONUNCIATION_WARN_MAX: float = 0.20   # WER ≤ 20% → warn
PRONUNCIATION_SCORE_MAX: float = 10.0
# WER 비교 시 양쪽 텍스트에서 제거할 비-단어/공백 외 문자 (구두점·이모지 등) 정규식
PRONUNCIATION_NORMALIZE_PATTERN = re.compile(r"[^\w\s]", flags=re.UNICODE)


@dataclass
class FillerEvent:
    group: str        # "A" | "B"
    kind: str         # "vocal" | "word" | "phrase" | "ending"
    token: str
    start_sec: float
    end_sec: float
    confidence: float


@dataclass
class SilenceEvent:
    start_sec: float
    end_sec: float
    duration_sec: float


def run(ctx: PipelineContext) -> StepResult:
    ctx.update_progress(6, 5)

    audio_path = _get_audio_path(ctx)
    words = _get_whisper_words(ctx)

    fillers_a = _detect_group_a(words, audio_path)
    ctx.update_progress(6, 30)

    fillers_b = _detect_group_b(words)
    ctx.update_progress(6, 50)

    silences = _detect_group_c(audio_path)
    ctx.update_progress(6, 70)

    pronunciation = _evaluate_pronunciation(ctx, words)
    ctx.update_progress(6, 95)

    fillers = fillers_a + fillers_b
    minutes = _get_speech_minutes(ctx, audio_path)
    per_minute = (len(fillers) / minutes) if minutes > 0 else 0.0
    grade = filler_grade(per_minute)
    score = filler_score(per_minute)
    timeline = [_filler_to_timeline(f) for f in fillers]

    ctx.update_progress(6, 100)
    logger.info(
        f"[Step6] 필러 — 총 {len(fillers)}개 (A:{len(fillers_a)}, B:{len(fillers_b)}), "
        f"분당 {per_minute:.2f}개, grade={grade}, score={score:.0f}/{FILLER_SCORE_GOOD:.0f}, "
        f"long_silences={len(silences)}건 (점수 미반영)"
    )
    logger.info(
        f"[Step6] 발음 — method={pronunciation['method']}, "
        f"WER={pronunciation['wer']:.1%}, score={pronunciation['score']:.2f}/"
        f"{PRONUNCIATION_SCORE_MAX:.0f}, grade={pronunciation['grade']}, "
        f"flags={pronunciation['flags']}"
    )

    return StepResult(
        step_key=STEP_KEY,
        data={
            "fillers": {
                "events": [asdict(f) for f in fillers],
                "count": len(fillers),
                "per_minute": per_minute,
                "minutes_basis": minutes,
                "grade": grade,
                "score": score,
                "by_group": {"A": len(fillers_a), "B": len(fillers_b)},
                "by_token": dict(Counter(f.token for f in fillers)),
            },
            "pronunciation": pronunciation,
            "long_silences": [asdict(s) for s in silences],  # step7 GPT 피드백 입력
            "timeline": timeline,                             # 그룹 A+B 만 (그룹 C 는 점수 미반영)
        },
    )


# ============================================================
# 외부 입력
# ============================================================
def _get_audio_path(ctx: PipelineContext) -> str:
    extract = ctx.results.get("audio_extract")
    if extract is None or "audio_path" not in extract.data:
        raise RuntimeError(
            "step6 prerequisite missing: ctx.results['audio_extract'].data['audio_path']"
        )
    return str(extract.data["audio_path"])


def _get_whisper_words(ctx: PipelineContext) -> list[dict]:
    """Whisper 단어 단위 출력 — [{'word', 'start', 'end', 'probability'}, ...]."""
    for key in ("audio_extract", "transcribe", "speech"):
        result = ctx.results.get(key)
        if result is not None and "whisper_words" in result.data:
            return list(result.data["whisper_words"])
    raise RuntimeError(
        "step6 prerequisite missing: whisper_words not found in "
        "ctx.results['audio_extract' | 'transcribe' | 'speech'].data['whisper_words']"
    )


def _get_speech_minutes(ctx: PipelineContext, audio_path: str) -> float:
    """분당 환산 분모 — step5 의 speech_seconds 가 있으면 재사용, 없으면 오디오 전체 길이."""
    audio_analyze = ctx.results.get("audio_analyze")
    if audio_analyze is not None and "spm" in audio_analyze.data:
        seconds = float(audio_analyze.data["spm"].get("speech_seconds", 0.0))
        if seconds > 0:
            return seconds / 60.0
    duration_sec = float(librosa.get_duration(path=audio_path))
    return duration_sec / 60.0 if duration_sec > 0 else 0.0


# ============================================================
# 그룹 A — STT 단어 매칭
# ============================================================
def clean_word(word: str) -> str:
    """Whisper 단어 출력에서 특수문자·공백 제거. 사용자 스펙 정규식 그대로."""
    return WORD_CLEAN_PATTERN.sub("", word).strip()


def _detect_group_a(words: list[dict], audio_path: str) -> list[FillerEvent]:
    events: list[FillerEvent] = []
    for w in words:
        prob = float(w.get("probability", 1.0))
        if prob < WHISPER_CONFIDENCE_MIN:
            continue
        token = clean_word(str(w.get("word", "")))
        if not token:
            continue

        if token in GROUP_A_VOCALS:
            duration = float(w["end"]) - float(w["start"])
            # 0.3초 미만 짧은 발성은 에너지 검증 생략
            if duration >= SHORT_VOCAL_DURATION_SEC:
                if not _verify_energy(audio_path, float(w["start"]), float(w["end"])):
                    continue
            kind = "vocal"
        elif token in GROUP_A_WORDS:
            kind = "word"
        elif token in GROUP_A_PHRASES:
            kind = "phrase"
        else:
            continue

        events.append(FillerEvent(
            group="A", kind=kind, token=token,
            start_sec=float(w["start"]), end_sec=float(w["end"]),
            confidence=prob,
        ))
    return events


def _verify_energy(audio_path: str, start_sec: float, end_sec: float) -> bool:
    """해당 구간의 RMS 가 ENERGY_RMS_MIN 이상이면 의미 있는 발성으로 본다.

    Whisper 가 무음 구간에 짧은 발성을 환각(hallucinate)하는 케이스를 거르기 위함.
    """
    duration = end_sec - start_sec
    if duration <= 0:
        return False
    try:
        y, _ = librosa.load(
            audio_path, sr=SAMPLE_RATE, mono=True,
            offset=start_sec, duration=duration,
        )
    except Exception as exc:
        logger.warning(f"[Step6] 에너지 검증 로드 실패: {exc}")
        return False
    if y.size == 0:
        return False
    rms = float(np.sqrt(np.mean(y.astype(np.float64) ** 2)))
    return rms > ENERGY_RMS_MIN


# ============================================================
# 그룹 B — 정규식 어미 매칭
# ============================================================
def _detect_group_b(words: list[dict]) -> list[FillerEvent]:
    text, char_to_word = _build_text_index(words)
    if not text:
        return []
    events: list[FillerEvent] = []
    for m in GROUP_B_PATTERN.finditer(text):
        start_word = char_to_word[m.start()]
        end_word = char_to_word[m.end() - 1]
        confs = [
            float(words[i].get("probability", 1.0))
            for i in range(start_word, end_word + 1)
        ]
        avg_conf = sum(confs) / len(confs) if confs else 1.0
        if avg_conf < WHISPER_CONFIDENCE_MIN:
            continue
        events.append(FillerEvent(
            group="B", kind="ending", token=m.group(0),
            start_sec=float(words[start_word]["start"]),
            end_sec=float(words[end_word]["end"]),
            confidence=avg_conf,
        ))
    return events


def _build_text_index(words: list[dict]) -> tuple[str, list[int]]:
    """단어 리스트를 정제된 텍스트 + 문자별 word index 로 변환.

    각 word.word 를 clean_word 로 정제해 이어붙이고, 결합된 텍스트의 char i 가
    어느 word index 에서 왔는지를 char_to_word[i] 에 기록. 정규식 매치 위치를
    원래 단어의 timestamp 로 역추적할 때 사용.
    """
    text = ""
    char_to_word: list[int] = []
    for word_idx, w in enumerate(words):
        cleaned = clean_word(str(w.get("word", "")))
        for _ in cleaned:
            char_to_word.append(word_idx)
        text += cleaned
    return text, char_to_word


# ============================================================
# 그룹 C — librosa 침묵 (점수 미반영, GPT 피드백 입력만)
# ============================================================
def _detect_group_c(audio_path: str) -> list[SilenceEvent]:
    try:
        y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    except Exception as exc:
        logger.warning(f"[Step6] 오디오 로드 실패 — 침묵 검출 스킵: {exc}")
        return []
    if y.size == 0:
        return []

    intervals = librosa.effects.split(y, top_db=SILENCE_TOP_DB)
    audio_duration = float(y.size / sr)

    silences: list[SilenceEvent] = []
    prev_end_sec = 0.0
    for start, end in intervals:
        gap_start = prev_end_sec
        gap_end = float(start / sr)
        if gap_end - gap_start >= SILENCE_MIN_DURATION_SEC:
            silences.append(SilenceEvent(
                start_sec=gap_start, end_sec=gap_end,
                duration_sec=gap_end - gap_start,
            ))
        prev_end_sec = float(end / sr)
    # 끝부분 무음
    if audio_duration - prev_end_sec >= SILENCE_MIN_DURATION_SEC:
        silences.append(SilenceEvent(
            start_sec=prev_end_sec, end_sec=audio_duration,
            duration_sec=audio_duration - prev_end_sec,
        ))
    return silences


# ============================================================
# 점수 / 등급 / 타임라인
# ============================================================
def filler_grade(per_minute: float) -> str:
    if per_minute <= FILLER_PER_MIN_GOOD:
        return "good"
    if per_minute <= FILLER_PER_MIN_WARN:
        return "warn"
    return "danger"


def filler_score(per_minute: float) -> float:
    if per_minute <= FILLER_PER_MIN_GOOD:
        return FILLER_SCORE_GOOD
    if per_minute <= FILLER_PER_MIN_WARN:
        return FILLER_SCORE_WARN
    return FILLER_SCORE_DANGER


def _filler_to_timeline(f: FillerEvent) -> TimelineEntry:
    return TimelineEntry(
        event_type="filler_word",
        timestamp_sec=f.start_sec,
        end_timestamp_sec=f.end_sec,
        severity=1,
        description=f"{f.kind}: {f.token}",
        extra_data={
            "group": f.group,
            "kind": f.kind,
            "token": f.token,
            "confidence": f.confidence,
        },
    )


# ============================================================
# 발음 정확성 — WER (스크립트 있음) / 추정 WER (스크립트 없음)
# ============================================================
def _evaluate_pronunciation(ctx: PipelineContext, words: list[dict]) -> dict[str, Any]:
    script = (ctx.script or "").strip()
    snr_warning = _is_snr_low_confidence(ctx)
    flags: list[str] = []
    avg_confidence: float | None = None

    if script:
        method = "script"
        hypothesis = _build_hypothesis_text(ctx, words)
        wer = _wer_from_script(script, hypothesis)
    else:
        method = "estimated"
        wer, avg_confidence = _estimated_wer_from_words(words)
        # 추정 방식은 본질적으로 신뢰도 낮음 — 스크립트 입력 강하게 권장
        flags.append("estimated_low_confidence")

    if snr_warning:
        flags.append("snr_low_confidence")

    return {
        "wer": wer,
        "score": pronunciation_score(wer),
        "grade": pronunciation_grade(wer),
        "method": method,                       # "script" | "estimated"
        "script_provided": bool(script),
        "avg_confidence": avg_confidence,       # estimated 일 때만 채워짐
        "snr_warning": snr_warning,
        "low_confidence": bool(flags),          # flag 가 하나라도 있으면 True
        "flags": flags,
    }


def _wer_from_script(reference: str, hypothesis: str) -> float:
    """jiwer.wer 직접 호출. 양쪽 모두 구두점·중복 공백 제거 후 비교, 결과는 [0, 1] 클램프."""
    ref = _normalize_for_wer(reference)
    hyp = _normalize_for_wer(hypothesis)
    if not ref or not hyp:
        return 1.0
    raw = float(jiwer.wer(ref, hyp))
    # jiwer 는 insertion 이 매우 많으면 1.0 초과 가능 — 점수가 음수가 되지 않도록 클램프
    return max(0.0, min(1.0, raw))


def _estimated_wer_from_words(words: list[dict]) -> tuple[float, float]:
    """Whisper word probability 평균을 confidence 로 보고 1 - avg_conf 로 WER 추정.

    no_speech_prob 가 segment 단위라 word 단위 probability 평균이 더 robust.
    값이 비어있으면 전부 인식 실패로 보고 WER=1.0.
    """
    confs = [
        float(w["probability"])
        for w in words
        if w.get("probability") is not None
    ]
    if not confs:
        return 1.0, 0.0
    avg_conf = sum(confs) / len(confs)
    wer = max(0.0, min(1.0, 1.0 - avg_conf))
    return wer, avg_conf


def _build_hypothesis_text(ctx: PipelineContext, words: list[dict]) -> str:
    """전사 텍스트 — ctx.results 의 full transcript 우선, 없으면 word 단위 재구성."""
    for key in ("audio_extract", "transcribe", "speech"):
        result = ctx.results.get(key)
        if result is not None and "transcript" in result.data:
            text = str(result.data["transcript"]).strip()
            if text:
                return text
    return " ".join(clean_word(str(w.get("word", ""))) for w in words).strip()


def _normalize_for_wer(text: str) -> str:
    """WER 비교 전 공통 정규화 — 구두점/이모지 제거, 중복 공백 축약, 양끝 strip."""
    text = PRONUNCIATION_NORMALIZE_PATTERN.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_snr_low_confidence(ctx: PipelineContext) -> bool:
    """step2 캘리브레이션의 low_confidence 플래그 — SNR 15~20dB 경고일 때 True."""
    cal = ctx.results.get("calibration")
    if cal is None:
        return False
    return bool(cal.data.get("low_confidence", False))


def pronunciation_grade(wer: float) -> str:
    if wer <= PRONUNCIATION_GOOD_MAX:
        return "good"
    if wer <= PRONUNCIATION_WARN_MAX:
        return "warn"
    return "danger"


def pronunciation_score(wer: float) -> float:
    score = (1.0 - wer) * PRONUNCIATION_SCORE_MAX
    return max(0.0, min(PRONUNCIATION_SCORE_MAX, score))
