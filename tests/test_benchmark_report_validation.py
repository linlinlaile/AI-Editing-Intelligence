import pytest

from aei.benchmark import BenchmarkReportValidator
from aei.domain.benchmark import BenchmarkReport, CaseOutcome, EvaluationBasisIdentity, MetricResult, RevisionIdentity


def _report(**kwargs):
    metric = MetricResult("m", "v1", "COMPUTED", 1, 0, values={"accuracy": 1.0}, case_outcomes=(CaseOutcome("c", "CORRECT"),))
    defaults = dict(
        id="r", evaluation_run_id="eval", dataset_id="ds", dataset_version="d1", annotation_version="a1",
        evaluator_ref="eval:v1", metric_results=(metric,), metadata={"provenance": {"dataset_version": "d1", "annotation_version": "a1", "evaluator_ref": "eval:v1", "metric_versions": ("v1",)}},
        dataset_identity="ds:f", annotation_identity="ann:f",
        evaluation_basis=EvaluationBasisIdentity("ds:f", "d1", "ann:f", "a1", "cases:f", "task", "feature", "tax"),
        revision_identity=RevisionIdentity("p", "m", "c", "code", ("run",)),
    )
    defaults.update(kwargs)
    return BenchmarkReport(**defaults)


def test_report_validator_accepts_consistent_report():
    BenchmarkReportValidator.validate(_report())


@pytest.mark.parametrize("change, message", [
    ({"dataset_version": "d2"}, "provenance dataset_version"),
    ({"annotation_identity": "other"}, "annotation identity"),
    ({"metadata": {"provenance": {"metric_versions": ("v2",)}}}, "metric_versions"),
    ({"metadata": {"provenance": {"producer_ref": "other"}}, "revision_identity": RevisionIdentity("p", "m", "c", "code", ("run",))}, "provenance producer_ref"),
    ({"report_contract_version": "v2"}, "unsupported report contract"),
])
def test_report_validator_rejects_external_inconsistency(change, message):
    with pytest.raises(ValueError, match=message):
        BenchmarkReportValidator.validate(_report(**change))
