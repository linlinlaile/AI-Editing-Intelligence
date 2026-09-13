"""Application orchestration for in-memory Shot visual aggregation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from aei.domain.aggregation import (
    AggregationInput, AggregationResult, MissingInput, MissingInputReason,
    aggregate_shot_observations, generate_shot_observation_evidence,
)
from aei.domain.models import AnalysisRun, Artifact, Evidence, Observation, Sample, TemporalSegment
from aei.ports.repository import ObservationRepository
from aei.ports.analyzer import AnalysisInput, Analyzer, AnalyzerContext


@dataclass(frozen=True)
class ShotAnalysisRequest:
    shot: TemporalSegment
    samples: tuple[Sample, ...]
    artifacts: tuple[Artifact, ...]
    vision_context: AnalyzerContext
    aggregation_run_id: str
    observation_id: str
    evidence_id: str
    taxonomy: str


@dataclass(frozen=True)
class ShotAnalysisResult:
    observation: Observation
    evidence: Evidence
    aggregation: AggregationResult
    failed_inputs: tuple[MissingInput, ...]


class ShotObservationAggregationUseCase:
    """Orchestrate per-Artifact vision analysis and pure Shot aggregation.

    This service is deliberately in-memory: callers provide snapshots and own
    persistence and AnalysisRun creation. The injected analyzer remains a
    single-Artifact analyzer.
    """

    def __init__(self, vision_analyzer: Analyzer):
        self._vision_analyzer = vision_analyzer

    def execute(self, request: ShotAnalysisRequest) -> ShotAnalysisResult:
        if request.shot.kind != "shot":
            raise ValueError("request shot must be a shot segment")
        artifacts = {artifact.id: artifact for artifact in request.artifacts}
        if len(artifacts) != len(request.artifacts):
            raise ValueError("artifact snapshot contains duplicate IDs")

        observations: list[Observation] = []
        evidences: list[Evidence] = []
        missing: list[MissingInput] = []
        seen_artifacts: set[str] = set()

        # Samples define the expected input set. An artifact can be referenced
        # by more than one sample; analyze it once and let domain aggregation
        # deduplicate canonical source points.
        for sample in request.samples:
            if sample.segment_id != request.shot.id:
                raise ValueError("sample does not belong to requested shot")
            artifact_ids = sample.artifact_ids
            if not artifact_ids:
                missing.append(MissingInput(sample.id, MissingInputReason.ARTIFACT_MISSING, (), "sample has no artifact"))
                continue
            for artifact_id in artifact_ids:
                if artifact_id in seen_artifacts:
                    continue
                seen_artifacts.add(artifact_id)
                artifact = artifacts.get(artifact_id)
                if artifact is None:
                    missing.append(MissingInput(sample.id, MissingInputReason.ARTIFACT_MISSING, (artifact_id,), "artifact snapshot missing"))
                    continue
                try:
                    result = self._vision_analyzer.analyze(
                        AnalysisInput(artifact_ids=(artifact.id,)), request.vision_context
                    )
                    observations.extend(result.observations)
                    evidences.extend(result.evidences)
                except Exception as exc:  # one failed input must not abort the Shot
                    missing.append(MissingInput(sample.id, MissingInputReason.FAILED, (artifact.id,), str(exc)))

        aggregation = aggregate_shot_observations(
            AggregationInput(
                request.shot, request.samples, tuple(observations), tuple(evidences), tuple(missing)
            ),
            taxonomy=request.taxonomy,
            producer_ref=request.vision_context.producer_ref,
        )
        observation, evidence = generate_shot_observation_evidence(
            aggregation,
            aggregation_run_id=request.aggregation_run_id,
            observation_id=request.observation_id,
            evidence_id=request.evidence_id,
        )
        return ShotAnalysisResult(observation, evidence, aggregation, tuple(missing))

    def execute_and_persist(self, request: ShotAnalysisRequest,
                            aggregation_run: AnalysisRun,
                            repository: ObservationRepository) -> ShotAnalysisResult:
        """Run orchestration and persist only the new aggregation records."""
        if aggregation_run.id != request.aggregation_run_id:
            raise ValueError("aggregation run ID does not match request")
        result = self.execute(request)
        repository.save_analysis_run(aggregation_run)
        repository.save_evidence(result.evidence)
        repository.save_observation(result.observation)
        return result






