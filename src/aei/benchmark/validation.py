"""Validation for benchmark contracts."""
from __future__ import annotations

from aei.domain.benchmark import BenchmarkReport, EvaluationBasisIdentity, MetricResult


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


class BenchmarkReportValidator:
    """Validate consistency across a benchmark report's public fields."""

    _supported_contract_versions = frozenset({"v1"})

    @classmethod
    def validate(cls, report: BenchmarkReport) -> None:
        if not isinstance(report, BenchmarkReport):
            raise TypeError("report must be a BenchmarkReport")
        for value, name in (
            (report.id, "id"), (report.evaluation_run_id, "evaluation_run_id"),
            (report.dataset_id, "dataset_id"), (report.dataset_version, "dataset_version"),
            (report.annotation_version, "annotation_version"), (report.evaluator_ref, "evaluator_ref"),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} is required")
        if report.report_contract_version not in cls._supported_contract_versions:
            raise ValueError(f"unsupported report contract version: {report.report_contract_version}")
        if not report.metric_results:
            raise ValueError("benchmark report requires at least one metric result")

        for metric in report.metric_results:
            MetricResultValidator.validate(metric)
        metric_names = {metric.metric_name for metric in report.metric_results}
        metric_versions = {metric.metric_version for metric in report.metric_results}
        if any(not name or not version for name, version in ((m.metric_name, m.metric_version) for m in report.metric_results)):
            raise ValueError("metric identity is required")
        provenance = report.metadata.get("provenance", {})
        if provenance and not isinstance(provenance, dict):
            raise ValueError("report provenance must be a mapping")
        if provenance:
            if provenance.get("dataset_version") not in (None, report.dataset_version):
                raise ValueError("provenance dataset_version mismatch")
            if provenance.get("annotation_version") not in (None, report.annotation_version):
                raise ValueError("provenance annotation_version mismatch")
            if provenance.get("evaluator_ref") not in (None, report.evaluator_ref):
                raise ValueError("provenance evaluator_ref mismatch")
            listed_versions = provenance.get("metric_versions")
            if listed_versions is not None and tuple(listed_versions) != tuple(metric.metric_version for metric in report.metric_results):
                raise ValueError("provenance metric_versions mismatch")

        basis = report.evaluation_basis
        if basis is not None:
            if not isinstance(basis, EvaluationBasisIdentity):
                raise ValueError("evaluation_basis must be an EvaluationBasisIdentity")
            if basis.dataset_version != report.dataset_version or basis.annotation_version != report.annotation_version:
                raise ValueError("evaluation basis version mismatch")
            if report.dataset_identity is not None and basis.dataset_identity != report.dataset_identity:
                raise ValueError("dataset identity mismatch")
            if report.annotation_identity is not None and basis.annotation_identity != report.annotation_identity:
                raise ValueError("annotation identity mismatch")

        revision = report.revision_identity
        if revision is not None:
            if provenance:
                for field in ("producer_ref", "model_ref", "config_ref", "analysis_run_ids"):
                    value = provenance.get(field)
                    if value is not None and value != getattr(revision, field):
                        raise ValueError(f"provenance {field} mismatch")
            if not isinstance(revision.analysis_run_ids, tuple) or any(not isinstance(run_id, str) or not run_id for run_id in revision.analysis_run_ids):
                raise ValueError("revision analysis_run_ids must contain non-empty strings")

        if len(metric_names) == 1 and report.metric_config_identity is not None and not isinstance(report.metric_config_identity, str):
            raise ValueError("metric_config_identity must be a string")


__all__ = ["MetricResultValidator", "BenchmarkReportValidator"]
