"""Deterministic analyzer used only to exercise the Phase 5.2 contract."""
from __future__ import annotations

from aei.domain.models import Evidence, Observation, ObservationStatus
from aei.ports.analyzer import AnalysisInput, AnalysisResult, AnalyzerContext


class FakeAnalyzer:
    name = "fake-analyzer"
    version = "1"

    def analyze(self, input: AnalysisInput, context: AnalyzerContext) -> AnalysisResult:
        reference_type, references = (
            ("artifact", input.artifact_ids)
            if input.artifact_ids
            else ("sample", input.sample_ids)
            if input.sample_ids
            else ("audio_segment", input.audio_segment_ids)
        )
        reference_id = references[0]
        evidence = Evidence(
            id=f"{context.analysis_run_id}:fake:evidence:0",
            run_id=context.analysis_run_id,
            kind="analyzer_input_reference",
            external_artifact_ref=f"{reference_type}:{reference_id}",
            metadata={"analyzer": self.name, "version": self.version},
        )
        observation = Observation(
            id=f"{context.analysis_run_id}:fake:observation:0",
            run_id=context.analysis_run_id,
            target_type=reference_type,
            target_id=reference_id,
            feature="fake.analysis_marker",
            value={"label": "fixture"},
            value_status=ObservationStatus.SUCCESS,
            confidence=1.0,
            confidence_kind="deterministic_fixture",
            coverage=1.0,
            evidence_ids=(evidence.id,),
            producer_ref=context.producer_ref,
        )
        result = AnalysisResult((observation,), (evidence,))
        result.validate(context)
        return result
