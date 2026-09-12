import math

from aei.domain.evaluation import EvaluationInput, EvaluationStatus
from aei.domain.models import Observation, ObservationStatus
from aei.evaluation.contract import ContractEvaluator


def make_observation(**changes):
    values = dict(id="o", run_id="r", target_type="artifact", target_id="a", feature="f", value={"label": "x"}, value_status=ObservationStatus.SUCCESS, evidence_ids=("e",), producer_ref="p")
    values.update(changes)
    return Observation(**values)


def test_valid_observation_passes():
    result = ContractEvaluator().evaluate(EvaluationInput(make_observation(), evaluation_run_id="er"))
    assert result.status is EvaluationStatus.PASS
    assert result.evaluation_kind == "contract"


def test_missing_producer_fails():
    result = ContractEvaluator().evaluate(EvaluationInput(make_observation(producer_ref=None)))
    assert result.status is EvaluationStatus.FAIL
    assert any(f.code == "missing_producer_ref" for f in result.findings)


def test_invalid_status_fails():
    obs = make_observation()
    object.__setattr__(obs, "value_status", "bad")
    result = ContractEvaluator().evaluate(EvaluationInput(obs))
    assert result.status is EvaluationStatus.FAIL
    assert any(f.code == "invalid_status" for f in result.findings)


def test_non_json_value_fails():
    obs = make_observation()
    object.__setattr__(obs, "value", {"bad": object()})
    result = ContractEvaluator().evaluate(EvaluationInput(obs))
    assert result.status is EvaluationStatus.FAIL


def test_non_finite_value_fails():
    obs = make_observation()
    object.__setattr__(obs, "value", {"score": math.nan})
    result = ContractEvaluator().evaluate(EvaluationInput(obs))
    assert result.status is EvaluationStatus.FAIL
