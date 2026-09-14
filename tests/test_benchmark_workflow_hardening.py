import pytest

from aei.application.benchmark import BenchmarkEvaluationUseCase, BenchmarkRunner
from aei.domain.benchmark import BenchmarkAnnotation, BenchmarkCase, BenchmarkDataset, BenchmarkInputSnapshot, MetricResult


def _snapshot(**metadata):
    dataset = BenchmarkDataset("ds", "fixture", "d1", "a1", "task", ("c1",))
    case = BenchmarkCase("c1", "target", "feature", BenchmarkAnnotation("c1", "target", "feature", "expected", "a1"))
    return BenchmarkInputSnapshot(dataset, (case,), "eval:v1", producer_ref="p", metadata=metadata)


class ValidMetric:
    name = "metric"
    version = "v1"

    def calculate(self, snapshot):
        return MetricResult(self.name, self.version, "COMPUTED", 1, 0, values={"accuracy": 1.0})


class InvalidMetric:
    name = "metric"
    version = "v1"

    def calculate(self, snapshot):
        return MetricResult(self.name, self.version, "COMPUTED", 1, 0, values={"accuracy": 2.0})


def test_valid_benchmark_run_returns_validated_report():
    report = BenchmarkEvaluationUseCase(BenchmarkRunner((ValidMetric(),))).execute(_snapshot(), "eval-1")
    assert report.metric_results[0].values["accuracy"] == 1.0


def test_invalid_metric_result_stops_report_generation():
    with pytest.raises(ValueError, match="between 0 and 1"):
        BenchmarkRunner((InvalidMetric(),)).run(_snapshot(), "eval-1")


def test_invalid_report_is_rejected_after_assembly():
    snapshot = _snapshot(evaluation_basis=object())
    with pytest.raises(ValueError, match="evaluation_basis"):
        BenchmarkRunner((ValidMetric(),)).run(snapshot, "eval-1")
