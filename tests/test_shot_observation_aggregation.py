from dataclasses import asdict

import pytest

from aei.domain.aggregation import (
    AggregationInput, MissingInput, MissingInputReason, aggregate_shot_observations,
)
from aei.domain.models import (
    Evidence, Observation, ObservationStatus, Rational, Sample, TemporalSegment,
    TimePoint, TimeSpan,
)


def _make(classes=(1, 1), hashes=None, missing=(), taxonomy="tax"):
    def p(i): return TimePoint("v", 100 + i, Rational(1, 100), i)
    shot = TemporalSegment("shot", "layer", "shot", TimeSpan(p(0), p(max(1, len(classes)))))
    samples = tuple(Sample(f"s{i}", "sampling", "asset", "representative", "frame",
                           TimeSpan(p(i), p(i)), i, segment_id="shot") for i in range(len(classes)))
    evidences, observations = [], []
    for i, class_id in enumerate(classes):
        ev = Evidence(f"e{i}", "vision", "artifact_classification_input",
                      external_artifact_ref=f"frame/{i}.png", artifact_hash=(hashes or [f"h{i}"] * len(classes))[i],
                      metadata={"sample_id": f"s{i}", "artifact_id": f"a{i}",
                                "source_point": asdict(p(i)), "producer_ref": "model", "taxonomy_version": "1"})
        evidences.append(ev)
        observations.append(Observation(f"o{i}", "vision", "artifact", f"a{i}",
                          "vision.classification", {"label": str(class_id), "class_id": class_id, "taxonomy": taxonomy},
                          evidence_ids=(ev.id,), producer_ref="model"))
    return AggregationInput(shot, samples, tuple(observations), tuple(evidences), tuple(missing)), shot


def test_distribution_disagreement_and_tie_preserve_all_classes():
    inp, _ = _make((1, 2, 1, 2))
    result = aggregate_shot_observations(inp)
    assert [(e.class_id, e.sample_count) for e in result.observation.value.class_distribution] == [(1, 2), (2, 2)]
    assert result.observation.value.disagreements == (1, 2)
    assert result.observation.value_status is ObservationStatus.SUCCESS
    assert result.observation.confidence is None and result.observation.coverage is None


def test_duplicate_presentation_frame_is_counted_once_but_same_hash_at_other_frame_is_not():
    inp, shot = _make((1, 2, 2), hashes=["same", "same", "same"])
    # Make the second sample a duplicate source presentation frame.
    samples = list(inp.samples)
    samples[1] = Sample("s1", "sampling", "asset", "representative", "frame", samples[0].source_span, 0, segment_id=shot.id)
    evidences = list(inp.evidences)
    meta = dict(evidences[1].metadata); meta["source_point"] = asdict(samples[0].source_span.start)
    evidences[1] = Evidence("e1", "vision", "artifact_classification_input", external_artifact_ref="frame/1.png", artifact_hash="same", metadata=meta)
    inp = AggregationInput(shot, tuple(samples), inp.artifact_observations, tuple(evidences))
    result = aggregate_shot_observations(inp)
    assert result.observation.value.analyzed_sample_count == 2
    assert result.observation.value.class_distribution[0].sample_ids == ("s0",)
    assert result.observation.value.class_distribution[1].sample_ids == ("s2",)


@pytest.mark.parametrize("reason,status", [
    (MissingInputReason.FAILED, ObservationStatus.PARTIAL),
    (MissingInputReason.UNKNOWN, ObservationStatus.PARTIAL),
    (MissingInputReason.NOT_COVERED, ObservationStatus.PARTIAL),
])
def test_missing_inputs_drive_status(reason, status):
    inp, _ = _make((1, 2), missing=(MissingInput("s1", reason),))
    result = aggregate_shot_observations(inp)
    assert result.observation.value_status is status


def test_incompatible_taxonomy_and_provenance_are_rejected():
    inp, _ = _make((1,))
    with pytest.raises(ValueError, match="taxonomy"):
        aggregate_shot_observations(inp, taxonomy="other")
    with pytest.raises(ValueError, match="producer"):
        aggregate_shot_observations(inp, producer_ref="other")
