"""파이프라인 orchestrator — 등록된 단계를 순서대로 실행.

분석 알고리즘은 각 step 모듈에 들어가고, 여기서는 호출 순서·진행률 갱신·에러 처리만 담당.

사용자 작업:
  1. app/services/analysis/steps/ 안에 step1_*.py ~ step7_*.py 생성
     - 각 모듈은 다음 인터페이스를 따름:
         STEP_KEY: str                                    # ScoringOutput 환산 시 ctx.results의 key
         def run(ctx: PipelineContext) -> StepResult      # data 필드에 raw 측정값 채움
  2. 아래 STEPS 리스트에 (단계번호, 모듈) 튜플로 등록
  3. scoring.calculate에서 ctx.results를 읽어 점수 환산
"""
from app.services.analysis.context import PipelineContext, StepResult
from app.services.analysis.scoring import ScoringOutput, calculate
from app.utils.logger import logger


# 사용자가 step 파일을 만든 후 import 추가하고 아래 리스트에 등록.
# 예시:
#   from app.services.analysis.steps import step1_quality, step2_calibration, step3_visual
#   STEPS = [
#       (1, step1_quality),
#       (2, step2_calibration),
#       (3, step3_visual),
#       ...
#   ]
STEPS: list[tuple[int, object]] = []


class PipelineError(Exception):
    """단계 실행 중 발생한 예외를 step 정보와 함께 감쌈."""

    def __init__(self, step_number: int, step_key: str, original: BaseException):
        self.step_number = step_number
        self.step_key = step_key
        self.original = original
        super().__init__(f"[Step {step_number}/{step_key}] {type(original).__name__}: {original}")


def run_pipeline(ctx: PipelineContext) -> ScoringOutput:
    """등록된 단계를 순서대로 실행하고 점수를 산출.

    한 단계라도 실패하면 PipelineError로 감싸 위로 전파 (Celery 태스크가 잡아 FAILED 처리).
    """
    if not STEPS:
        logger.warning("[Pipeline] STEPS가 비어있음 — pipeline.py에 단계 등록 필요")

    for step_number, module in STEPS:
        step_key = getattr(module, "STEP_KEY", getattr(module, "__name__", str(module)))
        logger.info(f"[Pipeline] step {step_number}/{step_key} 시작")
        ctx.update_progress(step_number, 0)

        try:
            result = module.run(ctx)
        except Exception as exc:
            logger.error(f"[Pipeline] step {step_number}/{step_key} 실패: {exc}")
            raise PipelineError(step_number, step_key, exc) from exc

        if not isinstance(result, StepResult):
            raise PipelineError(
                step_number, step_key,
                TypeError(f"step.run은 StepResult를 반환해야 함 (받음: {type(result).__name__})"),
            )

        ctx.results[result.step_key] = result
        ctx.update_progress(step_number, 100)
        logger.info(f"[Pipeline] step {step_number}/{step_key} 완료")

    logger.info("[Pipeline] 점수 환산 시작")
    return calculate(ctx.results)
