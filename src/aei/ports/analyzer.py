"""Infrastructure-independent contract for semantic analyzers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from aei.domain.models import Evidence, Observation


@dataclass(frozen=True)
class AnalysisInput:
    """References to inputs; payloads and infrastructure handles stay outside the contract."""

    artifact_ids: tuple[str, ...] = ()
    sample_ids: tuple[str, ...] = ()
    audio_segment_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not (self.artifact_ids or self.sample_ids or self.audio_segment_ids):
            raise ValueError("analysis input must contain at least one reference")


@dataclass(frozen=True)
class AnalyzerContext:
    analysis_run_id: str
    producer_ref: str
    configuration: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.analysis_run_id:
            raise ValueError("analysis_run_id is required")
        if not self.producer_ref:
            raise ValueError("producer_ref is required")


@dataclass(frozen=True)
class AnalysisResult:
    observations: tuple[Observation, ...] = ()
    evidences: tuple[Evidence, ...] = ()

    def validate(self, context: AnalyzerContext) -> None:
        evidence_by_id = {e.id: e for e in self.evidences}
        if len(evidence_by_id) != len(self.evidences):
            raise ValueError("analysis result contains duplicate evidence IDs")
        for evidence in self.evidences:
            if evidence.run_id != context.analysis_run_id:
                raise ValueError("evidence run_id does not match analyzer context")
        for observation in self.observations:
            if observation.run_id != context.analysis_run_id:
                raise ValueError("observation run_id does not match analyzer context")
            if not observation.producer_ref:
                raise ValueError("observation producer_ref is required")
            if not observation.evidence_ids:
                raise ValueError("observation must reference evidence")
            missing = set(observation.evidence_ids) - evidence_by_id.keys()
            if missing:
                raise ValueError(f"observation references missing evidence: {sorted(missing)}")
            if observation.producer_ref != context.producer_ref:
                raise ValueError("observation producer_ref does not match analyzer context")


class Analyzer(Protocol):
    name: str
    version: str

    def analyze(self, input: AnalysisInput, context: AnalyzerContext) -> AnalysisResult:
        ...
