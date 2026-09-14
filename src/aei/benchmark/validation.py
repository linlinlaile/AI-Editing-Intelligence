"""Validation for benchmark contracts."""
from __future__ import annotations

from aei.domain.benchmark import BenchmarkReport, EvaluationBasisIdentity, MetricResult, RevisionIdentity


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


class RevisionIdentityValidator:
    """Validate the existing revision identity contract."""

    @classmethod
    def validate(cls, identity: RevisionIdentity) -> str:
        if not isinstance(identity, RevisionIdentity):
            raise TypeError("identity must be a RevisionIdentity")
        for value, name in ((identity.producer_ref, "producer_ref"), (identity.model_ref, "model_ref"),
                            (identity.config_ref, "config_ref"), (identity.code_revision, "code_revision"),
                            (identity.fingerprint, "fingerprint")):
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"{name} must be a non-empty string when provided")
        if not isinstance(identity.analysis_run_ids, tuple) or any(not isinstance(run_id, str) or not run_id for run_id in identity.analysis_run_ids):
            raise ValueError("analysis_run_ids must contain non-empty strings")
        return identity.completeness


class EvaluationBasisIdentityValidator:
    """Validate the existing evaluation basis identity contract."""

    @classmethod
    def validate(cls, identity: EvaluationBasisIdentity) -> None:
        if not isinstance(identity, EvaluationBasisIdentity):
            raise TypeError("identity must be an EvaluationBasisIdentity")
        for value, name in ((identity.dataset_identity, "dataset_identity"), (identity.dataset_version, "dataset_version"),
                            (identity.annotation_identity, "annotation_identity"), (identity.annotation_version, "annotation_version"),
                            (identity.case_membership_identity, "case_membership_identity"), (identity.task, "task"),
                            (identity.feature, "feature"), (identity.taxonomy, "taxonomy")):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} is required")


__all__ = ["MetricResultValidator", "BenchmarkReportValidator", "RevisionIdentityValidator", "EvaluationBasisIdentityValidator"]


def validate_comparison_identities(baseline: BenchmarkReport, candidate: BenchmarkReport, baseline_metric, candidate_metric) -> tuple[str, ...]:
    """Return stable comparability reasons for two benchmark report identities."""
    reasons: list[str] = []
    if baseline.evaluation_basis is None or candidate.evaluation_basis is None:
        reasons.append("missing_evaluation_basis")
    else:
        try:
            EvaluationBasisIdentityValidator.validate(baseline.evaluation_basis)
            EvaluationBasisIdentityValidator.validate(candidate.evaluation_basis)
        except (TypeError, ValueError):
            reasons.append("invalid_evaluation_basis")
        if baseline.evaluation_basis != candidate.evaluation_basis:
            reasons.append("evaluation_basis_mismatch")
    if (baseline.dataset_id, baseline.dataset_version, baseline.annotation_version) != (candidate.dataset_id, candidate.dataset_version, candidate.annotation_version):
        reasons.append("report_dataset_or_annotation_mismatch")
    if baseline.dataset_identity != candidate.dataset_identity:
        reasons.append("dataset_identity_mismatch")
    if baseline.annotation_identity != candidate.annotation_identity:
        reasons.append("annotation_identity_mismatch")
    if baseline.metric_config_identity != candidate.metric_config_identity:
        reasons.append("metric_config_identity_mismatch")
    if baseline_metric is None or candidate_metric is None:
        reasons.append("requires_single_metric")
    else:
        if (baseline_metric.metric_name, baseline_metric.metric_version) != (candidate_metric.metric_name, candidate_metric.metric_version):
            reasons.append("metric_mismatch")
        for key, reason in (("calculation_config", "metric_calculation_config_mismatch"), ("inclusion_rules", "metric_inclusion_rules_mismatch"), ("reporting_rules", "metric_reporting_rules_mismatch")):
            if baseline_metric.metadata.get(key) != candidate_metric.metadata.get(key):
                reasons.append(reason)
    for side, revision in (("baseline", baseline.revision_identity), ("candidate", candidate.revision_identity)):
        if revision is None:
            reasons.append(f"missing_{side}_revision_identity")
            continue
        try:
            status = RevisionIdentityValidator.validate(revision)
        except (TypeError, ValueError):
            reasons.append(f"invalid_{side}_revision_identity")
            continue
        if status == "MISSING":
            reasons.append(f"missing_{side}_revision_identity")
        elif status != "COMPLETE":
            reasons.append(f"incomplete_{side}_revision_identity")
    if baseline.revision_identity and candidate.revision_identity and baseline.revision_identity.fingerprint and candidate.revision_identity.fingerprint and baseline.revision_identity.fingerprint != candidate.revision_identity.fingerprint:
        reasons.append("revision_fingerprint_mismatch")
    return tuple(dict.fromkeys(reasons))


__all__ += ["validate_comparison_identities"]
