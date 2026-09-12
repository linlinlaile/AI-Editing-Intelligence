import inspect
from aei.domain.evaluation import EvaluationInput
from aei.domain.models import Observation, ObservationStatus
from aei.evaluation.benchmark import BenchmarkEvaluator
from aei.ports.evaluator import Evaluator

def test_benchmark_matches_evaluator_interface():
    assert isinstance(BenchmarkEvaluator(), Evaluator)

def test_benchmark_is_not_evaluable():
    o=Observation("o","r","artifact","a","f","x",ObservationStatus.SUCCESS,evidence_ids=("e",),producer_ref="p")
    result=BenchmarkEvaluator().evaluate(EvaluationInput(o,evaluation_run_id="er"))
    assert result.evaluation_kind == "benchmark"
    assert result.status.value == "NOT_EVALUABLE"
    assert result.findings[0].code == "benchmark_not_implemented"

def test_benchmark_has_no_repository_dependency():
    source = inspect.getsource(BenchmarkEvaluator)
    assert "repository" not in source.lower()
    assert "sqlite" not in source.lower()
