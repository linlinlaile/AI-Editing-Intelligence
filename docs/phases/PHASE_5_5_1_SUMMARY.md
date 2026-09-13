# Phase 5.5.1 Benchmark Dataset Contract Summary

本阶段建立 Benchmark Dataset Contract v1 的最小 vertical slice。Benchmark 与现有 Evaluation evaluator 分离：

```text
Evaluator: Observation → EvaluationResult
Benchmark: Dataset + Annotation + Snapshot → MetricResult / BenchmarkReport
```

新增的 domain 契约包含 `BenchmarkDataset`、`BenchmarkAnnotation`、`BenchmarkCase`、`BenchmarkInputSnapshot`、`MetricResult` 和 `BenchmarkReport`。Snapshot 要求 case membership 与 dataset 完全一致，保留 dataset version、annotation version、evaluator、producer/model/config 和 analysis run metadata。

`src/aei/application/benchmark.py` 提供 `BenchmarkRunner`、`MetricCalculator` protocol 和 `BenchmarkEvaluationUseCase`。它们只协调已准备的 immutable snapshot，不访问 repository、SQLite、媒体或模型，也不重新运行 analyzer。

本阶段没有实现 accuracy、precision、recall、F1 或其他具体质量指标。MetricResult 只承载通用 metric metadata、状态、计数和结果字段；测试使用 `NOT_COMPUTED` skeleton calculator 验证执行链路。

本阶段不新增 storage、migration、Observation/Evidence 字段或 EvaluationResult 字段。
