# Phase 5.4 Shot-level Visual Observation Aggregation Summary

## 1. Phase 5.4 目标

Phase 5.4 在既有 Artifact Observation 和 Evidence 之上，建立第一阶段的 Shot-level visual observation aggregation 能力：将同一 Shot 内已分析采样帧的分类观察汇总为新的 Shot Observation，并生成可追溯的 Aggregation Evidence。

本阶段不引入新的模型、存储服务或评价平台，也不把采样结果外推为完整 Shot 的现实语义事实。聚合结果只描述已分析采样帧的分类分布、分歧和输入缺失情况。

依据 [ADR-0012](../decisions/ADR-0012-shot-level-visual-observation-aggregation.md)，聚合结果追加到既有 Semantic Timeline，保留上游 Observation、Evidence 和 AnalysisRun 历史。

## 2. Aggregation 架构链路

```text
Shot snapshot + Sample snapshot
  + Artifact Observation snapshot + Evidence snapshot
        ↓
  pure Shot aggregation logic
        ↓
  Shot Observation draft + Aggregation Evidence draft
        ↓
  application materialization
        ↓
  new Shot Observation + new Aggregation Evidence
        ↓
  ContractEvaluator / EvidenceGroundingEvaluator
        ↓
  EvaluationResult
```

应用层准备输入快照、运行 Analyzer、处理缺失项并负责持久化；domain aggregation 不访问 repository、SQLite、媒体 payload 或模型。Evaluator 只消费应用层提供的 Observation、Evidence 和 AnalysisRun metadata 快照。

## 3. Step 1-5 实际完成内容

### Step 1：Aggregation Contract

新增并固化聚合输入、输出和 provenance 契约：

- `AggregationInput`
- `MissingInput` / `MissingInputReason`
- `SampledClassificationSummary`
- `ShotObservationDraft`
- `ObservationSource`
- `AggregationEvidenceDraft`
- `AggregationMetadata`
- `AggregationResult`

契约保留预期采样集合、已分析数量、类别分布、分歧和显式缺失记录，并使用源 PTS、rational timebase 和 presentation frame index 表达采样位置。

### Step 2：Pure Aggregation Logic

实现确定性的 `aggregate_shot_observations()`：

- 验证 Shot、Sample、Artifact Observation 和 Evidence 的关联。
- 检查 taxonomy、producer、model/preprocess 版本兼容性。
- 按唯一源呈现点等权统计类别分布。
- 对重复源呈现点去重；不同时间点不会因 artifact hash 相同而合并。
- 保留多类别分歧和平票。
- 区分成功、部分、失败、未知和未覆盖输入。
- 保持 `confidence=None`、`coverage=None`，不把采样完成率或 top-1 分数当作语义置信度。

### Step 3：Shot Observation + Evidence Generation

实现 `generate_shot_observation_evidence()`，将聚合草稿物化为：

- `target_type="segment"`、`target_id` 指向 Shot 的新 Observation。
- feature `vision.sampled_classification_summary`。
- 同一聚合 run 下的新 Evidence。
- 包含上游 Observation、Evidence、run、Artifact URI/hash、source point、分类统计、缺失输入和聚合规则版本的 metadata。

上游 Evidence 不被复用为新 Observation 的直接 `evidence_ids`，而是作为新 Evidence 中的 provenance 记录。

### Step 4：Application Orchestration

新增 `ShotObservationAggregationUseCase`：

- 以 Sample 作为预期输入集合。
- 调用现有单 Artifact Vision Analyzer。
- 将单个输入失败转换为显式 `MissingInput`，不阻断整个 Shot。
- 调用纯聚合逻辑并物化新 Observation/Evidence。

### Step 4.2：Persistence Integration

新增 `execute_and_persist()`：

- 写入调用方提供的聚合 `AnalysisRun`。
- 持久化新 Aggregation Evidence 和 Shot Observation。
- 保留旧 run 和上游结果，不覆盖历史。
- 复用既有 Observation、Evidence 和 `observation_evidence` 存储，没有新增 migration 或表。

### Step 5：Evaluation Integration

新增评价集成测试，使用真实 aggregation pipeline 生成 Shot Observation 和 Aggregation Evidence，再构造 `EvaluationInput`：

- `ContractEvaluator` 对合法 Shot Observation 返回 PASS。
- 缺少 `producer_ref`、非法 status 或非法 value 返回 FAIL。
- `EvidenceGroundingEvaluator` 对 direct Aggregation Evidence、run consistency 和现有 provenance 返回 PASS。
- 缺少 direct Evidence reference 或 run 不一致返回 FAIL。
- direct Evidence 缺少 source material 返回 `NOT_EVALUABLE`。

