from dataclasses import replace

from aei.benchmark.metrics import VisionClassificationAccuracy
from aei.domain.benchmark import (
    BenchmarkAnnotation,
    BenchmarkCase,
    BenchmarkDataset,
    BenchmarkInputSnapshot,
)


def _snapshot(*cases):
    dataset = BenchmarkDataset("ds", "vision fixture", "d1", "a1", "artifact_vision_classification", tuple(c.id for c in cases))
    return BenchmarkInputSnapshot(dataset, tuple(cases), "benchmark:vision-classification:v1")


def _case(case_id, class_id, *, label="cat", taxonomy="fixture-taxonomy", expected_id=None, status=None):
    expected_id = class_id if expected_id is None else expected_id
    annotation = BenchmarkAnnotation(case_id, f"artifact-{case_id}", "vision.classification", {
        "class_id": expected_id, "label": label, "taxonomy": taxonomy,
    }, "a1")
    return BenchmarkCase(case_id, f"artifact-{case_id}", "vision.classification", annotation,
                         observation_id=f"observation-{case_id}", observed_value={
                             "class_id": class_id, "label": label, "taxonomy": taxonomy,
                         }, observed_status=status)


def test_accuracy_uses_class_id_and_ignores_confidence():
    result = VisionClassificationAccuracy().calculate(_snapshot(_case("1", 1), _case("2", 2, expected_id=9)))
    assert result.status == "COMPUTED"
    assert result.values["accuracy"] == 0.5
    assert result.values["correct_case_count"] == 1


def test_normal_wrong_class_is_incorrect_even_when_label_differs():
    result = VisionClassificationAccuracy().calculate(_snapshot(_case("1", 1, expected_id=2, label="dog")))
    assert result.evaluated_case_count == 1
    assert result.unevaluable_case_count == 0
    assert result.values["incorrect_case_count"] == 1
    assert result.values["accuracy"] == 0.0


def test_taxonomy_and_status_mismatches_are_unevaluable():
    taxonomy = _case("1", 1)
    taxonomy = replace(taxonomy, observed_value={"class_id": 1, "label": "cat", "taxonomy": "other"})
    status = _case("2", 1, status="UNKNOWN")
    result = VisionClassificationAccuracy().calculate(_snapshot(taxonomy, status))
    assert result.evaluated_case_count == 0
    assert result.unevaluable_case_count == 2
    assert result.status == "NOT_EVALUABLE"
    assert result.metadata["unevaluable_reasons"] == {"taxonomy_mismatch": 1, "unsupported_observation_status": 1}


def test_same_class_label_inconsistency_is_unevaluable():
    case = _case("1", 1)
    case = replace(case, annotation=BenchmarkAnnotation("1", "artifact-1", "vision.classification", {
        "class_id": 1, "label": "dog", "taxonomy": "fixture-taxonomy",
    }, "a1"))
    result = VisionClassificationAccuracy().calculate(_snapshot(case))
    assert result.evaluated_case_count == 0
    assert result.unevaluable_case_count == 1
    assert result.metadata["unevaluable_reasons"] == {"label_mismatch": 1}


def test_missing_classification_fields_are_unevaluable():
    case = _case("1", 1)
    result = VisionClassificationAccuracy().calculate(_snapshot(replace(case, observed_value={"label": "cat", "taxonomy": "fixture-taxonomy"})))
    assert result.evaluated_case_count == 0
    assert result.unevaluable_case_count == 1
    assert result.metadata["unevaluable_reasons"] == {"missing_classification_field": 1}


def test_empty_required_fields_are_unevaluable():
    case = _case("1", 1)
    result = VisionClassificationAccuracy().calculate(_snapshot(replace(case, observed_value={"class_id": None, "label": "", "taxonomy": ""})))
    assert result.evaluated_case_count == 0
    assert result.unevaluable_case_count == 1


def test_missing_observation_and_annotation_remain_unevaluable():
    missing_observation = BenchmarkCase("1", "artifact-1", "vision.classification", _case("1", 1).annotation)
    missing_annotation = BenchmarkCase("2", "artifact-2", "vision.classification", None,
                                      observation_id="observation-2", observed_value={"class_id": 1, "label": "cat", "taxonomy": "fixture-taxonomy"})
    result = VisionClassificationAccuracy().calculate(_snapshot(missing_observation, missing_annotation))
    assert result.evaluated_case_count == 0
    assert result.unevaluable_case_count == 2
