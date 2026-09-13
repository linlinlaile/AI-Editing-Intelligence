from dataclasses import asdict, replace

from aei.domain.aggregation import AggregationInput, aggregate_shot_observations
from aei.domain.aggregation import generate_shot_observation_evidence
from aei.domain.evaluation import EvaluationInput, EvaluationStatus
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
from aei.evaluation.contract import ContractEvaluator
from aei.evaluation.grounding import EvidenceGroundingEvaluator


def _materialized():
    def point(index):
        return TimePoint("video:0", 100 + index, Rational(1, 100), index)

    shot = TemporalSegment(
        "shot-1", "layer-1", "shot", TimeSpan(point(0), point(2))
    )
    samples = tuple(
        Sample(
            f"sample-{i}",
            "sampling-run",
            "asset-1",
            "representative_sampling",
            "frame",
            TimeSpan(point(i), point(i)),
            i,
            segment_id=shot.id,
            artifact_ids=(f"artifact-{i}",),
        )
        for i in range(2)
    )
    evidences = tuple(
        Evidence(
            f"vision-evidence-{i}",
            "vision-run",
            "artifact_classification_input",
            external_artifact_ref=f"frames/{i}.png",
            artifact_hash=f"sha256:{i}",
            metadata={
                "sample_id": f"sample-{i}",
                "artifact_id": f"artifact-{i}",
                "source_point": asdict(point(i)),
                "producer_ref": "vision:test:v1",
                "taxonomy_version": "1",
            },
        )
        for i in range(2)
    )
    observations = tuple(
        Observation(
            f"vision-observation-{i}",
            "vision-run",
            "artifact",
            f"artifact-{i}",
            "vision.classification",
            {"label": label, "class_id": class_id, "taxonomy": "test-taxonomy"},
            evidence_ids=(evidences[i].id,),
            producer_ref="vision:test:v1",
        )
        for i, (label, class_id) in enumerate((("cat", 1), ("dog", 2)))
    )
    result = aggregate_shot_observations(
        AggregationInput(shot, samples, observations, evidences),
        taxonomy="test-taxonomy",
        producer_ref="vision:test:v1",
    )
    return generate_shot_observation_evidence(
        result,
        aggregation_run_id="aggregation-run",
        observation_id="shot-observation",
        evidence_id="aggregation-evidence",
    )


def _evaluation_input(observation, evidence, metadata_run_id="aggregation-run"):
    return EvaluationInput(
        observation,
        (evidence,),
        evaluation_run_id="evaluation-run",
        analysis_run_metadata={"run_id": metadata_run_id},
    )


def test_real_shot_aggregation_output_passes_contract_evaluation():
    observation, evidence = _materialized()
    assert observation.target_type == "segment"
    assert observation.target_id == "shot-1"
    assert observation.feature == "vision.sampled_classification_summary"
    assert observation.value["scope"] == "sampled_frames"
    assert observation.value["class_distribution"]
    assert observation.confidence is None
    assert observation.coverage is None

    result = ContractEvaluator().evaluate(
        _evaluation_input(observation, evidence)
    )
    assert result.status is EvaluationStatus.PASS


def test_contract_evaluator_rejects_missing_producer_invalid_status_and_value():
    observation, evidence = _materialized()

    missing_producer = replace(observation, producer_ref=None)
    result = ContractEvaluator().evaluate(_evaluation_input(missing_producer, evidence))
    assert result.status is EvaluationStatus.FAIL
    assert any(f.code == "missing_producer_ref" for f in result.findings)

    invalid_status = replace(observation)
    object.__setattr__(invalid_status, "value_status", "invalid")
    result = ContractEvaluator().evaluate(_evaluation_input(invalid_status, evidence))
    assert result.status is EvaluationStatus.FAIL
    assert any(f.code == "invalid_status" for f in result.findings)

    invalid_value = replace(observation)
    object.__setattr__(invalid_value, "value", {"raw_response": object()})
    result = ContractEvaluator().evaluate(_evaluation_input(invalid_value, evidence))
    assert result.status is EvaluationStatus.FAIL
    assert any(f.code == "invalid_value" for f in result.findings)


def test_direct_aggregation_evidence_passes_grounding_without_lineage_recursion():
    observation, evidence = _materialized()
    result = EvidenceGroundingEvaluator().evaluate(
        _evaluation_input(observation, evidence)
    )
    assert result.status is EvaluationStatus.PASS
    assert result.evaluation_kind == "evidence_grounding"


def test_grounding_fails_for_missing_evidence_reference_and_provenance_mismatch():
    observation, evidence = _materialized()
    missing = EvaluationInput(
        observation,
        (),
        evaluation_run_id="evaluation-run",
        analysis_run_metadata={"run_id": "aggregation-run"},
    )
    result = EvidenceGroundingEvaluator().evaluate(missing)
    assert result.status is EvaluationStatus.FAIL
    assert any(f.code == "missing_evidence_reference" for f in result.findings)

    mismatched = replace(evidence, run_id="other-run")
    result = EvidenceGroundingEvaluator().evaluate(
        _evaluation_input(observation, mismatched)
    )
    assert result.status is EvaluationStatus.FAIL
    assert any(f.code == "provenance_mismatch" for f in result.findings)


def test_grounding_is_not_evaluable_when_direct_evidence_has_no_source_material():
    observation, evidence = _materialized()
    object.__setattr__(evidence, "numeric_measurement", None)
    object.__setattr__(evidence, "external_artifact_ref", None)
    object.__setattr__(evidence, "artifact_hash", None)
    object.__setattr__(evidence, "source_span", None)
    object.__setattr__(evidence, "frame_start", None)
    object.__setattr__(evidence, "frame_end", None)

    result = EvidenceGroundingEvaluator().evaluate(
        _evaluation_input(observation, evidence)
    )
    assert result.status is EvaluationStatus.NOT_EVALUABLE
    assert any(f.code == "untraceable_evidence" for f in result.findings)
