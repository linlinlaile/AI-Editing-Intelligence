# Shot-level Visual Observation Aggregation

## Phase 5.4 Step 1 scope

依据 [ADR-0012](../decisions/ADR-0012-shot-level-visual-observation-aggregation.md)，本步只建立 `src/aei/domain/aggregation.py` 中的纯数据契约。没有模型调用、aggregation algorithm、SemanticVisionAnalyzer、存储适配或 migration；已有 Analyzer、Observation 和 Evidence schema 不变。

## Input contract

`AggregationInput` 包含 `shot`（TemporalSegment）、`samples`（预期 Sample 集合）、`artifact_observations`、`evidences` 和显式 `missing_inputs`。快照全部由应用层提供，不带 repository、SQLite、模型客户端或媒体 payload。空预期集合可以表示没有采样输入。

`MissingInput` 记录 Sample ID、可选的 Artifact ID 集合、原因和说明。原因分别为 `artifact_missing`、`observation_missing`、`failed`、`unknown`、`not_covered`；这是输入原因，不是新增 Observation 状态。

构造检查 Shot 类型、唯一记录 ID、Sample 归属、Artifact classification target、Evidence 引用和上游 run 一致性。保留重复源帧对应的不同 Sample，既不去重也不选取结果。模型兼容性、完整 source grounding、缺失项发现、源帧去重和统计留给后续步骤。

## Feature value v1.0

`SampledClassificationSummary` 的 feature 是 `vision.sampled_classification_summary`。value 使用以下封闭结构：

| 字段 | 含义 |
|---|---|
| `schema_version` | 固定 `1.0`，独立于数据库和 taxonomy 版本 |
| `scope` | 固定 `sampled_frames` |
| `taxonomy` / `taxonomy_version` | 调用方明确提供的标签体系及其版本，不从模型名称猜测 |
| `analyzed_sample_count` | 已分析的唯一源采样点数，由调用方提供 |
| `class_distribution` | class ID、label、支持数量及代表这些唯一源采样点的 Sample IDs |
| `disagreements` | 存在多类别时列出全部竞争 class IDs；一致或无结果时为空 |
| `missing_inputs` | 显式缺失、失败、未知或未覆盖记录 |

每个唯一源采样点采用一个代表 Sample ID，不能重复计票。契约只校验调用方给出的数量与支持 ID 一致、类别唯一及分歧清单完整，不计算类别分布、选择代表 Sample 或推导状态。

value 不表示 full Shot truth、temporal coverage 或 semantic confidence。没有概率字段或时间占比字段。`to_value()` 仅转换成现有 Observation value 可接受的 JSON 字典和数组，不产生 Observation。

## Result drafts v1.0

`AggregationResult` 包含：

- `observation`：`ShotObservationDraft`，固定 target type 为 `segment`，target ID 指向 Shot；携带 feature value 和调用方提供的现有 ObservationStatus。`coverage`、`confidence`、`confidence_kind` 固定为 `None`。
- `evidence`：`AggregationEvidenceDraft`，记录显式的 `ObservationSource` 列表和缺失输入。每条 source 包含上游 Observation/Evidence/run、Sample/Artifact ID、Artifact URI/hash 和原始 TimePoint。
- `metadata`：`AggregationMetadata`，记录 producer、聚合规则名/版本、配置 hash、上游 run IDs、预期和已分析唯一采样点数。

三个对象共同组成一个草稿包；Evidence 与 Observation 的关联由此包明确表达。metadata 是本次新 Evidence 将要携带的聚合规则与计数信息，不是 EvaluationResult。sampling completeness 所需计数只在 metadata 中提供，本步不计算比例；零分母不解释为完成率 1。

草稿不分配正式 Observation/Evidence ID 或聚合 run ID，也不创建 AnalysisRun。后续应用层必须将草稿包物化为同一个新聚合 run 的 Observation 和新 Evidence，把 metadata/source 清单写入既有 Evidence 支持的结构化字段，并将 parent run IDs 写入 AnalysisRun。上游 Evidence IDs 是 provenance，不能直接用作新 Observation 的 evidence_ids。

无来源的空摘要允许存在，以表达尚未覆盖或失败；仍须提供缺失说明或预期/已分析计数。仅有草稿不代表已通过现实语义验证或已完成持久化。

## Serialization and validation

所有对象使用 frozen dataclass 和 tuple 集合，遵循既有 domain 对象风格；现有 Observation/Evidence 内部 JSON 字典不新增深度冻结语义。标准 `dataclasses.asdict` 加 `json.dumps(..., allow_nan=False)` 可序列化整个输入或结果；枚举按字符串、tuple 按 JSON 数组输出，PTS 和 rational timebase 保持整数。此步不新增通用反序列化框架。

固定 input/result JSON golden fixture 和契约测试覆盖无输入、缺失/失败、类别分歧、非法引用、run 不一致及序列化边界。测试使用 [ENVIRONMENT.md](../development/ENVIRONMENT.md) 中的项目解释器；现有集成测试作为回归检查，不新增媒体分析能力。
