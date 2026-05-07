"""파이프라인 컨텍스트 — 모든 단계가 공유하는 입력/상태 컨테이너."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class StepResult:
    """각 단계의 출력. data에 단계별 raw 측정값을 자유롭게 채움.

    예시 (step3_visual): data={"gaze_ratio": 0.82, "posture_variance": 0.07, ...}
    """
    step_key: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineContext:
    """파이프라인 전 단계에 공유되는 컨텍스트.

    - update_progress: orchestrator가 단계 시작/끝 시 호출. (step_number, percent)
    - results: 이미 끝난 단계의 결과. 후속 단계가 이전 출력에 접근할 때 사용.
      (예: step5가 step4의 추출 오디오 경로를 사용)
    """
    job_uuid: str
    file_path: Path
    user_id: int
    target_duration_sec: float | None = None
    # 사용자가 업로드 시 입력한 발표 원고. 있으면 step6 발음 정확성에서 jiwer WER 직접 산출,
    # 없으면 Whisper word probability 기반 추정으로 폴백.
    script: str | None = None
    update_progress: Callable[[int, int], None] = field(
        default_factory=lambda: (lambda step, percent: None)
    )
    results: dict[str, StepResult] = field(default_factory=dict)
