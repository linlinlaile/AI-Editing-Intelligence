from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
from aei.domain.models import Evidence, Observation

class EvaluationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EVALUABLE = "NOT_EVALUABLE"

@dataclass(frozen=True)
class EvaluationFinding:
    code: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self) -> None:
        if not self.code: raise ValueError("finding code is required")
        if not self.message: raise ValueError("finding message is required")

@dataclass(frozen=True)
class EvaluationInput:
    observation: Observation
    evidences: tuple[Evidence, ...] = ()
    evaluation_run_id: str = ""
    analysis_run_metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self) -> None:
        if self.evaluation_run_id is None: raise ValueError("evaluation_run_id must be a string")
        ids = [e.id for e in self.evidences]
        if len(set(ids)) != len(ids): raise ValueError("evaluation input contains duplicate evidence IDs")

@dataclass(frozen=True)
class EvaluationResult:
    id: str
    observation_id: str
    evaluation_run_id: str
    evaluator_ref: str
    evaluation_kind: str
    status: EvaluationStatus
    scores: Mapping[str, float] = field(default_factory=dict)
    findings: tuple[EvaluationFinding, ...] = ()
    def __post_init__(self) -> None:
        for name in ("id", "observation_id", "evaluation_run_id", "evaluator_ref", "evaluation_kind"):
            if not getattr(self, name): raise ValueError(f"{name} is required")
        if not isinstance(self.status, EvaluationStatus): raise ValueError("status must be an EvaluationStatus")
        for key, value in self.scores.items():
            if not isinstance(key, str) or not key: raise ValueError("score keys must be non-empty strings")
            if not isinstance(value, (int, float)) or isinstance(value, bool): raise ValueError("scores must contain numeric values")

__all__ = ["EvaluationFinding", "EvaluationInput", "EvaluationResult", "EvaluationStatus"]
