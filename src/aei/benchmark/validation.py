"""Validation for benchmark contracts."""
from __future__ import annotations

from aei.domain.benchmark import MetricResult


class MetricResultValidator:
    """Validate consistency of a metric result without recalculating it."""

    _known_statuses = frozenset({"COMPUTED", "NOT_EVALUABLE", "NOT_COMPUTED"})

    @classmethod
    def validate(cls, result: MetricResult) -> None:
        if not isinstance(result, MetricResult):
            raise TypeError("result must be a MetricResult")
        if result.status not in cls._known_statuses:
            raise ValueError(f"unsupported metric result status: {result.status}")

        outcomes = result.case_outcomes
        evaluated = sum(o.status in ("CORRECT", "INCORRECT") for o in outcomes)
        unevaluable = sum(o.status == "UNEVALUABLE" for o in outcomes)
        if outcomes and evaluated != result.evaluated_case_count:
            raise ValueError("evaluated_case_count does not match case outcomes")
        if outcomes and unevaluable != result.unevaluable_case_count:
            raise ValueError("unevaluable_case_count does not match case outcomes")

        if result.status == "NOT_EVALUABLE" and result.evaluated_case_count:
            raise ValueError("NOT_EVALUABLE result cannot contain evaluated cases")
        if result.status == "COMPUTED" and result.evaluated_case_count == 0:
            raise ValueError("COMPUTED result requires evaluated cases")
        if "accuracy" in result.values:
            accuracy = result.values["accuracy"]
            if not isinstance(accuracy, (int, float)) or isinstance(accuracy, bool) or not 0 <= accuracy <= 1:
                raise ValueError("accuracy must be a number between 0 and 1")
            if result.evaluated_case_count == 0:
                raise ValueError("accuracy cannot be present without evaluated cases")


__all__ = ["MetricResultValidator"]
