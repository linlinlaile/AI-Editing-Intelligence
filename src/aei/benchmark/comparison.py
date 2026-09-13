"""Pure comparison of immutable benchmark reports."""
from __future__ import annotations

from datetime import datetime, timezone

from aei.domain.benchmark import BenchmarkComparisonReport, BenchmarkReport, CaseOutcome


def _metric(report: BenchmarkReport):
    return report.metric_results[0] if len(report.metric_results) == 1 else None


def compare_benchmark_reports(baseline: BenchmarkReport, candidate: BenchmarkReport) -> BenchmarkComparisonReport:
    reasons: list[str] = []
    bm, cm = _metric(baseline), _metric(candidate)
    if baseline.evaluation_basis is None or candidate.evaluation_basis is None:
        reasons.append("missing_evaluation_basis")
    elif baseline.evaluation_basis != candidate.evaluation_basis:
        reasons.append("evaluation_basis_mismatch")
    if (baseline.dataset_id, baseline.dataset_version, baseline.annotation_version) != (candidate.dataset_id, candidate.dataset_version, candidate.annotation_version):
        reasons.append("report_dataset_or_annotation_mismatch")
    if bm is None or cm is None:
        reasons.append("requires_single_metric")
    elif (bm.metric_name, bm.metric_version) != (cm.metric_name, cm.metric_version):
        reasons.append("metric_mismatch")
    for side, revision in (("baseline", baseline.revision_identity), ("candidate", candidate.revision_identity)):
        if revision is None or revision.completeness == "MISSING":
            reasons.append(f"missing_{side}_revision_identity")
        elif revision.completeness != "COMPLETE":
            reasons.append(f"incomplete_{side}_revision_identity")

    bo = {o.case_id: o for o in (bm.case_outcomes if bm else ())}
    co = {o.case_id: o for o in (cm.case_outcomes if cm else ())}
    transitions: dict[str, int] = {}
    for case_id in sorted(set(bo) | set(co)):
        left = bo.get(case_id, CaseOutcome(case_id, "MISSING"))
        right = co.get(case_id, CaseOutcome(case_id, "MISSING"))
        key = f"{left.status}->{right.status}"
        transitions[key] = transitions.get(key, 0) + 1

    base_eval = {k for k, v in bo.items() if v.status in ("CORRECT", "INCORRECT")}
    cand_eval = {k for k, v in co.items() if v.status in ("CORRECT", "INCORRECT")}
    shift = {
        "baseline_evaluable_case_count": len(base_eval),
        "candidate_evaluable_case_count": len(cand_eval),
        "newly_evaluable_case_count": len(cand_eval - base_eval),
        "no_longer_evaluable_case_count": len(base_eval - cand_eval),
        "baseline_unevaluable_case_count": sum(v.status == "UNEVALUABLE" for v in bo.values()),
        "candidate_unevaluable_case_count": sum(v.status == "UNEVALUABLE" for v in co.values()),
        "baseline_missing_case_count": sum(v.status == "MISSING" for v in bo.values()),
        "candidate_missing_case_count": sum(v.status == "MISSING" for v in co.values()),
    }
    comparable = not reasons
    delta = None
    if comparable and base_eval == cand_eval and bm and cm and "accuracy" in bm.values and "accuracy" in cm.values:
        delta = {"status": "COMPUTED", "value": cm.values["accuracy"] - bm.values["accuracy"]}
    elif comparable:
        delta = {"status": "NOT_STRICTLY_COMPARABLE"}
    comparison_metadata = {"generated_at": datetime.now(timezone.utc).isoformat(), "comparison_producer": "aei.benchmark.comparison:v1", "transition_interpretation": "REGRESSION_OR_IMPROVEMENT" if comparable else "DIAGNOSTIC_ONLY"}
    return BenchmarkComparisonReport(
        baseline.id, candidate.id, "COMPARABLE" if comparable else "NOT_COMPARABLE",
        tuple(reasons), transitions, shift, delta,
        metadata=comparison_metadata,
        baseline_basis=baseline.evaluation_basis,
        candidate_basis=candidate.evaluation_basis,
        baseline_revision=baseline.revision_identity,
        candidate_revision=candidate.revision_identity,
        baseline_metric_name=bm.metric_name if bm else None,
        baseline_metric_version=bm.metric_version if bm else None,
        baseline_metric_config_identity=baseline.metric_config_identity,
        candidate_metric_name=cm.metric_name if cm else None,
        candidate_metric_version=cm.metric_version if cm else None,
        candidate_metric_config_identity=candidate.metric_config_identity,
    )


__all__ = ["compare_benchmark_reports"]
