from dataclasses import replace

from aei.application.benchmark import BenchmarkRunner
from aei.benchmark.comparison import compare_benchmark_reports
from aei.domain.benchmark import (
    BenchmarkAnnotation, BenchmarkCase, BenchmarkDataset, BenchmarkInputSnapshot,
    EvaluationBasisIdentity, MetricResult, RevisionIdentity,
)


class AccuracyMetric:
    name = "vision.classification.accuracy"
    version = "v1"

    def __init__(self, accuracy=1.0):
        self.accuracy = accuracy

    def calculate(self, snapshot):
        return MetricResult(self.name, self.version, "COMPUTED", 1, 0,
                            values={"accuracy": self.accuracy},
                            metadata={"calculation_config": "exact", "inclusion_rules": "success", "reporting_rules": "round:none"})


def _snapshot(*, identity="input:f", basis=None):
    dataset = BenchmarkDataset("ds", "fixture", "d1", "a1", "task", ("c1",))
    case = BenchmarkCase("c1", "target", "feature", BenchmarkAnnotation("c1", "target", "feature", "expected", "a1"))
    metadata = {"dataset_identity": "ds:f", "annotation_identity": "ann:f", "metric_config_identity": "metric:f",
                "code_revision": "code", "revision_fingerprint": identity,
                "evaluation_basis": basis or EvaluationBasisIdentity("ds:f", "d1", "ann:f", "a1", "cases:f", "task", "feature", "tax")}
    return BenchmarkInputSnapshot(dataset, (case,), "eval:v1", producer_ref="p", model_ref="m", config_ref="c", analysis_run_ids=("run",), metadata=metadata)


def _reports():
    runner = BenchmarkRunner((AccuracyMetric(0.0),))
    baseline = runner.run(_snapshot(), "baseline")
    candidate = BenchmarkRunner((AccuracyMetric(1.0),)).run(_snapshot(), "candidate")
    # Supply the case outcomes produced by the metric implementation for transition analysis.
    bmetric = replace(baseline.metric_results[0], case_outcomes=())
    cmetric = replace(candidate.metric_results[0], case_outcomes=())
    return replace(baseline, metric_results=(bmetric,)), replace(candidate, metric_results=(cmetric,))


def test_strict_comparable_workflow_produces_delta():
    baseline, candidate = _reports()
    result = compare_benchmark_reports(baseline, candidate)
    assert result.comparability_status == "COMPARABLE"
    assert result.metric_delta == {"status": "COMPUTED", "value": 1.0}


def test_invalid_report_is_rejected_by_comparison():
    baseline, candidate = _reports()
    invalid = replace(candidate, metadata={"provenance": {"dataset_version": "wrong"}})
    result = compare_benchmark_reports(baseline, invalid)
    assert result.comparability_status == "NOT_COMPARABLE"
    assert "invalid_candidate_report" in result.comparability_reasons
    assert result.metadata["transition_interpretation"] == "DIAGNOSTIC_ONLY"


def test_identity_mismatches_are_diagnostic_only():
    baseline, candidate = _reports()
    cases = [
        (replace(candidate, revision_identity=RevisionIdentity("p", "m", "c", "code", ("run",), "other")), "revision_fingerprint_mismatch"),
        (replace(candidate, dataset_identity="other"), "dataset_identity_mismatch"),
        (replace(candidate, annotation_identity="other"), "annotation_identity_mismatch"),
        (replace(candidate, metric_config_identity="other"), "metric_config_identity_mismatch"),
        (replace(candidate, evaluation_basis=replace(candidate.evaluation_basis, task="other")), "evaluation_basis_mismatch"),
        (replace(candidate, evaluation_basis=replace(candidate.evaluation_basis, taxonomy="other")), "evaluation_basis_mismatch"),
    ]
    for changed, reason in cases:
        result = compare_benchmark_reports(baseline, changed)
        assert result.comparability_status == "NOT_COMPARABLE"
        assert reason in result.comparability_reasons
        assert result.metadata["transition_interpretation"] == "DIAGNOSTIC_ONLY"


def test_old_report_without_identity_is_readable_but_not_comparable():
    baseline, candidate = _reports()
    old = replace(candidate, revision_identity=None, evaluation_basis=None)
    result = compare_benchmark_reports(baseline, old)
    assert result.comparability_status == "NOT_COMPARABLE"
    assert "missing_candidate_revision_identity" in result.comparability_reasons
    assert "missing_evaluation_basis" in result.comparability_reasons
    assert result.metadata["transition_interpretation"] == "DIAGNOSTIC_ONLY"
