"""Pure comparison of immutable benchmark reports."""
from __future__ import annotations

from datetime import datetime, timezone

from aei.domain.benchmark import BenchmarkComparisonReport, BenchmarkReport, CaseOutcome
from aei.benchmark.validation import validate_comparison_identities


def _metric(report: BenchmarkReport):
    return report.metric_results[0] if len(report.metric_results) == 1 else None


def compare_benchmark_reports(baseline: BenchmarkReport, candidate: BenchmarkReport) -> BenchmarkComparisonReport:
    bm, cm = _metric(baseline), _metric(candidate)
    reasons = list(validate_comparison_identities(baseline, candidate, bm, cm))

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
