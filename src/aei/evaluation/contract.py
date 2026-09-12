"""Contract-only evaluation of Observation objects."""
from __future__ import annotations

import json
import math
from typing import Any

from aei.domain.evaluation import EvaluationFinding, EvaluationInput, EvaluationResult, EvaluationStatus
from aei.domain.models import ObservationStatus


_FORBIDDEN_KEYS = {"prompt", "response", "raw_response", "artifact_payload", "embedding_vector"}


def _valid_value(value: Any) -> bool:
    if isinstance(value, float) and not math.isfinite(value):
        return False
    if isinstance(value, dict):
        if any(not isinstance(k, str) or k.lower() in _FORBIDDEN_KEYS for k in value):
            return False
        return all(_valid_value(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(_valid_value(v) for v in value)
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError, OverflowError):
        return False
    return True


class ContractEvaluator:
    name = "contract"
    version = "v1"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        findings: list[EvaluationFinding] = []
        observation = input.observation
        required = ("id", "run_id", "target_type", "target_id", "feature", "value", "value_status", "producer_ref")
        for field in required:
            if not hasattr(observation, field) or getattr(observation, field) in (None, ""):
                findings.append(EvaluationFinding(f"missing_{field}", f"Observation field '{field}' is required"))

        status = getattr(observation, "value_status", None)
        if not isinstance(status, ObservationStatus):
            findings.append(EvaluationFinding("invalid_status", "Observation value_status is not a valid ObservationStatus"))

        if hasattr(observation, "value") and not _valid_value(observation.value):
            findings.append(EvaluationFinding("invalid_value", "Observation value must be JSON-serializable and finite"))

        return EvaluationResult(
            id=f"evaluation:{getattr(observation, 'id', 'unknown')}:{self.version}",
            observation_id=getattr(observation, "id", "unknown") or "unknown",
            evaluation_run_id=input.evaluation_run_id or getattr(observation, "run_id", "unknown") or "unknown",
            evaluator_ref=f"{self.name}:{self.version}",
            evaluation_kind="contract",
            status=EvaluationStatus.FAIL if findings else EvaluationStatus.PASS,
            findings=tuple(findings),
        )


__all__ = ["ContractEvaluator"]
