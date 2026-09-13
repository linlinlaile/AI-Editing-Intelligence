# Phase 5.5.3 Benchmark Revision Comparison Summary

## 1. Phase objective

建立最小的 benchmark revision comparison vertical slice：消费两个既有的
`BenchmarkReport`，验证比较基础是否一致，按稳定 `case_id` 计算 outcome
迁移，并在严格可比条件下计算 metric delta。

本阶段不重新运行 analyzer 或 model，不修改 Observation、Evidence 或
EvaluationResult，也不引入 benchmark persistence。

## 2. Completed capabilities

### RevisionIdentity

`RevisionIdentity` 结构化记录 producer、model、config、code revision、analysis
run IDs 和可选 fingerprint，并区分：

- `MISSING`
- `INCOMPLETE`
- `COMPLETE`

只有双方 revision identity 均为 `COMPLETE` 时，比较才可能声明为
`COMPARABLE`。

### EvaluationBasisIdentity

`EvaluationBasisIdentity` 表示固定评价基础，包含：

- dataset identity/version；
- annotation identity/version；
- case membership identity；
- task；
- feature；
- taxonomy。

双方评价基础必须一致，且报告层 dataset/version/annotation 信息也必须一致。

### CaseOutcome

新增独立的类型化 case-level contract，支持：

- `CORRECT`
- `INCORRECT`
- `UNEVALUABLE`
- `MISSING`

`UNEVALUABLE` 可携带 metric 定义的 reason。重复 `case_id` 会被拒绝，避免
比较时静默覆盖。

### BenchmarkComparisonReport

新增比较报告，保留：

- baseline/candidate report identity；
- baseline/candidate evaluation basis；
- baseline/candidate revision identity；
- baseline/candidate metric name、version 和可选 config identity；
- comparability status 与原因；
- case transition counts；
- evaluability shift；
- metric delta 及其状态；
- comparison producer/version 和生成时间。

报告只保存 comparison 所需的引用、identity、计数和 outcome 信息，不复制
Observation、Evidence 或媒体 payload。

### Comparator

`aei.benchmark.comparison.compare_benchmark_reports` 是纯 benchmark comparison
逻辑，负责：

1. 验证比较基础与 revision identity；
2. 按稳定 `case_id` 对齐两侧 metric outcomes；
3. 统计 outcome transitions；
4. 统计 evaluability shift；
5. 在严格条件满足时计算 metric delta。

### Diagnostic-only non-comparable semantics

当 `comparability_status != COMPARABLE` 时，transition counts 仍可作为输入
覆盖和结果变化的诊断信息，但报告明确标记：

```text
transition_interpretation = DIAGNOSTIC_ONLY
```

这些 transitions 不得被解释为 regression 或 improvement 结论。

## 3. Architecture boundaries

本阶段保持以下边界：

```text
Benchmark != Evaluator
MetricResult != EvaluationResult
BenchmarkComparisonReport != Observation
BenchmarkComparisonReport != EvaluationResult
```

`EvaluationResult` 表示单 Observation 的契约/grounding evaluation；
`BenchmarkComparisonReport` 表示跨 benchmark revision 的比较结果。两者均属于
evaluation 相关体系，但语义和生命周期不同，不应互相替代。

Comparator 只消费 benchmark domain contracts，不访问：

- Observation；
- Evidence；
- Analyzer；
- Model；
- Media；
- Repository；
- SQLite。

Benchmark comparison 不生成或修改 Observation、Evidence 或 EvaluationResult。

## 4. Comparison semantics

### Comparability validation

严格比较要求：

- dataset/report identity 和 version 一致；
- annotation identity 和 version 一致；
- `EvaluationBasisIdentity` 完全一致；
- metric name/version 一致；
- 双方 revision identity 均为 `COMPLETE`。

不满足条件时返回 `NOT_COMPARABLE`，并记录原因。

### Case transition

两侧按稳定 `case_id` 对齐，支持：

- `CORRECT → INCORRECT`；
- `INCORRECT → CORRECT`；
- `CORRECT → UNEVALUABLE`；
- `UNEVALUABLE → CORRECT`；
- 其他 outcome 组合；
- 缺少一侧 case 时使用 `MISSING` 诊断状态。

Comparator 不从 Observation 原始字段重新推导 outcome。

### Metric delta conditions

正式 metric delta 仅在以下条件全部满足时计算：

- comparison 为 `COMPARABLE`；
- baseline/candidate 可评价 case 集合完全一致；
- 两侧均提供相应 metric value。

可评价集合变化时不会把整体 accuracy 差值当作严格 regression 或 improvement。

### Diagnostic-only interpretation

不可比报告可以保留 transition 和 evaluability shift，用于诊断覆盖变化、
输入缺失或评价基础变化，但不产生严格质量结论。

## 5. Tests

完整测试结果：

```text
89 passed, 1 skipped
```

跳过项为显式 opt-in 的真实模型测试，需要本地权重和 `RUN_REAL_MODEL=1`。

测试包含 benchmark comparison、revision completeness、basis mismatch、
case transition、duplicate case outcome 和既有 Phase 5.5.1/5.5.2 回归覆盖。

## 6. Known limitations

- task-aware `RevisionIdentity` 未实现；
- `MetricResult` full consistency validation 未实现；
- benchmark report 和 comparison report 没有 persistence；
- 没有 quality gate 或 automatic decision；
- 本阶段仍只覆盖既有视觉分类 accuracy v1，不新增其他 metric。
