"""Benchmark evaluation extension point ( intentionally not implemented )."""
from __future__ import annotations

from aei.domain.evaluation import EvaluationFinding, EvaluationInput, EvaluationResult, EvaluationStatus


class BenchmarkEvaluator:
    name = "benchmark"
    version = "v1"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        observation_id = getattr(input.observation, "id", "unknown") or "unknown"
        return EvaluationResult(
            id=f"evaluation:{observation_id}:benchmark:{self.version}",
            observation_id=observation_id,
            evaluation_run_id=input.evaluation_run_id or getattr(input.observation, "run_id", "unknown") or "unknown",
            evaluator_ref=f"{self.name}:{self.version}",
            evaluation_kind="benchmark",
            status=EvaluationStatus.NOT_EVALUABLE,
            findings=(EvaluationFinding("benchmark_not_implemented", "Benchmark evaluation is an extension point in this phase"),),
        )


__all__ = ["BenchmarkEvaluator"]
