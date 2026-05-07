"""Step 5 — 음성 분석 (현재: 말하기 속도 SPM).

VAD 로 의도적 정적을 제외한 순수 발화 시간 동안의 음절 속도를 측정한다.
음절 수는 사전 단계(step4 audio_extract 또는 step6 speech)에서 채워둔
한글 전사를 사용한다 — step5 자체는 Whisper 를 호출하지 않는다.

SPM = 총 음절 수 / 순수 발화 시간(분)

VAD
  librosa.effects.split(y, top_db=30)  — 내부적으로 frame 단위 RMS 를 dB 로 변환해
  최대 진폭 대비 top_db dB 이상 작은 구간을 무음으로 본다.
  top_db = 30 은 실측 후 조정 예정.

기준 (음절/분)
  양호 : 280 ≤ SPM ≤ 360                                  → 20점
  경고 : 240 ≤ SPM < 280  또는  360 < SPM ≤ 410           → 12점
  위험 : SPM < 240        또는  SPM > 410                 →  5점
  (점수 만점은 config.SCORE_SPEECH_RATE = 20 과 일치)

레퍼런스 (참고용)
  신승용·현숙자 (2003) 음성과학 — 읽기 평균 348 SPM / 말하기 평균 265 SPM
  한국언어치료학회 (2021) — 아나운서 평균 355 SPM

호출자 주의
  audio_path 와 transcript 는 동일한 시간 범위를 가리켜야 한다.
  (예: 둘 다 본 발표 구간 10s~ 의 데이터, 또는 둘 다 전체 오디오)
"""
from __future__ import annotations

import librosa
import numpy as np

from app.services.analysis.context import PipelineContext, StepResult
from app.utils.logger import logger


STEP_KEY = "audio_analyze"

SAMPLE_RATE: int = 16000

# VAD — 실측 후 조정 예정
VAD_TOP_DB: float = 30.0

# SPM 기준 (음절/분)
SPM_GOOD_MIN: float = 280.0
SPM_GOOD_MAX: float = 360.0
SPM_WARN_LOW_MIN: float = 240.0
SPM_WARN_HIGH_MAX: float = 410.0

# 점수 (config.SCORE_SPEECH_RATE = 20 만점)
SPM_SCORE_GOOD: float = 20.0
SPM_SCORE_WARN: float = 12.0
SPM_SCORE_DANGER: float = 5.0


def run(ctx: PipelineContext) -> StepResult:
    ctx.update_progress(5, 5)

    audio_path = _get_audio_path(ctx)
    transcript = _get_transcript(ctx)

    syllables = count_korean_syllables(transcript)
    ctx.update_progress(5, 30)

    speech_seconds = vad_speech_seconds(audio_path, top_db=VAD_TOP_DB)
    ctx.update_progress(5, 80)

    spm = compute_spm(syllables, speech_seconds)
    grade = spm_grade(spm)
    score = spm_score(grade)

    ctx.update_progress(5, 100)
    logger.info(
        f"[Step5] SPM — syllables={syllables}, speech={speech_seconds:.2f}s, "
        f"SPM={spm:.1f}, grade={grade}, score={score:.0f}/{SPM_SCORE_GOOD:.0f}"
    )

    return StepResult(
        step_key=STEP_KEY,
        data={
            "spm": {
                "value": spm,
                "syllables": syllables,
                "speech_seconds": speech_seconds,
                "top_db": VAD_TOP_DB,
                "grade": grade,
                "score": score,
            },
        },
    )


# ============================================================
# 외부 입력 — audio_path, transcript
# ============================================================
def _get_audio_path(ctx: PipelineContext) -> str:
    """step4 audio_extract 결과의 추출 오디오 파일 경로."""
    extract = ctx.results.get("audio_extract")
    if extract is None or "audio_path" not in extract.data:
        raise RuntimeError(
            "step5 prerequisite missing: ctx.results['audio_extract'].data['audio_path']"
        )
    return str(extract.data["audio_path"])


def _get_transcript(ctx: PipelineContext) -> str:
    """한글 전사 — step4(audio_extract) 혹은 step6(speech) 에서 채워둔 transcript."""
    for key in ("audio_extract", "speech"):
        result = ctx.results.get(key)
        if result is not None and "transcript" in result.data:
            return str(result.data["transcript"])
    raise RuntimeError(
        "step5 prerequisite missing: transcript not found in "
        "ctx.results['audio_extract' | 'speech'].data['transcript']"
    )


# ============================================================
# SPM 핵심 로직 — 모두 pure function (테스트·재사용 용이)
# ============================================================
def vad_speech_seconds(audio_path: str, *, top_db: float = VAD_TOP_DB) -> float:
    """librosa.effects.split 으로 무음을 제거한 순수 발화 시간(초)."""
    y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    if y.size == 0:
        return 0.0
    intervals = librosa.effects.split(y, top_db=top_db)
    if intervals.size == 0:
        return 0.0
    total_samples = int(np.sum(intervals[:, 1] - intervals[:, 0]))
    return float(total_samples / sr)


def count_korean_syllables(text: str) -> int:
    """한글 음절(U+AC00 ~ U+D7A3) 개수. 공백·구두점·비-한글은 제외."""
    return sum(1 for c in text if 0xAC00 <= ord(c) <= 0xD7A3)


def compute_spm(syllables: int, speech_seconds: float) -> float:
    """SPM = 음절 / 분. 발화 시간이 0 이하면 0."""
    if speech_seconds <= 0:
        return 0.0
    return syllables / (speech_seconds / 60.0)


def spm_grade(spm: float) -> str:
    if SPM_GOOD_MIN <= spm <= SPM_GOOD_MAX:
        return "good"
    if SPM_WARN_LOW_MIN <= spm < SPM_GOOD_MIN or SPM_GOOD_MAX < spm <= SPM_WARN_HIGH_MAX:
        return "warn"
    return "danger"


def spm_score(grade: str) -> float:
    if grade == "good":
        return SPM_SCORE_GOOD
    if grade == "warn":
        return SPM_SCORE_WARN
    return SPM_SCORE_DANGER
