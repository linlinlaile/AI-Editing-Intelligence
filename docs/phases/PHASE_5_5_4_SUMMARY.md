# Phase 5.5.4 Benchmark Workflow Consistency Hardening Summary

## 1. Phase objective

Phase 5.5.4 完成 ADR-0014 已定义的 benchmark workflow consistency hardening。目标是在不改变 benchmark 架构、BenchmarkReport schema 或 Semantic Timeline 契约的前提下，确保 MetricResult、BenchmarkReport、revision identity 和比较输入的一致性可验证，并形成可测试的完整 workflow 闭环。

本阶段不修改 ADR-0014，也不创建 ADR-0015。

## 2. Implemented capabilities

本阶段完成：

- 独立 `MetricResultValidator`。
- 独立 `BenchmarkReportValidator`。
- `BenchmarkRunner` workflow validation hardening。
- 独立 `RevisionIdentityValidator`。
- 独立 `EvaluationBasisIdentityValidator`。
- 集中的 comparison identity validation。
- Comparator 对 metric name/version、calculation config、inclusion rules、reporting rules、dataset/annotation identity、metric config identity 和 fingerprint 的可比性检查。
- `NOT_COMPARABLE` 时保留 transition analysis，并标记 `DIAGNOSTIC_ONLY`。
- 旧 report 缺少 identity 时可读取，但不会补造 identity，也不会生成严格比较结论。

## 3. Architecture changes

新增的是 validation layer 和 workflow checks，不是新的 benchmark 架构：

```text
BenchmarkInputSnapshot
        ↓
BenchmarkRunner
        ↓
MetricResultValidator
        ↓
BenchmarkReport creation
        ↓
BenchmarkReportValidator
        ↓
BenchmarkReport
        ↓
Identity validation
        ↓
Comparator
        ↓
BenchmarkComparisonReport
```

`BenchmarkRunner` 仍只协调 prepared snapshot 和 MetricCalculator。Benchmark 不调用 Analyzer，不访问 Observation、Evidence、media、repository 或 SQLite。

未修改 Observation、Evidence、EvaluationResult 或 BenchmarkReport schema。

## 4. Validation layers

### MetricResultValidator

负责 MetricResult 内部一致性：

- metric result status；
- evaluated/unevaluable counts；
- case outcome 唯一性及计数对应关系；
- accuracy value 范围和基本状态约束。

### BenchmarkReportValidator

负责 BenchmarkReport 外部一致性：

- report 基础身份字段；
- delegated MetricResult validation；
- metric identity 与 provenance；
- dataset、annotation 与 evaluation basis version/identity；
- revision provenance；
- report contract version。

### Identity validators

`RevisionIdentityValidator` 验证既有 RevisionIdentity：

- producer_ref；
- model_ref；
- config_ref；
- code_revision；
- analysis_run_ids；
- completeness status；
- preprocessing/input fingerprint 的格式和一致性使用条件。

`EvaluationBasisIdentityValidator` 验证：

- dataset identity/version；
- annotation identity/version；
- case membership identity；
- task；
- feature；
- taxonomy。

## 5. Benchmark workflow final form

单次 benchmark execution：

```text
Dataset + Annotation + prepared evaluation input
        ↓
MetricCalculator
        ↓
MetricResultValidator
        ↓
BenchmarkReport assembly
        ↓
BenchmarkReportValidator
        ↓
validated BenchmarkReport
```

比较 workflow：

```text
baseline BenchmarkReport + candidate BenchmarkReport
        ↓
validation-layer comparability checks
        ↓
case_id alignment
        ↓
transition/evaluability analysis
        ↓
strict metric delta when permitted
        ↓
BenchmarkComparisonReport
```

Comparator 不重新解释 Observation，也不根据 Observation/Evidence 推导 outcome。

## 6. Identity model boundary

本阶段验证既有 identity contract，不扩展新的 identity model。

`RevisionIdentity` 保持以下语义：

- producer
- model
- config
- code revision
- analysis run IDs
- preprocessing/input fingerprint

`task`、`feature`、`taxonomy` 不加入 RevisionIdentity；它们继续属于 `EvaluationBasisIdentity`。

两类 fingerprint/identity 语义保持分离：

- revision fingerprint 表示分析输入/preprocessing revision；
- evaluation basis identities 表示 dataset、annotation、case membership 及 task-specific evaluation basis。

缺少或不一致的 identity 不会被猜测或补造。

## 7. Comparator boundary

Comparator 只消费既有 benchmark domain contracts 和 validation layer 结果，负责：

- 接收 comparability reasons；
- 按稳定 `case_id` 对齐 outcome；
- 统计 transition 和 evaluability shift；
- 在严格可比条件下计算 metric delta；
- 生成 `BenchmarkComparisonReport`。

Identity、fingerprint、metric comparability 规则集中在 validation layer。不可比时 transition 仍可保留，但只能是 diagnostic information，不产生 regression/improvement 结论。

## 8. ADR-0014 relationship

Phase 5.5.4 实现并强化 ADR-0014 已定义的：

- benchmark workflow boundary；
- report/metric consistency prerequisites；
- revision identity and fingerprint validation；
- evaluation basis comparability；
- metric comparability rules；
- strict delta conditions；
- backward compatibility and `NOT_COMPARABLE` semantics；
- diagnostic-only transition behavior。

ADR-0014 未修改。未引入 ADR-0015。

## 9. Tests

完整测试命令使用项目 `.venv` 解释器：

```powershell
.\\.venv\\Scripts\\python.exe -m pytest -q
```

结果：

```text
116 passed, 1 skipped
```

跳过项为显式 opt-in 的真实模型测试。

测试覆盖 workflow success、MetricResult blocking、BenchmarkReport blocking、identity/fingerprint mismatch、task/taxonomy mismatch、diagnostic-only semantics、backward compatibility 以及既有 benchmark regression。

## 10. Explicit non-goals

本阶段明确不实现：

- benchmark persistence；
- quality gate 或 automatic decision；
- CapabilityRegistry；
- Temporal Observation；
- Retrieval benchmark 或 Retrieval 能力；
- 新 benchmark 架构；
- Observation/Evidence/EvaluationResult schema 修改；
- Phase 5.6 能力。

## 11. Design invariants

Phase 5.5.4 establishes the following long-term invariants:

1. **Observation is never replaced by Benchmark result.**

   Benchmark 负责评价已有分析结果，不替代 Observation/Evidence，也不改变分析语义。

2. **Benchmark evaluates prepared outputs only.**

   Benchmark 不负责媒体理解，不调用 Analyzer，不重新执行模型推理。

3. **Comparator only compares validated reports.**

   Comparator 消费经过 validation 的 BenchmarkReport，不承担 MetricResult 或 identity validation 职责。

4. **NOT_COMPARABLE is preferred over guessed comparison.**

   当 identity、evaluation basis 或 provenance 不足以证明可比时，应返回 `NOT_COMPARABLE`，而不是推测 regression/improvement。

5. **Identity absence cannot be silently repaired.**

   缺失 identity、fingerprint 或 provenance 时，不补造、不猜测历史信息。

6. **Diagnostic transition is not equivalent to regression/improvement.**

   不可比情况下产生的 transition analysis 只能用于 diagnostic information，不能解释为模型改进或退化。
