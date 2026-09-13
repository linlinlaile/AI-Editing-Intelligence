from dataclasses import dataclass

import pytest

from aei.application.benchmark import BenchmarkEvaluationUseCase, BenchmarkRunner
from aei.domain.benchmark import (
    BenchmarkAnnotation,
    BenchmarkCase,
    BenchmarkDataset,
    BenchmarkInputSnapshot,
    MetricResult,
)


def _snapshot():
    dataset = BenchmarkDataset("ds", "visual fixture", "d1", "a1", "observation", ("c1", "c2"))
    cases = tuple(
        BenchmarkCase(
            case_id,
            "target-" + case_id,
            "feature.x",
            BenchmarkAnnotation(case_id, "target-" + case_id, "feature.x", "expected", "a1"),
            observation_id="obs-" + case_id,
            observed_value="observed",
        )
        for case_id in ("c1", "c2")
    )
    return BenchmarkInputSnapshot(dataset, cases, "benchmark-skeleton:v1", producer_ref="p:v1")


@dataclass(frozen=True)
class SkeletonMetric:
    name: str = "skeleton"
    version: str = "v1"

    def calculate(self, snapshot):
        return MetricResult(self.name, self.version, "NOT_COMPUTED", 0, len(snapshot.cases), metadata={"skeleton": True})


def test_snapshot_preserves_dataset_annotation_and_membership_versions():
    snapshot = _snapshot()
    assert snapshot.dataset.dataset_version == "d1"
    assert snapshot.dataset.annotation_version == "a1"
    assert {case.id for case in snapshot.cases} == {"c1", "c2"}


def test_runner_returns_generic_metric_report_without_quality_metric():
    snapshot = _snapshot()
    report = BenchmarkEvaluationUseCase(BenchmarkRunner((SkeletonMetric(),))).execute(snapshot, "eval-1")
    assert report.dataset_version == "d1"
    assert report.annotation_version == "a1"
    assert report.metric_results[0].status == "NOT_COMPUTED"
    assert report.metric_results[0].metadata["skeleton"] is True


def test_runner_report_preserves_provenance_metadata():
    snapshot = _snapshot()
    snapshot = BenchmarkInputSnapshot(snapshot.dataset, snapshot.cases, "benchmark-skeleton:v1",
                                      producer_ref="producer:v1", model_ref="model:v2",
                                      config_ref="config:abc", analysis_run_ids=("run-1", "run-2"))
    report = BenchmarkRunner((SkeletonMetric(),)).run(snapshot, "eval-1")
    provenance = report.metadata["provenance"]
    assert provenance == {
        "dataset_version": "d1",
        "annotation_version": "a1",
        "metric_version": "v1",
        "metric_versions": ("v1",),
        "evaluator_ref": "benchmark-skeleton:v1",
        "producer_ref": "producer:v1",
        "model_ref": "model:v2",
        "config_ref": "config:abc",
        "analysis_run_ids": ("run-1", "run-2"),
    }


def test_snapshot_rejects_missing_dataset_case():
    snapshot = _snapshot()
    with pytest.raises(ValueError, match="match dataset membership"):
        BenchmarkInputSnapshot(snapshot.dataset, snapshot.cases[:1], snapshot.evaluator_ref)


def test_case_rejects_mismatched_annotation():
    with pytest.raises(ValueError, match="annotation case_id"):
        BenchmarkCase("c1", "t", "f", BenchmarkAnnotation("other", "t", "f", "x", "a1"))


def test_snapshot_rejects_annotation_version_mismatch():
    snapshot = _snapshot()
    case = BenchmarkCase("c1", "target-c1", "feature.x", BenchmarkAnnotation("c1", "target-c1", "feature.x", "expected", "a2"))
    with pytest.raises(ValueError, match="annotation version"):
        BenchmarkInputSnapshot(snapshot.dataset, (case, snapshot.cases[1]), snapshot.evaluator_ref)
