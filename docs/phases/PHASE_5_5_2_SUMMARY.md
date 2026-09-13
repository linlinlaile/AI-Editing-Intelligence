# Phase 5.5.2 Benchmark Evaluation Vertical Slice Summary

Phase 5.5.2 implements the first semantic benchmark metric while preserving the
boundary between evaluation and benchmarking:

```text
Benchmark Dataset + Annotation + Snapshot
        ↓
VisionClassificationAccuracy
        ↓
MetricResult / BenchmarkReport
```

The metric is `vision.classification.accuracy` version `v1` and evaluates
Artifact-level `vision.classification` observations. `class_id` is the primary
correctness key. A case enters the accuracy denominator only when it has a
SUCCESS observation, a matching taxonomy, and non-empty `class_id`, `label`,
and `taxonomy` fields. Matching class IDs are correct; different class IDs are
incorrect regardless of their labels. Taxonomy mismatch, same-class label
inconsistency, missing inputs, invalid required fields, and unsupported
Observation statuses are unevaluable. Confidence is not used for correctness.
When no case is evaluable, the result is `NOT_EVALUABLE` and no accuracy value
is emitted; unevaluable counts and reasons remain visible.

The implementation is in `src/aei/benchmark/metrics.py`. It consumes an
evaluation snapshot and does not access repositories, media, models or the
EvaluationResult evaluator path. Benchmark reports retain dataset,
annotation, metric, evaluator, producer, model, config and analysis-run
provenance. No storage schema or Observation/Evidence contract was changed.

Tests cover correct and incorrect cases, taxonomy and status exclusions, label
consistency, missing classification fields, missing observations or
annotations, annotation-version mismatch, report provenance, and Runner
output. The full suite uses synthetic fixtures only; it does not establish
real-world model accuracy. The explicitly opt-in real-model test remains
skipped unless local weights are supplied.
