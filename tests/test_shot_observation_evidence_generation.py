from copy import deepcopy

from aei.domain.aggregation import generate_shot_observation_evidence

from test_shot_observation_aggregation_contract import _result


def test_aggregation_result_materializes_shot_observation_and_new_evidence():
    result = _result()
    observation, evidence = generate_shot_observation_evidence(
        result, aggregation_run_id="aggregation-run", observation_id="shot-observation",
        evidence_id="aggregation-evidence",
    )

    assert observation.target_type == "segment"
    assert observation.target_id == "shot-1"
    assert observation.feature == "vision.sampled_classification_summary"
    assert observation.evidence_ids == ("aggregation-evidence",)
    assert observation.confidence is None and observation.coverage is None
    assert evidence.run_id == "aggregation-run"
    assert evidence.id not in result.observation.value.to_value().get("evidence_ids", [])


def test_generated_evidence_contains_provenance_and_does_not_mutate_upstream():
    result = _result()
    upstream = deepcopy(result.evidence.sources)
    _, evidence = generate_shot_observation_evidence(
        result, aggregation_run_id="aggregation-run", observation_id="o-new", evidence_id="e-new",
    )
    metadata = evidence.metadata
    assert metadata["upstream_observation_ids"] == ["observation-0", "observation-1"]
    assert metadata["upstream_evidence_ids"] == ["evidence-0", "evidence-1"]
    assert metadata["upstream_run_ids"] == ["vision-run"]
    assert len(metadata["artifact_references"]) == 2
    assert metadata["aggregation_rule"]["version"] == "1"
    assert metadata["classification_statistics"]["analyzed_sample_count"] == 2
    assert metadata["missing_inputs"][0]["sample_id"] == "sample-2"
    assert result.evidence.sources == upstream

