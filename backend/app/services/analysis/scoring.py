"""점수 환산 — 각 단계 측정값을 7개 지표 + 4개 채널 점수로 합산.

사용자가 환산식·임계값·가중치를 직접 채우는 영역.
ScoringOutput 필드는 AnalysisResult 모델 컬럼과 1:1 대응되므로 변경 시 모델도 갱신 필요.
"""
from dataclasses import dataclass, field
from typing import Any

from app.services.analysis.context import StepResult


@dataclass
class TimelineEntry:
    """타임라인 이벤트 1건. TimelineEvent 모델로 1:1 변환됨."""
    event_type: str          # EventType enum value (filler_word, gaze_miss, ...)
    timestamp_sec: float
    severity: int = 1
    end_timestamp_sec: float | None = None
    description: str | None = None
    extra_data: dict[str, Any] | None = None


@dataclass
class ScoringOutput:
    """환산 결과 — analysis_task가 AnalysisResult 모델로 그대로 매핑."""
    total_score: float = 0.0

    # 7개 지표
    gaze_score: float = 0.0
    posture_score: float = 0.0
    speech_rate_score: float = 0.0
    volume_pitch_score: float = 0.0
    filler_word_score: float = 0.0
    pronunciation_score: float = 0.0
    time_score: float = 0.0

    # 4개 채널
    visual_score: float = 0.0
    audio_score: float = 0.0
    vocab_score: float = 0.0
    delivery_score: float = 0.0

    # 부가 데이터
    raw_metrics: dict[str, Any] | None = None
    feedback_summary: str | None = None
    feedback_strengths: str | None = None
    feedback_improvements: str | None = None
    feedback_details: dict[str, str] | None = None
    calibration_data: dict[str, Any] | None = None

    # 타임라인 이벤트 — TimelineEvent 행으로 저장
    timeline: list[TimelineEntry] = field(default_factory=list)


def calculate(results: dict[str, StepResult]) -> ScoringOutput:
    """단계별 측정값을 7개 지표 점수 → 4개 채널 점수 → 총점으로 환산.

    사용자 구현 영역:
      - results["visual"].data → gaze_score, posture_score
      - results["audio_analyze"].data → speech_rate_score, volume_pitch_score
      - results["speech"].data → filler_word_score, pronunciation_score
      - results["quality"].data + target_duration → time_score
      - feedback (step7 결과) → feedback_summary 등
      - 4개 채널 점수는 7개 지표의 합산 (가중치 적용)
      - 총점 = 4개 채널 점수의 합
    """
    raise NotImplementedError("scoring.calculate 미구현")
