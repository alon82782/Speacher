"""Step 2 — 캘리브레이션.

영상 첫 10초로 사용자/환경 기준값을 측정한다. 이후 step3~6은
ctx.results['calibration'].data 의 baseline 값을 기준으로 편차를 계산한다.

구간 설계
  0~3s   자세 캘리브레이션 (무음, 정자세)
         - SNR 잡음 측정
         - 어깨 기울기 / 중심점 / 너비 / 화면비율
         - 시선 홍채 오프셋
  3~10s  음성 캘리브레이션 (제시 문장 낭독)
         - SNR 신호 측정
         - RMS / 피치 기준값
  10s~   본 발표 — 분석 구간 (이후 단계에서 사용)

제시 문장: "안녕하세요, 지금부터 발표를 시작하겠습니다."

SNR 판정 (음향학 표준)
  ≥ 20dB     정상
  15~20dB    경고 → low_confidence
  < 15dB     분석 중단

실패 처리 — 측정 실패 시 분석 중단 (RuntimeError 로 전파)
  어깨 감지 5프레임 미만   → 0~10s 로 확장 후 재시도, 여전히 부족하면 중단
  시선 감지 5프레임 미만   → 중단
  유효 피치 없음           → 중단
  RMS < 0.005 (사실상 무음) → 중단
  오디오 디코딩 실패        → 중단
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import cv2
import librosa
import mediapipe as mp
import numpy as np

from app.services.analysis.context import PipelineContext, StepResult
from app.utils.logger import logger


STEP_KEY = "calibration"

CALIBRATION_PROMPT = "안녕하세요, 지금부터 발표를 시작하겠습니다."

# 구간 (초)
POSTURE_END_SEC: float = 3.0
VOICE_START_SEC: float = 3.0
VOICE_END_SEC: float = 10.0
ANALYSIS_START_SEC: float = 10.0
POSTURE_FALLBACK_END_SEC: float = 10.0  # 어깨 감지 폴백 구간

# 임계값
MIN_VALID_FRAMES: int = 5
SNR_NORMAL_DB: float = 20.0
SNR_WARNING_DB: float = 15.0
RMS_MIN: float = 0.005
SAMPLE_RATE: int = 16000


@dataclass
class CalibrationData:
    """step2 결과 — 후속 단계가 baseline 으로 참조.

    모든 baseline 필드는 측정 성공 시에만 채워진다 (실패 시 step2 가 raise).
    """
    # 자세
    tilt_baseline: float
    center_baseline: float
    shoulder_width: float
    frame_ratio: float
    posture_frames_used: int
    # 시선
    iris_offset_left: float
    iris_offset_right: float
    iris_frames_used: int
    # 음성
    rms_baseline: float
    pitch_baseline: float
    pitch_frames_used: int
    # SNR
    noise_rms: float
    signal_rms: float
    snr_db: float
    # 메타
    analysis_start_sec: float = ANALYSIS_START_SEC
    calibration_prompt: str = CALIBRATION_PROMPT
    low_confidence: bool = False
    fallbacks: list[str] = field(default_factory=list)


def run(ctx: PipelineContext) -> StepResult:
    ctx.update_progress(2, 5)
    logger.info(f"[Step2] 캘리브레이션 시작 — file={ctx.file_path.name}")

    fallbacks: list[str] = []

    posture = _calibrate_posture(ctx, fallbacks)
    ctx.update_progress(2, 35)

    iris = _calibrate_iris(ctx)
    ctx.update_progress(2, 55)

    audio = _calibrate_audio(ctx, fallbacks)
    ctx.update_progress(2, 100)

    cal = CalibrationData(
        **posture,
        **iris,
        **audio,
        low_confidence=("snr_warning" in fallbacks),
        fallbacks=fallbacks,
    )

    logger.info(
        f"[Step2] 완료 — SNR={cal.snr_db:.1f}dB, RMS={cal.rms_baseline:.4f}, "
        f"pitch={cal.pitch_baseline:.1f}Hz, fallbacks={cal.fallbacks}, "
        f"low_confidence={cal.low_confidence}"
    )
    return StepResult(step_key=STEP_KEY, data=asdict(cal))


# ============================================================
# 자세 (어깨)
# ============================================================
def _calibrate_posture(ctx: PipelineContext, fallbacks: list[str]) -> dict[str, Any]:
    samples = _read_pose_samples(ctx, end_sec=POSTURE_END_SEC)
    if len(samples) < MIN_VALID_FRAMES:
        logger.warning(
            f"[Step2] 0~{POSTURE_END_SEC:.0f}s 어깨 감지 {len(samples)}프레임 — "
            f"0~{POSTURE_FALLBACK_END_SEC:.0f}s 로 확장 재시도"
        )
        fallbacks.append("posture_extended_to_10s")
        samples = _read_pose_samples(ctx, end_sec=POSTURE_FALLBACK_END_SEC)

    if len(samples) < MIN_VALID_FRAMES:
        raise RuntimeError(
            f"calibration_failed: 어깨 감지 프레임 부족 ({len(samples)} < {MIN_VALID_FRAMES})"
        )

    return {
        "tilt_baseline": float(np.median([s["tilt"] for s in samples])),
        "center_baseline": float(np.median([s["center"] for s in samples])),
        "shoulder_width": float(np.median([s["width"] for s in samples])),
        "frame_ratio": float(np.median([s["frame_ratio"] for s in samples])),
        "posture_frames_used": len(samples),
    }


def _read_pose_samples(ctx: PipelineContext, *, end_sec: float) -> list[dict[str, float]]:
    cap = cv2.VideoCapture(str(ctx.file_path))
    if not cap.isOpened():
        logger.error(f"[Step2] 영상 열기 실패: {ctx.file_path}")
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    end_frame = int(end_sec * fps)

    samples: list[dict[str, float]] = []
    pose = mp.solutions.pose.Pose(model_complexity=0, enable_segmentation=False)
    try:
        idx = 0
        while idx < end_frame:
            ok, frame = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)
            if res.pose_landmarks:
                lm = res.pose_landmarks.landmark
                ls = lm[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
                rs = lm[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
                nose = lm[mp.solutions.pose.PoseLandmark.NOSE]
                if ls.visibility > 0.5 and rs.visibility > 0.5 and nose.visibility > 0.5:
                    mid_y = (ls.y + rs.y) / 2.0
                    samples.append({
                        # 양 어깨 y 차이. +면 영상기준 우어깨 처짐
                        "tilt": float(rs.y - ls.y),
                        # 양 어깨 가로 중앙 (0=좌, 1=우)
                        "center": float((ls.x + rs.x) / 2.0),
                        # 어깨 너비 / 프레임 가로
                        "width": float(abs(rs.x - ls.x)),
                        # 머리(코)~어깨 세로 길이 / 프레임 세로 (인물 크기 지표)
                        "frame_ratio": float(mid_y - nose.y),
                    })
            idx += 1
    finally:
        pose.close()
        cap.release()
    return samples


# ============================================================
# 시선 (홍채)
# ============================================================
def _calibrate_iris(ctx: PipelineContext) -> dict[str, Any]:
    samples = _read_iris_samples(ctx, end_sec=POSTURE_END_SEC)
    if len(samples) < MIN_VALID_FRAMES:
        raise RuntimeError(
            f"calibration_failed: 시선 감지 프레임 부족 ({len(samples)} < {MIN_VALID_FRAMES})"
        )
    return {
        "iris_offset_left": float(np.median([s["left"] for s in samples])),
        "iris_offset_right": float(np.median([s["right"] for s in samples])),
        "iris_frames_used": len(samples),
    }


def _read_iris_samples(ctx: PipelineContext, *, end_sec: float) -> list[dict[str, float]]:
    cap = cv2.VideoCapture(str(ctx.file_path))
    if not cap.isOpened():
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    end_frame = int(end_sec * fps)

    # FaceMesh refine_landmarks=True → 홍채 landmark (468~477) 활성화
    mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5,
    )
    samples: list[dict[str, float]] = []
    try:
        idx = 0
        while idx < end_frame:
            ok, frame = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = mesh.process(rgb)
            if res.multi_face_landmarks:
                lm = res.multi_face_landmarks[0].landmark
                # mediapipe 의 LEFT/RIGHT 라벨을 그대로 사용 (영상 기준 좌/우)
                left = _iris_offset(lm, iris_idx=468, outer_idx=33, inner_idx=133)
                right = _iris_offset(lm, iris_idx=473, outer_idx=263, inner_idx=362)
                if left is not None and right is not None:
                    samples.append({"left": left, "right": right})
            idx += 1
    finally:
        mesh.close()
        cap.release()
    return samples


def _iris_offset(landmarks: Any, *, iris_idx: int, outer_idx: int, inner_idx: int) -> float | None:
    """홍채 중심이 눈 가로축 어디에 있는지 0~1로 정규화. 0.5=정중앙."""
    iris = landmarks[iris_idx]
    outer = landmarks[outer_idx]
    inner = landmarks[inner_idx]
    span = inner.x - outer.x
    if abs(span) < 1e-6:
        return None
    return float((iris.x - outer.x) / span)


# ============================================================
# 음성 (SNR / RMS / 피치)
# ============================================================
def _calibrate_audio(ctx: PipelineContext, fallbacks: list[str]) -> dict[str, Any]:
    try:
        noise, _ = librosa.load(
            str(ctx.file_path), sr=SAMPLE_RATE,
            offset=0.0, duration=POSTURE_END_SEC, mono=True,
        )
        signal, _ = librosa.load(
            str(ctx.file_path), sr=SAMPLE_RATE,
            offset=VOICE_START_SEC, duration=VOICE_END_SEC - VOICE_START_SEC,
            mono=True,
        )
    except Exception as exc:
        logger.error(f"[Step2] 오디오 로드 실패: {exc}")
        raise RuntimeError(f"calibration_failed: audio_load_failed: {exc}") from exc

    noise_rms = float(np.sqrt(np.mean(noise.astype(np.float64) ** 2))) if noise.size else 0.0
    signal_rms = float(np.sqrt(np.mean(signal.astype(np.float64) ** 2))) if signal.size else 0.0

    # SNR 산출 — 잡음 RMS 가 사실상 0이면 SNR 무한대로 보고 60dB 로 캡
    if noise_rms < 1e-6:
        snr_db = 60.0
    else:
        snr_db = float(20.0 * np.log10(max(signal_rms, 1e-12) / noise_rms))

    # SNR 판정
    if snr_db < SNR_WARNING_DB:
        raise RuntimeError(
            f"calibration_failed: SNR {snr_db:.1f}dB < {SNR_WARNING_DB:.0f}dB"
        )
    if snr_db < SNR_NORMAL_DB:
        fallbacks.append("snr_warning")

    # RMS 임계값 미달 — 사실상 무음, 분석 불가
    if signal_rms < RMS_MIN:
        raise RuntimeError(
            f"calibration_failed: 음성 RMS {signal_rms:.4f} < {RMS_MIN} (사실상 무음)"
        )

    pitch_hz, pitch_frames = _estimate_pitch(signal)

    return {
        "noise_rms": noise_rms,
        "signal_rms": signal_rms,
        "snr_db": snr_db,
        "rms_baseline": signal_rms,
        "pitch_baseline": pitch_hz,
        "pitch_frames_used": pitch_frames,
    }


def _estimate_pitch(signal: np.ndarray) -> tuple[float, int]:
    if signal.size == 0:
        raise RuntimeError("calibration_failed: 음성 신호 비어있음")
    try:
        # pyin: 사람 음역(C2~C6) 안에서 voiced 구간 f0 추정. unvoiced 는 NaN.
        f0, _, _ = librosa.pyin(
            signal, sr=SAMPLE_RATE,
            fmin=librosa.note_to_hz("C2"),  # 약 65Hz
            fmax=librosa.note_to_hz("C6"),  # 약 1047Hz
        )
    except Exception as exc:
        logger.error(f"[Step2] pyin 실패: {exc}")
        raise RuntimeError(f"calibration_failed: pyin 실패: {exc}") from exc

    valid = f0[~np.isnan(f0)]
    if valid.size == 0:
        raise RuntimeError("calibration_failed: 유효 피치 없음")
    return float(np.median(valid)), int(valid.size)
