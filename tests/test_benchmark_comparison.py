from aei.benchmark.comparison import compare_benchmark_reports
from aei.domain.benchmark import BenchmarkReport, CaseOutcome, MetricResult, RevisionIdentity, EvaluationBasisIdentity


def _report(report_id, statuses, accuracy, *, identity="same"):
    metric = MetricResult("vision.classification.accuracy", "v1", "COMPUTED", sum(s.status in ("CORRECT", "INCORRECT") for s in statuses), sum(s.status == "UNEVALUABLE" for s in statuses), values={"accuracy": accuracy}, case_outcomes=tuple(statuses))
    return BenchmarkReport(report_id, "run-" + report_id, "ds", "d1", "a1", "eval:v1", (metric,), report_contract_version="v1", revision_identity=RevisionIdentity(producer_ref=identity, model_ref="m", config_ref="c", code_revision="code"), dataset_identity="ds:f", annotation_identity="ann:f", metric_config_identity="metric:f", evaluation_basis=EvaluationBasisIdentity("ds:f", "d1", "ann:f", "a1", "cases:f", "task", "vision.classification", "tax"))


def test_comparison_aligns_cases_and_computes_delta():
    baseline = _report("b", (CaseOutcome("1", "CORRECT"), CaseOutcome("2", "INCORRECT")), 0.5)
    candidate = _report("c", (CaseOutcome("1", "INCORRECT"), CaseOutcome("2", "CORRECT")), 0.5)
    result = compare_benchmark_reports(baseline, candidate)
    assert result.comparability_status == "COMPARABLE"
    assert result.transition_counts == {"CORRECT->INCORRECT": 1, "INCORRECT->CORRECT": 1}
    assert result.metric_delta == {"status": "COMPUTED", "value": 0.0}


def test_missing_case_is_reported_without_quality_transition():
    baseline = _report("b", (CaseOutcome("1", "CORRECT"),), 1.0)
    candidate = _report("c", (), 0.0)
    result = compare_benchmark_reports(baseline, candidate)
    assert result.transition_counts == {"CORRECT->MISSING": 1}
    assert result.metric_delta["status"] == "NOT_STRICTLY_COMPARABLE"


def test_incomplete_revision_and_basis_mismatch_are_not_comparable():
    baseline = _report("b", (CaseOutcome("1", "CORRECT"),), 1.0)
    candidate = _report("c", (CaseOutcome("1", "CORRECT"),), 1.0)
    candidate = BenchmarkReport(candidate.id, candidate.evaluation_run_id, candidate.dataset_id, candidate.dataset_version, candidate.annotation_version, candidate.evaluator_ref, candidate.metric_results, revision_identity=RevisionIdentity(producer_ref="p"), evaluation_basis=candidate.evaluation_basis)
    result = compare_benchmark_reports(baseline, candidate)
    assert result.comparability_status == "NOT_COMPARABLE"
    assert "incomplete_candidate_revision_identity" in result.comparability_reasons


def test_evaluability_regression_is_diagnostic_when_basis_is_comparable():
    result = compare_benchmark_reports(_report("b", (CaseOutcome("1", "CORRECT"),), 1.0), _report("c", (CaseOutcome("1", "UNEVALUABLE", "missing_observation"),), 0.0))
    assert result.transition_counts == {"CORRECT->UNEVALUABLE": 1}
    assert result.metadata["transition_interpretation"] == "REGRESSION_OR_IMPROVEMENT"


def test_dataset_and_metric_mismatch_are_not_comparable():
    baseline = _report("b", (CaseOutcome("1", "CORRECT"),), 1.0)
    candidate = _report("c", (CaseOutcome("1", "CORRECT"),), 1.0)
    candidate = BenchmarkReport(candidate.id, candidate.evaluation_run_id, "other", candidate.dataset_version, candidate.annotation_version, candidate.evaluator_ref, candidate.metric_results, revision_identity=candidate.revision_identity, evaluation_basis=candidate.evaluation_basis)
    result = compare_benchmark_reports(baseline, candidate)
    assert result.comparability_status == "NOT_COMPARABLE"
    assert result.metadata["transition_interpretation"] == "DIAGNOSTIC_ONLY"


def test_duplicate_case_outcome_is_rejected():
    import pytest
    with pytest.raises(ValueError, match="unique"):
        MetricResult("m", "v1", "COMPUTED", 1, 0, case_outcomes=(CaseOutcome("1", "CORRECT"), CaseOutcome("1", "INCORRECT")))
