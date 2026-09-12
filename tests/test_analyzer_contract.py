import pytest

from aei.adapters.fake_analyzer import FakeAnalyzer
from aei.domain.models import Evidence, Observation, ObservationStatus
from aei.ports.analyzer import AnalysisInput, AnalysisResult, AnalyzerContext


def test_fake_analyzer_returns_valid_result_without_repository():
    context = AnalyzerContext("run", "fake:v1", {"fixture": True})
    result = FakeAnalyzer().analyze(AnalysisInput(artifact_ids=("artifact-1",)), context)
    assert len(result.observations) == 1 and len(result.evidences) == 1
    observation = result.observations[0]
    assert observation.evidence_ids == (result.evidences[0].id,)
    assert observation.run_id == context.analysis_run_id
    assert observation.producer_ref == context.producer_ref


def test_result_validation_rejects_bad_provenance_or_missing_evidence():
    context = AnalyzerContext("run", "producer:v1")
    evidence = Evidence("e", "run", "artifact", artifact_hash="sha256:x")
    bad_run = Observation("o", "other", "artifact", "a", "x", "v", evidence_ids=("e",), producer_ref="producer:v1")
    with pytest.raises(ValueError, match="run_id"):
        AnalysisResult((bad_run,), (evidence,)).validate(context)
    missing = Observation("o2", "run", "artifact", "a", "x", "v", evidence_ids=("missing",), producer_ref="producer:v1")
    with pytest.raises(ValueError, match="missing evidence"):
        AnalysisResult((missing,), (evidence,)).validate(context)


def test_result_validation_rejects_missing_or_mismatched_producer():
    context = AnalyzerContext("run", "producer:v1")
    evidence = Evidence("e", "run", "artifact", artifact_hash="sha256:x")
    missing = Observation("o", "run", "artifact", "a", "x", "v", evidence_ids=("e",))
    with pytest.raises(ValueError, match="producer_ref"):
        AnalysisResult((missing,), (evidence,)).validate(context)
    mismatched = Observation("o2", "run", "artifact", "a", "x", "v", evidence_ids=("e",), producer_ref="other:v1")
    with pytest.raises(ValueError, match="producer_ref"):
        AnalysisResult((mismatched,), (evidence,)).validate(context)


def test_analysis_input_supports_multiple_reference_kinds():
    assert AnalysisInput(sample_ids=("s1", "s2"), audio_segment_ids=("a1",)).sample_ids == ("s1", "s2")
    with pytest.raises(ValueError):
        AnalysisInput()
