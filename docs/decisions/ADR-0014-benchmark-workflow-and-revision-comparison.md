# ADR-0014: Benchmark Workflow and Revision Comparison

- Status: Accepted
- Date: 2026-09-13
- Phase: 5.5.3

## Context

ADR-0013 建立了 Benchmark Dataset、evaluation input boundary、MetricResult 和
BenchmarkReport 的独立契约。Phase 5.5.2 已实现
`vision.classification.accuracy` v1，但当前报告主要描述一次 benchmark
运行，尚未定义如何安全地比较两次分析结果、识别 case 级退化，或处理两次
运行的可评价集合不同的情况。

如果只比较两个总 accuracy，producer、model、config、代码 revision、数据集
内容或 annotation 发生变化时，结果可能被错误解释为模型回归。若把比较结论
写回 Observation，或把它包装成 EvaluationResult，又会破坏 ADR-0011 和
ADR-0013 已建立的语义边界。

## Decision

Phase 5.5.3 定义一个只消费既有 benchmark 输出的 revision comparison workflow。
它不运行 analyzer 或 model，不修改 Observation、Evidence 或 EvaluationResult，
也不新增 Semantic Timeline 存储表。

### 1. Workflow boundary

单次 benchmark workflow 为：

```text
Dataset + Annotation + prepared evaluation input
        ↓
MetricCalculator
        ↓
MetricResult / BenchmarkReport
```

revision comparison workflow 为：

```text
baseline BenchmarkReport + candidate BenchmarkReport
        ↓
comparability validation
        ↓
case alignment and transition calculation
        ↓
BenchmarkComparisonReport
```

`BenchmarkReport` 是一次运行在一个 dataset、annotation、metric 和输入
revision 上的结果。`BenchmarkComparisonReport` 是两个已存在报告之间的派生
比较结果；它不替代任一单次报告，也不成为新的 Observation 或 Evidence。

`MetricResult` 表示一个指标在 benchmark case 集合上的汇总及指标专属值。
`EvaluationResult` 仍表示一个 Evaluator 对单个 Observation 的契约、证据或
其他独立评价结果。Benchmark 不通过实现或扩展 Evaluator 来完成比较。

### 1.1 `BenchmarkComparisonReport` v1 minimum contract

`BenchmarkComparisonReport` v1 至少必须包含：

- `comparison_contract_version`；
- baseline 与 candidate 两侧 `BenchmarkReport` 的稳定身份或引用；
- 两侧 dataset、annotation、metric 和 revision identity（或明确缺失）；
- comparability 状态及不可比原因（如适用）；
- 按稳定 `case_id` 对齐后的 case outcome transition 计数；
- evaluability shift 信息，包括两侧分母及新增、消失、不可评价 case 计数；
- metric delta（仅在本 ADR 的严格可比条件满足时）及其状态；
- 生成时间、comparison producer/version 和可追溯的输入 report identity。

可选的 case ID 和 reason 明细不得替代上述汇总字段。新增字段必须遵守本 ADR
的向后读取和显式版本规则。

### 2. Revision identity

每个 baseline 或 candidate 必须使用结构化 revision identity，而不是从任意
字符串中解析含义。revision identity 至少包含：

- `producer_ref`：产生结果的 adapter/provider 身份；
- `model_ref`：模型名称及模型 revision/hash（如适用）；
- `config_ref`：分析配置或 config hash；
- `code_revision`：分析器实现的代码 revision；
- `analysis_run_ids`：实际提供输入结果的 AnalysisRun 身份；
- 可选的 preprocessing、taxonomy 或其他会影响指标输入的 revision。

缺少必要身份、或一个 revision 内混合无法归属到同一 identity 的输入时，
报告可以保留，但不能生成严格的 revision regression 结论。

revision identity 描述被比较的分析输入来源。它不是 metric version，也不
改变 dataset、annotation 或 metric 的版本语义。

### 3. Comparability rules

严格比较要求 baseline 与 candidate 保持以下评价基础一致：

- dataset identity、dataset version、case membership 和 target/feature 定义；
- annotation identity、annotation version 及其内容；
- metric name、metric version、计算配置、纳入规则和报告规则；
- task、taxonomy 及会改变 expected value 解释的契约版本；
- 用于确定 case 身份和输入 Artifact 的数据内容身份。

以下内容可以不同，但必须分别记录在两侧 revision identity 中：

- producer、model、model revision；
- analyzer code revision；
- analysis config 和 preprocessing revision；
- 产生输入的 analysis run IDs。

仅 dataset/annotation/metric 等版本字符串相同，不足以证明内容相同。应用层
应使用稳定的内容 identity 或 fingerprint；无法证明一致时，比较状态应为
`NOT_COMPARABLE`，而不是猜测兼容。

