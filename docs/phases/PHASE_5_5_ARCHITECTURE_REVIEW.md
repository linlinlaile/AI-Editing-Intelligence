# Phase 5.5 Architecture Review

## 1. Review Objective

Phase 5.5 Benchmark Foundation 位于 Semantic Timeline、Observation/Evidence 分析链路之后，承担“对已准备的分析输出进行可复核、可比较质量评价”的架构职责。它把固定数据集、任务标注、指标计算和 revision comparison 组织成独立的 benchmark 闭环，为后续能力提供可重算的质量证据。

进行本次 architecture review，是为了确认 Phase 5.5.1–5.5.4 形成的契约、执行 workflow、验证层和比较语义彼此一致，并与 ADR-0013、ADR-0014 及既有 Observation/Evaluation 边界相容。评审的目标不是扩展能力，而是冻结 Benchmark Foundation 的长期边界、身份语义和不可比处理方式。

本文冻结 Phase 5.5 benchmark foundation；不进入 Phase 5.6，也不改变代码、ADR 或 Semantic Timeline 契约。

## 2. Phase 5.5 Architecture Overview

Phase 5.5 的整体数据流为：

```text
Dataset
   ↓
Annotation
   ↓
BenchmarkInputSnapshot
   ↓
MetricCalculator
   ↓
MetricResult
   ↓
BenchmarkReport
   ↓
BenchmarkComparisonReport
```

- **Dataset**：定义版本化、有限的 benchmark case 集合及其范围、版本和身份。Dataset 是评价资产，不是 Semantic Timeline 的事实来源。
- **Annotation**：为 case 提供任务定义的参考标签或期望值。Annotation 是外部参考数据，不是 Analyzer 生成的 Evidence；其结构和解释由 task/metric contract 定义。
- **BenchmarkInputSnapshot**：为一次执行固定 dataset、annotation、case membership，以及已准备的 Observation、Evidence 和 AnalysisRun 相关输入/provenance。它是稳定的评价输入边界，保证同一 metric 实现和版本可以重算相同结果。
- **MetricCalculator**：只消费 snapshot，按具体 metric contract 计算结果。它不访问 repository、SQLite、媒体或模型，也不重新运行 Analyzer。当前已落地的 metric 是 `vision.classification.accuracy` v1。
- **MetricResult**：承载单一 metric/version 在 case 集合上的状态、计数、case outcome 和 metric-specific value。它描述 benchmark 评价结果，不改变 Observation、Evidence、confidence、coverage 或 AnalysisRun。
- **BenchmarkReport**：封装一次 benchmark execution 的结果及其 dataset、annotation、metric、evaluation basis、producer/model/config 和 analysis-run provenance，作为后续复核和比较的稳定输入。
- **BenchmarkComparisonReport**：消费两个既有 BenchmarkReport，记录可比性、不可比原因、按稳定 `case_id` 对齐的 transition、evaluability shift，以及仅在严格条件满足时的 metric delta。它是派生比较结果，不替代任一单次报告。

## 3. Layer Responsibility Boundary

### Dataset

Dataset 定义 benchmark 的范围、case membership、dataset identity 和 dataset version。增删、替换或重新标识 case 必须形成新的 dataset version。Dataset 不生成 Observation，也不成为 Observation 的权威来源。

### Annotation

Annotation 定义某个 task/feature 下 case 的期望值、参考标签或显式的 unknown/not-covered 状态（仅当对应 task contract 支持）。Annotation identity/version 必须可追溯；修正标签或改变 unknown 规则必须形成新的 annotation version。Annotation 不属于 Evidence，也不表示模型来源。

### BenchmarkInputSnapshot

Snapshot 将 Dataset、Annotation、case membership 和已准备的评价输入固定在一次执行边界内，并保留复现所需的 producer/model/config/analysis-run metadata。它由应用层准备；benchmark runner 和 metric calculator 只消费其内容，不从媒体或存储层补取事实。

### MetricResult

MetricResult 是一个 metric version 对固定 case 集合的结构化输出，包含状态、evaluated/unevaluable counts、case outcomes、原因和适用的 metric value。MetricResult 不修改 Observation 状态，不替代 EvaluationResult，也不把 benchmark 分数提升为永久语义事实。

