import pytest

from aei.benchmark import MetricResultValidator
from aei.domain.benchmark import CaseOutcome, MetricResult


def test_validator_accepts_computed_result():
    result = MetricResult(
        "m", "v1", "COMPUTED", 1, 1,
        values={"accuracy": 1.0},
        case_outcomes=(CaseOutcome("a", "CORRECT"), CaseOutcome("b", "UNEVALUABLE", "missing")),
    )
    MetricResultValidator.validate(result)


@pytest.mark.parametrize(
    "result, message",
    [
        (MetricResult("m", "v1", "COMPUTED", 0, 0), "requires evaluated"),
        (MetricResult("m", "v1", "NOT_EVALUABLE", 1, 0), "cannot contain"),
        (MetricResult("m", "v1", "COMPUTED", 2, 0, case_outcomes=(CaseOutcome("a", "CORRECT"),)), "evaluated_case_count"),
        (MetricResult("m", "v1", "NOT_EVALUABLE", 0, 0, values={"accuracy": 0.0}), "accuracy cannot"),
        (MetricResult("m", "v1", "COMPUTED", 1, 0, values={"accuracy": 2.0}), "between 0 and 1"),
    ],
)
def test_validator_rejects_inconsistent_results(result, message):
    with pytest.raises(ValueError, match=message):
        MetricResultValidator.validate(result)


def test_validator_accepts_not_computed_skeleton():
    MetricResultValidator.validate(MetricResult("m", "v1", "NOT_COMPUTED", 0, 2))
