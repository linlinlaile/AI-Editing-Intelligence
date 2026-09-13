"""Application-level benchmark execution skeleton.

This module coordinates evaluation snapshots and metric calculators. It
does not load repositories, run analyzers, or implement a quality metric.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aei.domain.benchmark import BenchmarkInputSnapshot, BenchmarkReport, MetricResult, RevisionIdentity, EvaluationBasisIdentity


class MetricCalculator(Protocol):
    name: str
    version: str

    def calculate(self, snapshot: BenchmarkInputSnapshot) -> MetricResult:
        ...


@dataclass(frozen=True)
class BenchmarkRunner:
    calculators: tuple[MetricCalculator, ...]

    def run(self, snapshot: BenchmarkInputSnapshot, evaluation_run_id: str) -> BenchmarkReport:
        if not evaluation_run_id:
            raise ValueError("evaluation_run_id is required")
        if not self.calculators:
            raise ValueError("at least one metric calculator is required")
        results = tuple(calculator.calculate(snapshot) for calculator in self.calculators)
        metric_versions = tuple(result.metric_version for result in results)
        provenance = {
            "dataset_version": snapshot.dataset.dataset_version,
            "annotation_version": snapshot.dataset.annotation_version,
            "metric_version": metric_versions[0] if len(metric_versions) == 1 else metric_versions,
            "metric_versions": metric_versions,
            "evaluator_ref": snapshot.evaluator_ref,
            "producer_ref": snapshot.producer_ref,
            "model_ref": snapshot.model_ref,
            "config_ref": snapshot.config_ref,
            "analysis_run_ids": snapshot.analysis_run_ids,
        }
        return BenchmarkReport(
            id=f"benchmark:{snapshot.dataset.id}:{evaluation_run_id}",
            evaluation_run_id=evaluation_run_id,
            dataset_id=snapshot.dataset.id,
            dataset_version=snapshot.dataset.dataset_version,
            annotation_version=snapshot.dataset.annotation_version,
            evaluator_ref=snapshot.evaluator_ref,
            metric_results=results,
            metadata={"provenance": provenance},
            revision_identity=RevisionIdentity(
                producer_ref=snapshot.producer_ref,
                model_ref=snapshot.model_ref,
                config_ref=snapshot.config_ref,
                code_revision=snapshot.metadata.get("code_revision"),
                analysis_run_ids=snapshot.analysis_run_ids,
                fingerprint=snapshot.metadata.get("revision_fingerprint"),
            ),
            dataset_identity=snapshot.metadata.get("dataset_identity"),
            annotation_identity=snapshot.metadata.get("annotation_identity"),
            metric_config_identity=snapshot.metadata.get("metric_config_identity"),
            evaluation_basis=snapshot.metadata.get("evaluation_basis"),
        )


@dataclass(frozen=True)
class BenchmarkEvaluationUseCase:
    runner: BenchmarkRunner

    def execute(self, snapshot: BenchmarkInputSnapshot, evaluation_run_id: str) -> BenchmarkReport:
        return self.runner.run(snapshot, evaluation_run_id)


__all__ = ["BenchmarkEvaluationUseCase", "BenchmarkRunner", "MetricCalculator"]
