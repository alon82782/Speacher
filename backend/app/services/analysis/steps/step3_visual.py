"""Step 3 — 시각 분석 (시선 처리율 + 자세 안정성).

step2 캘리브레이션 baseline 과 본 발표 구간(10s~) 프레임을 비교해
정면 응시 비율 / 자세 안정 비율을 산출하고 점수·타임라인 이벤트로 환산한다.

──────────────────────── 시선 ────────────────────────
판정
  좌·우 홍채 오프셋이 baseline ± 0.10 이내   → 정면 응시 (FRONT)
  벗어난 경우 우선순위로 분류: 이탈 → 대본 → 슬라이드 → 정면
    이탈    : |편차| > 0.30                            (실측 검증 예정)
    대본    : vertical 시선 정보 미도입 — 차후 추가
    슬라이드: 그 외 비-정면

점수
  score = front_ratio × 25                              (0~25, 비례)
  good   : front_ratio ≥ 0.60
  warn   : 0.40 ≤ front_ratio < 0.60
  danger : front_ratio < 0.40

타임라인 (10s 비중첩 윈도우 — 실측 검증 예정)
  구간 front_ratio < 0.60 → severity 1 (warn)
  구간 front_ratio < 0.40 → severity 2 (danger)

──────────────────────── 자세 ────────────────────────
판정
  보정 계수  = 0.3 / cal.frame_ratio  (캘리브레이션 시점 인물 크기 기준 정규화)
  tilt_dev   = |current_tilt   - tilt_baseline|   × 보정계수
  center_dev = |current_center - center_baseline| × 보정계수
  STABLE  : max(tilt_dev, center_dev) ≤ 0.10
  WARN    : 0.10 < max ≤ 0.25
  DANGER  : max > 0.25                              (모두 실측 검증 예정)

점수 (config.SCORE_POSTURE = 10 과 일치)
  stable_ratio ≥ 90%       → 10점
  75% ≤ stable_ratio < 90% →  6점
  stable_ratio < 75%       →  2점

레퍼런스
  없음 — 자체 실측 검증 예정.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import cv2
import mediapipe as mp

from app.services.analysis.context import PipelineContext, StepResult
from app.services.analysis.scoring import TimelineEntry
from app.services.analysis.steps.step2_calibration import ANALYSIS_START_SEC
from app.utils.logger import logger


STEP_KEY = "visual"

# ─── 시선 ─────────────────────────────────────────────
FRONT_TOLERANCE: float = 0.10                # 스펙 — 고정
ESCAPE_THRESHOLD: float = 0.30               # 실측 검증 예정
GAZE_FPS: int = 10                           # 실측 검증 예정 (다운샘플)
WARN_RATIO: float = 0.60
DANGER_RATIO: float = 0.40
WINDOW_DURATION_SEC: float = 10.0            # 실측 검증 예정
GAZE_SCORE_MAX: float = 25.0                 # config.SCORE_GAZE 와 일치

# ─── 자세 ─────────────────────────────────────────────
POSTURE_FPS: int = 10                        # 실측 검증 예정
POSTURE_STABLE_DEV: float = 0.10             # 실측 검증 예정
POSTURE_WARN_DEV: float = 0.25               # 실측 검증 예정
POSTURE_GOOD_RATIO: float = 0.90
POSTURE_WARN_RATIO: float = 0.75
POSTURE_SCORE_GOOD: float = 10.0             # config.SCORE_POSTURE 와 일치
POSTURE_SCORE_WARN: float = 6.0
POSTURE_SCORE_DANGER: float = 2.0
FRAME_RATIO_REFERENCE: float = 0.3           # 보정 계수 분자 — 기본 frame_ratio
MIN_FRAME_RATIO: float = 0.1                 # 보정 계수 발산 방지 하한
SHOULDER_VISIBILITY_MIN: float = 0.5         # mediapipe pose visibility 최소


class GazeState(str, Enum):
    FRONT = "front"
    SLIDE = "slide"
    SCRIPT = "script"
    ESCAPE = "escape"
    UNKNOWN = "unknown"


@dataclass
class GazeSample:
    timestamp_sec: float
    state: GazeState
    iris_left: float | None
    iris_right: float | None
    dev_left: float
    dev_right: float


class PoseState(str, Enum):
    STABLE = "stable"   # 안정
    WARN = "warn"       # 경고
    DANGER = "danger"   # 위험
    UNKNOWN = "unknown"


@dataclass
class PoseSample:
    timestamp_sec: float
    state: PoseState
    tilt: float | None
    center: float | None
    tilt_dev: float        # 보정 계수 적용된 값
    center_dev: float      # 보정 계수 적용된 값


def run(ctx: PipelineContext) -> StepResult:
    ctx.update_progress(3, 5)
    cal = _get_calibration(ctx)
    coef = _correction_coef(cal["frame_ratio"])

    # 시선 ────────────────────────────────────────────
    gaze_samples = _collect_gaze_samples(ctx, cal)
    ctx.update_progress(3, 50)
    front_ratio, gaze_breakdown = _summarize_gaze(gaze_samples)
    gaze_score = front_ratio * GAZE_SCORE_MAX
    gaze_grade = _gaze_grade(front_ratio)
    gaze_timeline = _build_gaze_timeline(gaze_samples)
    gaze_unknown = gaze_breakdown.get(GazeState.UNKNOWN.value, 0)
    gaze_low_conf = (
        len(gaze_samples) == 0
        or gaze_unknown / max(len(gaze_samples), 1) > 0.5
    )

    # 자세 ────────────────────────────────────────────
    pose_samples = _collect_pose_samples(ctx, cal, coef)
    ctx.update_progress(3, 95)
    stable_ratio, pose_breakdown = _summarize_posture(pose_samples)
    posture_score = _posture_score(stable_ratio)
    posture_grade = _posture_grade(stable_ratio)
    pose_unknown = pose_breakdown.get(PoseState.UNKNOWN.value, 0)
    pose_low_conf = (
        len(pose_samples) == 0
        or pose_unknown / max(len(pose_samples), 1) > 0.5
    )

    ctx.update_progress(3, 100)
    logger.info(
        f"[Step3] 시선 — front={front_ratio:.1%}, score={gaze_score:.2f}/{GAZE_SCORE_MAX:.0f}, "
        f"grade={gaze_grade}, samples={len(gaze_samples)} (unknown={gaze_unknown}), "
        f"events={len(gaze_timeline)}"
    )
    logger.info(
        f"[Step3] 자세 — stable={stable_ratio:.1%}, score={posture_score:.0f}/10, "
        f"grade={posture_grade}, samples={len(pose_samples)} (unknown={pose_unknown}), "
        f"frame_ratio={cal['frame_ratio']:.3f} → coef={coef:.3f}"
    )

    return StepResult(
        step_key=STEP_KEY,
        data={
            "gaze": {
                "front_ratio": front_ratio,
                "score": gaze_score,
                "grade": gaze_grade,
                "samples_count": len(gaze_samples),
                "states": gaze_breakdown,
                "low_confidence": gaze_low_conf,
            },
            "posture": {
                "stable_ratio": stable_ratio,
                "score": posture_score,
                "grade": posture_grade,
                "samples_count": len(pose_samples),
                "states": pose_breakdown,
                "correction_coef": coef,
                "low_confidence": pose_low_conf,
            },
            "timeline": gaze_timeline,  # 자세 타임라인은 추후 추가
        },
    )


# ============================================================
# 캘리브레이션 로드
# ============================================================
def _get_calibration(ctx: PipelineContext) -> dict[str, float]:
    # step2 가 측정 실패 시 raise 하므로 step3 도달 시점엔 모든 baseline 이 채워져 있다.
    cal_result = ctx.results["calibration"]
    data = cal_result.data
    return {
        "iris_offset_left": float(data["iris_offset_left"]),
        "iris_offset_right": float(data["iris_offset_right"]),
        "tilt_baseline": float(data["tilt_baseline"]),
        "center_baseline": float(data["center_baseline"]),
        "frame_ratio": float(data["frame_ratio"]),
    }


# ============================================================
# 시선 — 프레임 수집 / 분류 / 집계 / 점수 / 타임라인
# ============================================================
def _collect_gaze_samples(ctx: PipelineContext, cal: dict[str, float]) -> list[GazeSample]:
    cap = cv2.VideoCapture(str(ctx.file_path))
    if not cap.isOpened():
        logger.error(f"[Step3] 영상 열기 실패: {ctx.file_path}")
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    stride = max(1, int(round(fps / GAZE_FPS)))
    start_frame = int(ANALYSIS_START_SEC * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5,
    )
    samples: list[GazeSample] = []
    try:
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % stride == 0:
                ts = (start_frame + idx) / fps
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = mesh.process(rgb)
                samples.append(_classify_gaze(ts, res, cal))
            idx += 1
    finally:
        mesh.close()
        cap.release()
    return samples


def _classify_gaze(timestamp_sec: float, res: Any, cal: dict[str, float]) -> GazeSample:
    if not res.multi_face_landmarks:
        return GazeSample(timestamp_sec, GazeState.UNKNOWN, None, None, 0.0, 0.0)
    lm = res.multi_face_landmarks[0].landmark
    left = _iris_offset(lm, iris_idx=468, outer_idx=33, inner_idx=133)
    right = _iris_offset(lm, iris_idx=473, outer_idx=263, inner_idx=362)
    if left is None or right is None:
        return GazeSample(timestamp_sec, GazeState.UNKNOWN, left, right, 0.0, 0.0)

    dev_left = left - cal["iris_offset_left"]
    dev_right = right - cal["iris_offset_right"]
    max_dev = max(abs(dev_left), abs(dev_right))

    # 우선순위: 이탈 → 대본 → 슬라이드 → 정면
    if max_dev > ESCAPE_THRESHOLD:
        state = GazeState.ESCAPE
    elif max_dev <= FRONT_TOLERANCE:
        state = GazeState.FRONT
    else:
        # 대본 분류는 vertical 시선 도입 후 활성화 — 현재 비-정면은 슬라이드로 통합
        state = GazeState.SLIDE
    return GazeSample(timestamp_sec, state, left, right, dev_left, dev_right)


def _iris_offset(landmarks: Any, *, iris_idx: int, outer_idx: int, inner_idx: int) -> float | None:
    """홍채 중심이 눈 가로축 어디에 있는지를 0~1로 정규화. 0.5=정중앙. step2와 동일 정의."""
    iris = landmarks[iris_idx]
    outer = landmarks[outer_idx]
    inner = landmarks[inner_idx]
    span = inner.x - outer.x
    if abs(span) < 1e-6:
        return None
    return float((iris.x - outer.x) / span)


def _summarize_gaze(samples: list[GazeSample]) -> tuple[float, dict[str, int]]:
    breakdown: dict[str, int] = {s.value: 0 for s in GazeState}
    for s in samples:
        breakdown[s.state.value] += 1
    if not samples:
        return 0.0, breakdown
    return breakdown[GazeState.FRONT.value] / len(samples), breakdown


def _gaze_grade(ratio: float) -> str:
    if ratio >= WARN_RATIO:
        return "good"
    if ratio >= DANGER_RATIO:
        return "warn"
    return "danger"


def _build_gaze_timeline(samples: list[GazeSample]) -> list[TimelineEntry]:
    if not samples:
        return []
    events: list[TimelineEntry] = []
    end = samples[-1].timestamp_sec
    win_start = samples[0].timestamp_sec

    while win_start < end:
        win_end = win_start + WINDOW_DURATION_SEC
        in_win = [s for s in samples if win_start <= s.timestamp_sec < win_end]
        if in_win:
            front = sum(1 for s in in_win if s.state == GazeState.FRONT)
            ratio = front / len(in_win)
            if ratio < WARN_RATIO:
                severity = 2 if ratio < DANGER_RATIO else 1
                label = "danger" if severity == 2 else "warn"
                events.append(TimelineEntry(
                    event_type="gaze_miss",
                    timestamp_sec=win_start,
                    end_timestamp_sec=min(win_end, end),
                    severity=severity,
                    description=f"구간 정면 응시 {ratio:.0%} ({label})",
                    extra_data={
                        "front_ratio": ratio,
                        "samples": len(in_win),
                        "window_start_sec": win_start,
                        "window_end_sec": win_end,
                    },
                ))
        win_start = win_end
    return events


# ============================================================
# 자세 — 프레임 수집 / 분류 / 집계 / 점수
# ============================================================
def _correction_coef(frame_ratio: float) -> float:
    """보정 계수 = 0.3 / max(frame_ratio, 0.1).

    캘리브레이션 시점 인물 크기를 기준 frame_ratio (0.3) 로 정규화.
    인물이 멀면(frame_ratio 작음) 편차를 더 크게 보고, 가까우면 더 작게 본다.
    frame_ratio 가 비정상적으로 작을 때 보정 계수가 발산하는 것을 막기 위해 하한 0.1 적용.
    """
    return FRAME_RATIO_REFERENCE / max(frame_ratio, MIN_FRAME_RATIO)


def _collect_pose_samples(
    ctx: PipelineContext, cal: dict[str, float], coef: float,
) -> list[PoseSample]:
    cap = cv2.VideoCapture(str(ctx.file_path))
    if not cap.isOpened():
        logger.error(f"[Step3] 영상 열기 실패: {ctx.file_path}")
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    stride = max(1, int(round(fps / POSTURE_FPS)))
    start_frame = int(ANALYSIS_START_SEC * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    pose = mp.solutions.pose.Pose(model_complexity=0, enable_segmentation=False)
    samples: list[PoseSample] = []
    try:
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % stride == 0:
                ts = (start_frame + idx) / fps
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = pose.process(rgb)
                samples.append(_classify_pose(ts, res, cal, coef))
            idx += 1
    finally:
        pose.close()
        cap.release()
    return samples


def _classify_pose(
    timestamp_sec: float, res: Any, cal: dict[str, float], coef: float,
) -> PoseSample:
    if not res.pose_landmarks:
        return PoseSample(timestamp_sec, PoseState.UNKNOWN, None, None, 0.0, 0.0)
    lm = res.pose_landmarks.landmark
    ls = lm[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
    rs = lm[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
    if ls.visibility < SHOULDER_VISIBILITY_MIN or rs.visibility < SHOULDER_VISIBILITY_MIN:
        return PoseSample(timestamp_sec, PoseState.UNKNOWN, None, None, 0.0, 0.0)

    tilt = float(rs.y - ls.y)                # 양 어깨 y 차 — step2 와 동일 정의
    center = float((ls.x + rs.x) / 2.0)      # 양 어깨 가로 중앙

    tilt_dev = abs(tilt - cal["tilt_baseline"]) * coef
    center_dev = abs(center - cal["center_baseline"]) * coef
    max_dev = max(tilt_dev, center_dev)

    if max_dev <= POSTURE_STABLE_DEV:
        state = PoseState.STABLE
    elif max_dev <= POSTURE_WARN_DEV:
        state = PoseState.WARN
    else:
        state = PoseState.DANGER
    return PoseSample(timestamp_sec, state, tilt, center, tilt_dev, center_dev)


def _summarize_posture(samples: list[PoseSample]) -> tuple[float, dict[str, int]]:
    breakdown: dict[str, int] = {s.value: 0 for s in PoseState}
    for s in samples:
        breakdown[s.state.value] += 1
    if not samples:
        return 0.0, breakdown
    return breakdown[PoseState.STABLE.value] / len(samples), breakdown


def _posture_score(stable_ratio: float) -> float:
    if stable_ratio >= POSTURE_GOOD_RATIO:
        return POSTURE_SCORE_GOOD
    if stable_ratio >= POSTURE_WARN_RATIO:
        return POSTURE_SCORE_WARN
    return POSTURE_SCORE_DANGER


def _posture_grade(stable_ratio: float) -> str:
    if stable_ratio >= POSTURE_GOOD_RATIO:
        return "good"
    if stable_ratio >= POSTURE_WARN_RATIO:
        return "warn"
    return "danger"