### BenchmarkReport

BenchmarkReport 是一次运行的可追溯封装，连接 MetricResult 与 dataset、annotation、evaluation basis、metric identity 和 revision provenance。它必须经过报告级验证，才能作为比较输入；旧报告可以读取，但缺少身份时不能被补造为严格可比报告。

### BenchmarkComparisonReport

BenchmarkComparisonReport 是两个已存在报告的派生结果，包含 baseline/candidate report identity、evaluation basis、revision identity、comparability status/reasons、case transition counts、evaluability shift 和条件化 metric delta。它不复制 Observation、Evidence 或媒体 payload。

Benchmark 不负责 Observation generation；不调用 Analyzer 或模型，不访问 Observation/Evidence、Media、Repository 或 SQLite。Benchmark 也不替代现有 `EvaluationResult`：后者仍表示 Evaluator 对单个 Observation 的契约、grounding 或其他独立评价结果。

## 4. Validation Architecture

Phase 5.5.4 在既有 benchmark 架构上建立独立 validation layer，形成以下闭环：

```text
BenchmarkInputSnapshot
        ↓
BenchmarkRunner
        ↓
MetricResultValidator
        ↓
BenchmarkReport assembly
        ↓
BenchmarkReportValidator
        ↓
validated BenchmarkReport
        ↓
identity/comparability validation
        ↓
Comparator
```

- **MetricResultValidator**：验证 metric result status、evaluated/unevaluable counts、case outcome 唯一性及计数对应关系、accuracy value 范围和基本状态约束，阻止内部自相矛盾的结果进入报告。
- **BenchmarkReportValidator**：验证 report contract version、基础身份字段、MetricResult 委托验证、metric identity/provenance、dataset/annotation/evaluation basis 一致性以及 revision provenance，确保报告可作为后续比较输入。
- **RevisionIdentityValidator**：验证 producer_ref、model_ref、config_ref、code_revision、analysis_run_ids、completeness status，以及 preprocessing/input fingerprint 的格式和使用一致性。缺失或不完整的身份不会被猜测补齐。
- **EvaluationBasisIdentityValidator**：验证 dataset identity/version、annotation identity/version、case membership identity、task、feature 和 taxonomy，确保评价条件的身份语义完整。

Comparator 使用这些验证结果进行集中式可比性判断；它不重新承担 metric result、report 或 identity 的内部解释职责。

## 5. Comparator Boundary

Comparator 冻结为纯 benchmark-domain comparison 逻辑，负责：

- 判断 baseline 与 candidate 是否满足 comparability 条件；
- 按稳定 `case_id` 对齐两侧 outcome；
- 统计 `CORRECT`、`INCORRECT`、`UNEVALUABLE`、`MISSING` 等 transition；
- 统计 evaluability shift；
- 仅在严格条件满足时计算 metric delta；
- 生成 BenchmarkComparisonReport 及不可比原因。

Comparator 不负责：

- Analyzer 或 Observation generation；
- 重新解释 Observation 或 Evidence；
- Media 读取或模型执行；
- Repository、SQLite 或其他持久化访问；
- 推导缺失 case 的正确/错误状态；
- 把 diagnostic transition 自动解释为 regression 或 improvement。

Comparator 只消费经过验证的 benchmark contracts 和 metric outputs；它不根据 Observation 原始字段自行推导 outcome。

## 6. Identity Model Boundary

`RevisionIdentity` 与 `EvaluationBasisIdentity` 是两种独立身份，不能互相替代。

- **RevisionIdentity** 回答：“结果如何产生？”它记录 producer、model、config、code revision、analysis run IDs，以及会影响输入的 preprocessing/input fingerprint 等分析来源。
- **EvaluationBasisIdentity** 回答：“结果在哪个评价条件下成立？”它记录 dataset identity/version、annotation identity/version、case membership identity、task、feature 和 taxonomy。

`task`、`feature`、`taxonomy` 不属于 RevisionIdentity；它们属于 EvaluationBasisIdentity。两类 identity/fingerprint 的缺失、不一致或混合归属都必须显式暴露，不能静默猜测或补造。

## 7. Comparability Semantics

严格可比至少要求以下内容一致且可证明：

