# ADR-0012: Shot-level Visual Observation Aggregation

- Status: Accepted
- Date: 2026-09-13
- Phase: 5.4，第一阶段

## Context

当前系统已经支持：

```text
Artifact
  ↓
VisionAnalyzer
  ↓
Artifact Observation + Evidence
```

单 Artifact Observation 只表达一个派生图像输入的分类结果，无法表达同一 Shot 内多个采样点的类别分布、分歧及缺失情况。需要在既有理解层上增加：

```text
Artifact Observations + Evidence
  ↓
Aggregation
  ↓
Shot-level Observation + new Evidence
```

本决策延续 [ADR-0008](ADR-0008-observation-contract-phase5.md) 的 Observation contract、[ADR-0009](ADR-0009-analyzer-interface-phase5-2.md) 的 Analyzer boundary、[ADR-0010](ADR-0010-first-vision-classifier.md) 的单图像分类边界及 [ADR-0011](ADR-0011-observation-evaluation-phase5-3-2.md) 的独立 Evaluation boundary。

## Decision

### 1. Shot-level Observation 是新增 Observation，不修改已有 Observation

Artifact Observation 的 target 保持为 artifact；Shot Observation 的语义 target 为 shot。按现有 Semantic Timeline 表示，后者使用 `target_type="segment"`，`target_id` 指向 `TemporalSegment(kind="shot")`，不引入另一套 Shot 实体。

聚合创建新的 Observation 和独立的聚合 AnalysisRun，保留已有 Artifact Observation、Evidence 和运行历史。重新聚合追加结果，不覆盖历史结果。

### 2. 第一阶段目标

第一阶段定义为 **Shot-level visual observation aggregation**：汇总一个 Shot 的已分析采样帧所提供的视觉分类观察。

结果必须明确其适用范围是已分析采样帧。它不表示 full video understanding、action understanding 或 scene reasoning；分类分布也不直接升级为对象存在、持续动作或全 Shot 的语义事实。

### 3. 输入边界

Aggregation 只消费应用层准备的输入快照：

- Shot snapshot：目标 Shot、所属版本及源时间范围。
- Sample snapshot：预期采样集合、Shot 归属和精确源位置。
- Artifact Observation snapshot：已有分类观察及其处理状态。
- Evidence snapshot：观察所引用的证据及上游来源信息。

应用层必须保留预期输入清单和缺失、失败记录，不能只提交成功结果而隐藏未处理输入。Artifact 身份、hash 和 source point 通过关联证据提供。

Aggregation 不访问 repository、SQLite 或 model，不读取媒体 payload，也不重新执行视觉推理。应用层负责快照准备、运行管理、结果验证和持久化。本决策不修改现有 `AnalysisInput`、`AnalyzerContext` 或 Analyzer port。

### 4. Aggregation 原则

聚合支持同一 Shot 的多 Artifact 输入，并记录类别分布、分歧、缺失输入和 provenance。

- 验证 Sample、Artifact Observation 和 Evidence 的关联，以及 asset、stream、源时间和 Shot 归属。
- 对同一源呈现帧的重复采样或不同编码 Artifact 去重，避免重复计票；不同时间点即使图像 hash 相同也不能仅按 hash 合并。
- 第一阶段只聚合兼容的 taxonomy、模型和预处理版本，采用唯一采样点的等权分类统计。
- 保留多类别和平票，不强制将分歧压缩成一个 Shot 标签。
- 缺失、失败、未知和没有检测到不能互相替代；状态继续使用 ADR-0008 的现有枚举，不新增状态。
- 聚合规则版本、配置及输入来源必须可追溯，以支持确定性重算。

禁止把单帧结果外推整个 Shot、把 softmax score 直接作为 Shot confidence，或把采样完成率作为时间 coverage。对 top-1 score 求平均也不构成经过校准的 Shot confidence。

### 5. Coverage

明确区分三个量：

| 概念 | 含义 | 第一阶段处理 |
|---|---|---|
| sampling completeness | 有效唯一采样点数 / 预期唯一采样点数 | 在聚合 Evidence 中记录计数和比例；分母为零时不定义比例 |
| temporal coverage | 有效分析时间区间覆盖 Shot 时间范围的比例 | 当前只有点采样，Observation 的 `coverage` 保持 `None` |
| semantic confidence | 对语义结论正确性的可信程度 | 不由采样完成率、类别支持比例或 softmax 平均值替代；第一阶段 Shot `confidence` 保持 `None` |

当前 frame Sample 的零长度时间范围和 Artifact 的 source point 只表示采样位置，不能推导相邻采样点之间已被分析。即使全部预期采样均成功，也不能声明完整时间覆盖或整个 Shot 不存在某类内容。

未来若存在真实分析窗口，temporal coverage 应基于这些区间与 Shot 的交集求并集后计算，保留空隙并避免重复计时。时间依据始终使用源 stream 的整数 PTS 和 rational timebase，不使用 nominal FPS 补造区间。

### 6. Evidence

Shot-level Observation 必须产生并引用新的 Evidence，表达使用了哪些 Artifact Observation、上游来源和聚合规则。

新 Evidence 使用既有 contract，通过现有来源字段、`metadata` 和必要的 `numeric_measurement` 记录：

- 上游 Observation、Evidence、Artifact 和 AnalysisRun 标识。
- 可复核的 Artifact URI/hash 和源 TimePoint。
- 聚合规则版本、配置、类别支持统计及缺失输入情况。

不新增 Evidence 字段，不把仅有自然语言描述或孤立 ID 的记录当作完整来源证据，也不把首尾采样点之间的范围伪装成连续分析窗口。

新 Evidence 与 Shot Observation 属于同一个聚合 run，并随结果一起返回。旧 run 的 Evidence 不直接作为新 Observation 的 `evidence_ids`；上游引用保存在新 Evidence 中，聚合 AnalysisRun 通过 `parent_run_ids` 记录上游运行。原始 Evidence 不修改，新 Evidence 不宣称重新执行过模型。

### 7. Boundary

职责保持为：

```text
VisionAnalyzer:    Artifact → Artifact Observation + Evidence
Shot aggregation: Artifact Observations → Shot Observation + new Evidence
Evaluator:        Observation + Evidence → EvaluationResult
```

Aggregation 是独立、可测试的逻辑模块，不是新的模型、数据库服务或通用聚合平台。现有 VisionAnalyzer 继续遵守单 Artifact 输入限制。

Evaluator 独立评价结果，不参与生成或改写聚合 Observation。契约与 grounding 检查通过不表示现实语义正确；evaluation run 与分析、聚合 run 分离，调用方显式提供独立标识。

### 8. Storage

Phase 5.4 第一阶段不新增 migration 或 SQLite table，不修改 Artifact、Observation schema 或 Evidence schema。

结果复用既有 AnalysisRun、Observation、Evidence 和 `observation_evidence` 存储。新增 feature 的结构化 value 与聚合 Evidence 内容必须有明确版本和验证规则，不承载 raw model response、payload 或无约束语义转储。

EvaluationResult 的独立返回和非持久化边界保持 ADR-0011 的决策。

## Non Goals

- VLM
- caption
- action recognition
- Scene/Event
- tracking
- editing recommendation
- retrieval
