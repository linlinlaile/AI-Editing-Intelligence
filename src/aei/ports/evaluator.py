"""Infrastructure-independent contract for observation evaluators."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from aei.domain.evaluation import EvaluationInput, EvaluationResult


@runtime_checkable
class Evaluator(Protocol):
    name: str
    version: str

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        ...


__all__ = ["Evaluator"]