case 数量相同不代表 case 集合相同。case 必须按稳定 case ID 对齐，不按报告
顺序或 Observation ID 对齐。比较器不得因为某侧缺少 case 而把它当作正确、
错误或未变化。

### 4. Case transition semantics

对同时存在于 baseline 和 candidate、且两侧都有该 metric 的 case，比较器应
保留由对应 `MetricCalculator` 产生的 case 级 outcome。Comparator 只负责读取
两侧 metric output、校验可比性、按 `case_id` 对齐并计算迁移；它不得重新解释
Observation，也不得根据 Observation 的原始字段自行推导正确或错误。对 accuracy
v1，基本 outcome 为：

- `CORRECT`；
- `INCORRECT`；
- `UNEVALUABLE`，并带 metric 定义的 reason；
- `MISSING`，表示该侧没有可供比较的 case 输入或结果。

两侧 outcome 的迁移至少包括：

- `CORRECT → INCORRECT`：candidate regression；
- `INCORRECT → CORRECT`：candidate improvement；
- `CORRECT → UNEVALUABLE`：coverage/evaluability regression，不能等同于语义错误；
- `UNEVALUABLE → CORRECT`：evaluability improvement；
- `UNEVALUABLE → INCORRECT`：只有在 candidate 满足该指标纳入规则时才是新增可评价错误；
- `MISSING` 相关迁移：输入或运行覆盖变化，单独报告，不推断为模型质量变化；
- 相同 outcome：`UNCHANGED`，同时保留 reason 是否发生变化。

`BenchmarkComparisonReport` 应保存迁移计数，并在需要解释时保存稳定、可追溯
的 case IDs 和 reason。它不需要复制完整 Observation 或 Evidence payload。

### 5. Regression interpretation

当两侧可评价 case 集合完全一致时，比较器可以报告正式的 metric delta，例如
`candidate_accuracy - baseline_accuracy`，并结合正确/错误迁移计数解释变化。

当可评价集合不一致时，整体 accuracy 差值只能作为描述性统计，不能单独作为
回归或改进结论。比较报告必须标记 evaluability shift，并分别给出：

- 两侧完整指标及分母；
- 共同可评价 case 子集上的辅助比较（若该指标允许）；
- 新增、消失和转为不可评价的 case 数量及原因；
- 是否具备严格回归判断所需的条件。

可评价比例不是语义准确率、Observation confidence 或 temporal coverage。
比较器不得把缺失输入、`UNKNOWN`、`FAILED` 或 `NOT_APPLICABLE` 静默转换成
正确或错误；具体转换只能由 metric version 定义。

Benchmark comparison 是对固定任务和数据的证据，不是全局模型质量结论，
也不自动触发质量门禁、拒绝 analysis run 或修改 active projection。

### 6. Compatibility rules

单次 `BenchmarkReport` 和比较报告分别拥有显式的 report/comparison contract
version。新增字段应保持旧报告可读取；旧报告没有 revision identity、内容
fingerprint 或 case outcome 时，可以展示历史汇总，但比较器必须返回
`NOT_COMPARABLE` 或缺少证据的明确状态，不得补造身份和迁移。

Metric version 是计算语义的版本。任何会改变纳入规则、正确性定义、聚合方式
或数值结果的变化都必须增加 metric version。仅修复展示层或增加不影响计算的
诊断字段，不得静默改变已有 v1 结果，并应在报告 contract version 或 metadata
中记录。

dataset version、annotation version、metric version 和 revision identity 相互
独立；任一变化都必须在报告中可见。比较器只能在本 ADR 的规则下声明可比，
不能因为两个报告来自同一 evaluation run ID 或具有相同 producer 名称就放宽
数据集和指标约束。

本阶段不要求持久化 BenchmarkReport 或 BenchmarkComparisonReport。若未来需要
SQLite 存储、查询索引、自动质量门禁或历史报告迁移，必须另行更新 ADR 并定义
独立 storage contract。

## Consequences

该决策使 benchmark workflow 能够区分模型语义退化、输入可评价性变化和数据
基础变化。case 迁移为总分变化提供可解释证据，同时保留单次报告作为可复核的
原始 benchmark 结果。

代价是严格比较需要更完整的 revision provenance、case outcome 和内容
fingerprint；缺少这些信息时，系统会返回不可比较，而不是给出看似精确的
回归结论。该限制是有意的，符合 evidence-first 和可重算要求。

## Non-goals

本 ADR 不定义：

- 新的语义指标或 retrieval/temporal/editorial benchmark；
- analyzer、model 或媒体重跑；
- 人工标注工具；
- EvaluationResult 的扩展、持久化或替代；
- 自动质量门禁、发布阻断或模型选择策略；
- 通用的跨 task 总质量分数。