- dataset identity、dataset version 和 case membership；
- annotation identity、annotation version 及其内容基础；
- metric name/version、计算配置、纳入规则和 reporting rules；
- EvaluationBasisIdentity，包括 task、feature、taxonomy；
- revision provenance 完整，且双方 RevisionIdentity 均为 `COMPLETE`。

仅版本字符串相同或 case 数量相同不足以证明内容相同；无法证明 identity/fingerprint 一致时，比较状态必须为 `NOT_COMPARABLE`。

不可比时仍允许保留 transition counts 和 evaluability shift，作为输入覆盖、缺失或评价条件变化的 diagnostic information，并标记 `DIAGNOSTIC_ONLY`。不可比时禁止据此推断 regression 或 improvement；整体 metric 差值也不能被当作严格质量结论。只有在可比且双方可评价 case 集合完全一致、两侧均提供相应 metric value 时，才允许生成正式 metric delta。

## 8. Design Invariants

1. Observation is never replaced by Benchmark result.
2. Benchmark evaluates prepared outputs only.
3. Comparator only compares validated reports.
4. `NOT_COMPARABLE` is preferred over guessed comparison.
5. Identity absence cannot be silently repaired.
6. Diagnostic transition is not equivalent to regression/improvement.

这些不变量适用于单次 benchmark workflow、revision comparison 和未来对现有契约的兼容扩展。

## 9. Frozen Scope

Phase 5.5 已冻结以下 foundation：

- benchmark dataset、annotation、snapshot、metric、report 和 comparison contracts；
- 从 prepared input 到 MetricResult/BenchmarkReport 的 benchmark workflow；
- MetricResult、BenchmarkReport、RevisionIdentity 和 EvaluationBasisIdentity 的 validation；
- 基于稳定 case identity 的 case alignment、transition 和 evaluability analysis；
- 严格可比时的 metric delta 规则，以及 `NOT_COMPARABLE`/`DIAGNOSTIC_ONLY` 语义。

该冻结建立在 Phase 5.5.1–5.5.4 实现和 ADR-0013、ADR-0014 的共同边界上。

## 10. Explicit Non-goals

Phase 5.5 不包括：

- benchmark persistence；
- SQLite migration；
- quality gate 或 automatic decision；
- CapabilityRegistry；
- Observation/Evidence schema modification；
- Retrieval benchmark；
- Temporal Observation implementation；
- automatic model selection；
- universal cross-task score。

这些事项不因本次架构冻结而获得隐含授权，也不应通过 benchmark contract 偷渡进当前阶段。

## 11. Future Extension Constraints

未来扩展必须遵守以下约束，但本文不设计 Phase 5.6：

- 新 task 必须提供 task-specific metric contract，并明确 case inclusion、outcome 和 annotation semantics。
- 新 metric 必须拥有独立、可追溯的 metric version；任何会改变计算结果、纳入规则、聚合或 reporting semantics 的变化都必须升级版本。
- Temporal evaluation 必须建立独立的 annotation identity、case semantics 和 evaluation-basis identity；不能复用视觉分类 accuracy v1 的隐含假设。
- Benchmark 继续消费 prepared outputs；新增 benchmark 能力不得调用 Analyzer、模型或媒体读取来绕过输入边界。
- 新增 durable storage、quality gate 或跨任务聚合时，必须另行定义契约、兼容规则和架构决策。

## 12. Final Assessment

基于 Phase 5.5.1–5.5.4 的实现、测试与 ADR-0013/0014 的约束，Phase 5.5 Benchmark Foundation 已形成从 Dataset/Annotation 到 Snapshot、MetricResult、BenchmarkReport，再到经过验证的 revision comparison 的完整架构闭环。其边界清楚地区分了 benchmark、Evaluator、Observation、Evidence 和 EvaluationResult；其 identity 与 comparability 语义也能在证据不足时稳定返回 `NOT_COMPARABLE`，避免猜测性质量结论。

因此，Phase 5.5 foundation 达到架构冻结条件。冻结范围仅覆盖本文第 9 节列出的 benchmark contracts、workflow、validation 和 comparison；任何超出范围的 persistence、quality gate、Temporal、Retrieval 或跨 task 能力，都必须经过独立的后续契约和架构评审。
