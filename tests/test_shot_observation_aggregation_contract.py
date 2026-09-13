import json
from dataclasses import asdict

import pytest

from aei.domain.aggregation import (
    FEATURE,
    AggregationEvidenceDraft,
    AggregationInput,
    AggregationMetadata,
    AggregationResult,
    ClassDistributionEntry,
    MissingInput,
    MissingInputReason,
    ObservationSource,
    SampledClassificationSummary,
    ShotObservationDraft,
)
from aei.domain.models import (
    Evidence,
    Observation,
    ObservationStatus,
    Rational,
    Sample,
    TemporalSegment,
    TimePoint,
    TimeSpan,
)


def _point(index: int) -> TimePoint:
    return TimePoint("video:0", 9000 + index * 1000, Rational(1, 1000), index)


def _shot_and_samples():
    shot = TemporalSegment("shot-1", "layer-1", "shot", TimeSpan(_point(0), _point(3)))
    samples = tuple(
        Sample(f"sample-{i}", "sample-run", "asset-1", "representative_sampling", "frame",
               TimeSpan(_point(i), _point(i)), i, segment_id=shot.id, sampling_method="uniform")
        for i in range(3)
    )
    return shot, samples


def _input():
    shot, samples = _shot_and_samples()
    evidences = tuple(
        Evidence(f"evidence-{i}", "vision-run", "artifact_classification_input",
                 external_artifact_ref=f"artifacts/{i}.png", artifact_hash=f"sha256:{i}")
        for i in range(3)
    )
    observations = tuple(
        Observation(f"observation-{i}", "vision-run", "artifact", f"artifact-{i}",
                    "vision.classification", {"label": "cat", "class_id": 1},
                    evidence_ids=(f"evidence-{i}",), producer_ref="vision:test:v1")
        for i in range(3)
    )
    return AggregationInput(shot, samples, observations, evidences)


def test_input_contract_is_pure_snapshot_and_validates_shot_links():
    value = _input()
    assert value.shot.kind == "shot"
    assert tuple(s.segment_id for s in value.samples) == ("shot-1",) * 3
    assert value.artifact_observations[0].target_type == "artifact"
    assert not any(name in __import__("aei.domain.aggregation", fromlist=["*"]).__dict__
                   for name in ("sqlite3", "repository", "model"))

    shot, samples = _shot_and_samples()
    with pytest.raises(ValueError, match="missing evidence"):
        AggregationInput(
            shot, samples,
            (Observation("o", "run", "artifact", "a", "vision.classification", {"x": 1},
                         evidence_ids=("missing",), producer_ref="p"),),
            (),
        )


def test_input_contract_preserves_explicit_missing_inputs_and_rejects_wrong_feature():
    shot, samples = _shot_and_samples()
    missing = MissingInput("sample-2", MissingInputReason.FAILED, ("artifact-2",), "decode failed")
    base = _input()
    value = AggregationInput(shot, samples, base.artifact_observations, base.evidences, (missing,))
    assert value.missing_inputs[0].reason is MissingInputReason.FAILED

    wrong = Observation("o", "vision-run", "artifact", "a", "content.subject", {"label": "cat"},
                        evidence_ids=("evidence-0",), producer_ref="vision:test:v1")
    with pytest.raises(ValueError, match="Artifact classifications"):
        AggregationInput(shot, samples, (wrong,), base.evidences)


def _result():
    missing = MissingInput("sample-2", MissingInputReason.UNKNOWN, ("artifact-2",))
    summary = SampledClassificationSummary(
        "test-taxonomy", "v1", 2,
        (ClassDistributionEntry(1, "cat", 1, ("sample-0",)),
         ClassDistributionEntry(2, "dog", 1, ("sample-1",))),
        (1, 2), (missing,),
    )
    observation = ShotObservationDraft("shot-1", summary, ObservationStatus.PARTIAL)
    sources = tuple(
        ObservationSource(f"observation-{i}", f"evidence-{i}", "vision-run", f"sample-{i}",
                          f"artifact-{i}", f"artifacts/{i}.png", f"sha256:{i}", _point(i))
        for i in range(2)
    )
    evidence = AggregationEvidenceDraft(sources, (missing,))
    metadata = AggregationMetadata("aggregation:test:v1", "sampled-classification", "1", "sha256:cfg",
                                   ("vision-run",), 3, 2)
    return AggregationResult(observation, evidence, metadata)


def test_output_contract_has_shot_feature_and_new_evidence_draft():
    result = _result()
    assert result.observation.target_type == "segment"
    assert result.observation.feature == FEATURE
    assert result.observation.coverage is None
    assert result.observation.confidence is None
    assert result.evidence.kind == "shot_visual_observation_aggregation"
    assert result.metadata.parent_run_ids == ("vision-run",)
    assert result.observation.value.to_value()["scope"] == "sampled_frames"


def test_output_contract_rejects_inconsistent_counts_or_unproven_support():
    result = _result()
    bad_meta = AggregationMetadata("aggregation:test:v1", "rule", "1", "cfg", ("vision-run",), 3, 1)
    with pytest.raises(ValueError, match="analyzed counts"):
        AggregationResult(result.observation, result.evidence, bad_meta)

    unsupported = ClassDistributionEntry(3, "bird", 1, ("not-an-input",))
    summary = SampledClassificationSummary("tax", "1", 1, (unsupported,), (), ())
    draft = ShotObservationDraft("shot-1", summary, ObservationStatus.SUCCESS)
    with pytest.raises(ValueError, match="support sample"):
        AggregationResult(draft, AggregationEvidenceDraft(result.evidence.sources, ()),
                          AggregationMetadata("p", "r", "1", "c", ("vision-run",), 1, 1))


def test_input_and_result_are_finite_json_serializable_and_feature_shape_is_closed():
    input_payload = json.loads(json.dumps(asdict(_input()), allow_nan=False))
    result_payload = json.loads(json.dumps(asdict(_result()), allow_nan=False))
    assert input_payload["shot"]["span"]["start"]["pts"] == 9000
    assert result_payload["metadata"]["analyzed_sample_count"] == 2
    value = _result().observation.value.to_value()
    assert set(value) == {
        "taxonomy", "taxonomy_version", "analyzed_sample_count", "class_distribution",
        "disagreements", "missing_inputs", "schema_version", "scope",
    }
    assert value["schema_version"] == "1.0"
    assert value["scope"] == "sampled_frames"
