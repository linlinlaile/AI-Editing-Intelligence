"""Deterministic benchmark metrics for existing Observation snapshots."""
from __future__ import annotations

from typing import Any

from aei.domain.benchmark import BenchmarkInputSnapshot, MetricResult


class VisionClassificationAccuracy:
    """Exact-match accuracy for Artifact ``vision.classification`` results.

    ``class_id`` is the correctness key.  Taxonomy and required field values
    are validated, while confidence is deliberately ignored. Labels explain
    results and only make a same-class inconsistency unevaluable; a normal
    wrong class is still an incorrect case even when its label differs.
    """

    name = "vision.classification.accuracy"
    version = "v1"
    _feature = "vision.classification"
    _supported_status = "SUCCESS"

    def calculate(self, snapshot: BenchmarkInputSnapshot) -> MetricResult:
        correct = incorrect = unevaluable = 0
        reasons: dict[str, int] = {}

        for case in snapshot.cases:
            reason = self._unevaluable_reason(case)
            if reason is not None:
                unevaluable += 1
                reasons[reason] = reasons.get(reason, 0) + 1
                continue
            expected = case.annotation.expected  # type: ignore[union-attr]
            observed = case.observed_value
            if observed["class_id"] == expected["class_id"] and observed["label"] != expected["label"]:
                unevaluable += 1
                reasons["label_mismatch"] = reasons.get("label_mismatch", 0) + 1
                continue
            if observed["class_id"] == expected["class_id"]:
                correct += 1
            else:
                incorrect += 1

        evaluated = correct + incorrect
        status = "COMPUTED" if evaluated else "NOT_EVALUABLE"
        values: dict[str, Any] = {
            "correct_case_count": correct,
            "incorrect_case_count": incorrect,
        }
        if evaluated:
            values["accuracy"] = correct / evaluated
        return MetricResult(
            self.name,
            self.version,
            status,
            evaluated,
            unevaluable,
            values=values,
            metadata={
                "task": "artifact_vision_classification",
                "comparison": "class_id_exact_match",
                "taxonomy_validation": "required_match",
                "label_role": "consistency_check_and_explanation",
                "confidence_used": False,
                "unevaluable_reasons": reasons,
            },
        )

    def _unevaluable_reason(self, case: Any) -> str | None:
        annotation = case.annotation
        observed = case.observed_value
        if annotation is None:
            return "missing_annotation"
        if case.observation_id is None or observed is None:
            return "missing_observation"
        if case.feature != self._feature or annotation.feature != self._feature:
            return "unsupported_feature"
        if case.target_id != annotation.target_id:
            return "target_mismatch"
        observed_status = case.observed_status or case.metadata.get("observation_status")
        if observed_status not in (None, self._supported_status):
            return "unsupported_observation_status"
        if not isinstance(observed, dict) or not isinstance(annotation.expected, dict):
            return "invalid_value_shape"
        required = ("class_id", "label", "taxonomy")
        if any(key not in observed or key not in annotation.expected for key in required):
            return "missing_classification_field"
        if not isinstance(observed["class_id"], int) or isinstance(observed["class_id"], bool):
            return "invalid_class_id"
        if not isinstance(annotation.expected["class_id"], int) or isinstance(annotation.expected["class_id"], bool):
            return "invalid_expected_class_id"
        if not isinstance(observed["label"], str) or not observed["label"].strip():
            return "invalid_label"
        if not isinstance(annotation.expected["label"], str) or not annotation.expected["label"].strip():
            return "invalid_expected_label"
        if not isinstance(observed["taxonomy"], str) or not observed["taxonomy"].strip():
            return "invalid_taxonomy"
        if not isinstance(annotation.expected["taxonomy"], str) or not annotation.expected["taxonomy"].strip():
            return "invalid_expected_taxonomy"
        if observed["taxonomy"] != annotation.expected["taxonomy"]:
            return "taxonomy_mismatch"
        return None


__all__ = ["VisionClassificationAccuracy"]