GroundingEvaluator 只检查 Observation 直接引用的 Evidence，不递归验证 Aggregation Evidence metadata 中的 upstream lineage。评价结果保持独立，不写回 Observation 或 Evidence。

## 4. Shot Observation 与 Artifact Observation 的边界

Artifact Observation 描述单个 Artifact 的分类结果，target 是 Artifact，通常由 Vision Analyzer 直接产生。

Shot Observation 描述同一 Shot 的已分析采样帧摘要，target 是 `TemporalSegment(kind="shot")`，使用 `target_type="segment"`。它表达采样帧的类别分布、分歧、分析数量和缺失输入，不等同于整个视频片段的 full-video understanding，也不直接断言对象在整个 Shot 中存在或持续发生。

Shot Observation 不覆盖 Artifact Observation 的历史结果；每次重新聚合都创建新的聚合 run 和结果。

## 5. Aggregation Evidence 设计

Aggregation Evidence 复用既有 Evidence contract，不新增字段。它通过现有 numeric measurement 和 metadata 保存：

- 聚合规则名、版本和 config hash。
- 上游 Observation、Evidence 和 AnalysisRun IDs。
- Artifact URI、hash、Sample ID 和源 TimePoint。
- 预期/已分析采样数量和类别统计。
- 多类别分歧。
- 缺失、失败、未知或未覆盖输入。

Evidence 仍必须包含可支持的直接来源引用。采样点之间没有真实分析窗口，因此不能把首尾采样点伪装成连续 temporal coverage。`sampling completeness`、`temporal coverage` 和 `semantic confidence` 保持分离。

## 6. Evaluation Integration 设计

评价层继续遵循 [ADR-0011](../decisions/ADR-0011-observation-evaluation-phase5-3-2.md)：

- `ContractEvaluator` 只检查 Observation 结构、状态、producer 和 value 的可序列化约束。
- `EvidenceGroundingEvaluator` 只检查 Observation 与 direct Evidence 的引用、run consistency 和可追溯来源。
- `EvaluationResult` 是独立结果，使用独立的 evaluation run ID。
- `PASS` 表示契约和直接证据关联检查通过，不表示分类语义或现实世界正确性。
- `FAIL` 与 `NOT_EVALUABLE` 保持区分。

本阶段不实现 benchmark、人工标注、语义准确率、质量门禁或评价结果持久化。

## 7. 测试结果

使用 [ENVIRONMENT.md](../development/ENVIRONMENT.md) 规定的项目解释器运行：

```text
70 passed, 1 skipped
```

跳过项是需要显式设置 `RUN_REAL_MODEL=1` 并提供本地权重的真实 ResNet18 测试。新增 Step 5 测试专测结果为：

```text
5 passed
```

覆盖了聚合输出的 ContractEvaluator 和 EvidenceGroundingEvaluator 集成行为，同时保留已有聚合 contract、evidence generation、orchestration、persistence 和媒体回归测试。

## 8. 当前限制

- 只聚合已分析的采样帧，不推导完整 Shot 的语义真值。
- 当前是分类分布摘要，不包含 action recognition、tracking、caption、VLM 或 Scene/Event 推理。
- 点采样不能计算真实 temporal coverage；Shot Observation 的 `coverage` 保持 `None`。
- Shot Observation 的 `confidence` 保持 `None`，不把采样完成率、类别支持比例或 softmax 平均值当作校准置信度。
- Evaluator 不判断现实语义正确性，也不执行 benchmark 或人工标注比较。
- EvaluationResult 尚未持久化；未来如需存储必须新增独立 ADR。
- GroundingEvaluator 当前只检查 direct Evidence，不递归验证 upstream lineage。
- 真实外部 PySceneDetect adapter 和真实模型推理不属于本阶段完整验证范围。

## 9. Phase 5.5 入口

Phase 5.4 的可交付范围在 Shot-level visual observation aggregation、其证据生成、应用编排、持久化接入和 Evaluation Layer 验证处收束。

Phase 5.5 若启动，应以新的阶段目标和 ADR 明确入口。可能的后续方向包括更丰富的 observation 类型、真实分析窗口与 temporal coverage、benchmark/标注流程或下游检索使用，但这些不属于 Phase 5.4，也未在本阶段预先实现。
