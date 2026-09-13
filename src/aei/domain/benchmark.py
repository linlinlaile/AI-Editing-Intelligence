"""Pure contracts for benchmark datasets and benchmark execution snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


def _required(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class BenchmarkDataset:
    id: str
    name: str
    dataset_version: str
    annotation_version: str
    task: str
    case_ids: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, name in ((self.id, "id"), (self.name, "name"), (self.dataset_version, "dataset_version"),
                            (self.annotation_version, "annotation_version"), (self.task, "task")):
            _required(value, name)
        if not self.case_ids or any(not isinstance(case_id, str) or not case_id for case_id in self.case_ids):
            raise ValueError("case_ids must contain non-empty strings")
        if len(set(self.case_ids)) != len(self.case_ids):
            raise ValueError("dataset case_ids must be unique")


@dataclass(frozen=True)
class BenchmarkAnnotation:
    case_id: str
    target_id: str
    feature: str
    expected: Any
    annotation_version: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, name in ((self.case_id, "case_id"), (self.target_id, "target_id"), (self.feature, "feature"),
                            (self.annotation_version, "annotation_version")):
            _required(value, name)


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    target_id: str
    feature: str
    annotation: BenchmarkAnnotation | None
    observation_id: str | None = None
    observed_value: Any = None
    observed_status: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, name in ((self.id, "id"), (self.target_id, "target_id"), (self.feature, "feature")):
            _required(value, name)
        if self.annotation is not None and self.annotation.case_id != self.id:
            raise ValueError("annotation case_id must match case id")
        if self.annotation is not None and (self.annotation.target_id != self.target_id or self.annotation.feature != self.feature):
            raise ValueError("annotation target and feature must match case")


@dataclass(frozen=True)
class BenchmarkInputSnapshot:
    dataset: BenchmarkDataset
    cases: tuple[BenchmarkCase, ...]
    evaluator_ref: str
    producer_ref: str | None = None
    model_ref: str | None = None
    config_ref: str | None = None
    analysis_run_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _required(self.evaluator_ref, "evaluator_ref")
        if not self.cases:
            raise ValueError("benchmark snapshot requires at least one case")
        case_ids = tuple(case.id for case in self.cases)
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("benchmark snapshot case IDs must be unique")
        expected = set(self.dataset.case_ids)
        if set(case_ids) != expected:
            raise ValueError("snapshot cases must match dataset membership")
        for case in self.cases:
            if case.annotation is not None and case.annotation.annotation_version != self.dataset.annotation_version:
                raise ValueError("case annotation version must match dataset annotation_version")
        if any(not isinstance(run_id, str) or not run_id for run_id in self.analysis_run_ids):
            raise ValueError("analysis_run_ids must contain non-empty strings")


@dataclass(frozen=True)
class MetricResult:
    metric_name: str
    metric_version: str
    status: str
    evaluated_case_count: int
    unevaluable_case_count: int
    values: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    case_outcomes: tuple["CaseOutcome", ...] = ()

    def __post_init__(self) -> None:
        for value, name in ((self.metric_name, "metric_name"), (self.metric_version, "metric_version"), (self.status, "status")):
            _required(value, name)
        if self.evaluated_case_count < 0 or self.unevaluable_case_count < 0:
            raise ValueError("metric case counts must be non-negative")
        ids = [outcome.case_id for outcome in self.case_outcomes]
        if len(ids) != len(set(ids)):
            raise ValueError("metric case outcome IDs must be unique")


@dataclass(frozen=True)
class BenchmarkReport:
    id: str
    evaluation_run_id: str
    dataset_id: str
    dataset_version: str
    annotation_version: str
    evaluator_ref: str
    metric_results: tuple[MetricResult, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)
    report_contract_version: str = "v1"
    revision_identity: "RevisionIdentity | None" = None
    dataset_identity: str | None = None
    annotation_identity: str | None = None
    metric_config_identity: str | None = None
    evaluation_basis: "EvaluationBasisIdentity | None" = None

    def __post_init__(self) -> None:
        for value, name in ((self.id, "id"), (self.evaluation_run_id, "evaluation_run_id"), (self.dataset_id, "dataset_id"),
                            (self.dataset_version, "dataset_version"), (self.annotation_version, "annotation_version"),
                            (self.evaluator_ref, "evaluator_ref")):
            _required(value, name)
        if not self.metric_results:
            raise ValueError("benchmark report requires at least one metric result")


@dataclass(frozen=True)
class CaseOutcome:
    case_id: str
    status: str
    reason: str | None = None

    VALID_STATUSES = frozenset({"CORRECT", "INCORRECT", "UNEVALUABLE", "MISSING"})

    def __post_init__(self) -> None:
        _required(self.case_id, "case_id")
        if self.status not in self.VALID_STATUSES:
            raise ValueError("invalid case outcome status")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason):
            raise ValueError("case outcome reason must be a non-empty string")


@dataclass(frozen=True)
class RevisionIdentity:
    producer_ref: str | None = None
    model_ref: str | None = None
    config_ref: str | None = None
    code_revision: str | None = None
    analysis_run_ids: tuple[str, ...] = ()
    fingerprint: str | None = None

    @property
    def completeness(self) -> str:
        if all(value is None for value in (self.producer_ref, self.model_ref, self.config_ref, self.code_revision, self.fingerprint)) and not self.analysis_run_ids:
            return "MISSING"
        required = (self.producer_ref, self.model_ref, self.config_ref, self.code_revision)
        return "COMPLETE" if all(isinstance(value, str) and value for value in required) else "INCOMPLETE"


@dataclass(frozen=True)
class EvaluationBasisIdentity:
    dataset_identity: str
    dataset_version: str
    annotation_identity: str
    annotation_version: str
    case_membership_identity: str
    task: str
    feature: str
    taxonomy: str

    def __post_init__(self) -> None:
        for value, name in ((self.dataset_identity, "dataset_identity"), (self.dataset_version, "dataset_version"), (self.annotation_identity, "annotation_identity"), (self.annotation_version, "annotation_version"), (self.case_membership_identity, "case_membership_identity"), (self.task, "task"), (self.feature, "feature"), (self.taxonomy, "taxonomy")):
            _required(value, name)


@dataclass(frozen=True)
class BenchmarkComparisonReport:
    baseline_report_id: str
    candidate_report_id: str
    comparability_status: str
    comparability_reasons: tuple[str, ...] = ()
    transition_counts: Mapping[str, int] = field(default_factory=dict)
    evaluability_shift: Mapping[str, int] = field(default_factory=dict)
    metric_delta: Mapping[str, Any] | None = None
    comparison_contract_version: str = "v1"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    baseline_basis: "EvaluationBasisIdentity | None" = None
    candidate_basis: "EvaluationBasisIdentity | None" = None
    baseline_revision: RevisionIdentity | None = None
    candidate_revision: RevisionIdentity | None = None
    baseline_metric_name: str | None = None
    baseline_metric_version: str | None = None
    baseline_metric_config_identity: str | None = None
    candidate_metric_name: str | None = None
    candidate_metric_version: str | None = None
    candidate_metric_config_identity: str | None = None

    def __post_init__(self) -> None:
        _required(self.baseline_report_id, "baseline_report_id")
        _required(self.candidate_report_id, "candidate_report_id")
        _required(self.comparability_status, "comparability_status")


__all__ = ["BenchmarkCase", "BenchmarkAnnotation", "BenchmarkDataset", "BenchmarkInputSnapshot", "MetricResult", "BenchmarkReport", "CaseOutcome", "RevisionIdentity", "EvaluationBasisIdentity", "BenchmarkComparisonReport"]
