# Changelog

本文件记录 AI Editing Intelligence 的能力演进、已冻结的架构约束和后续路线。内容以已提交的 git history、产品定义、架构文档和 ADR 为准；未提交的工作不会被视为已发布能力。

## [Unreleased]

当前工作区正在继续加固 Shot Boundary Detection 的契约验证，重点包括更多媒体探针 fixture，以及对 CFR、VFR、非零起始 PTS 和 B-frame 呈现顺序的排序、非重叠和往返一致性检查。这部分尚未形成新的发布里程碑。

下一阶段计划完成代表性帧与短时序窗口的 Sampling pipeline，使 Shot 能够产生带 source 坐标、用途和选择理由的 Sample，并为后续分析器消费。随后再接入不依赖具体模型的语义分析 port；VLM、ASR、embedding 和云服务仍不属于当前阶段的已交付内容。

---

## [v0.1.0-alpha]

首个 alpha milestone，基于截至 `e8ea1f9` 的提交历史。项目从契约设计进入了可运行的本地数据与 Shot 检测 vertical slice，但仍处于 V0.1 早期阶段。

### Added

- 建立 Python 模块化单体的基础结构，分离 `domain`、`adapters` 和 `storage`，并保留面向未来 application/ports/pipeline 的边界。
- 固化 Semantic Timeline Contract v1 的基础对象：`MediaAsset`、`MediaStream`、`TimelineLayer`、`TemporalSegment`、`AnalysisRun`、`Sample`、`Evidence` 和 `Observation`。
- 完成 frame-accurate ingest 的最小实现：通过 ffprobe 或可选 PyAV 适配器读取资产指纹、stream 元数据、PTS、rational timebase、帧率元数据、旋转、宽高比和色彩信息。
- 建立 SQLite 权威存储与迁移，保存媒体、时间轴层、segment、run、sample、evidence 和 observation；repository adapter 负责把纯 Python domain value objects 映射到 SQLite。
- 增加 evidence-first provenance：分析结果关联 `AnalysisRun`、producer、evidence、confidence 和 coverage，并区分 `observed`、`unknown`、`not_applicable` 与 `failed`。
- 完成 Shot Boundary Detection vertical slice：`ShotDetector` 协议只返回整数 PTS/帧边界，PySceneDetect 依赖留在 adapter；检测结果写入版本化 `shot` layer，并为每个 segment 保留 detector evidence 和 provenance。

### Changed

- 将时间模型从仅依赖显示秒数的边界提升为 `stream_id + integer PTS + rational timebase`，并保留可选 presentation frame index；`TimeSpan` 使用起始包含、结束不包含。
- 将 schema、domain model 与 infrastructure 解耦：ffprobe 输出先经过 adapter 转换，SQLite 只存在于存储边界，模型或索引实现不能进入领域契约。
- 将时间轴更新定义为可重算的追加模型：新的 detector 或 analysis run 产生新的 layer/run，不静默覆盖旧结果；当前视图由显式选择得到。
- 明确事实与编辑判断的分层：层级关系、描述性观察/推断关系和带 edit intent 的 `EditorialAssessment` 不共享同一语义字段。
- 将 embedding、缩略图、光流、全文索引和向量索引定义为可删除、可从 SQLite 权威数据重建的派生数据。

### Tests

- 已提交的测试模块覆盖 Contract v1、SQLite migration/repository、JSON golden fixture、evidence/observation 约束和 Shot detection vertical slice，共 11 个测试函数。
- 已提交的契约 fixture 覆盖 VFR 与非零起始 PTS；Shot detection 测试验证 source timebase、segment 边界和 provenance 保留。
- 架构约束要求后续媒体测试继续覆盖 CFR、VFR、非零起始 PTS、B-frame、旋转/色彩元数据以及缺失或读取失败的 stream；这些是持续验证要求，不表示当前都已实现。

### Architecture Decisions

以下 ADR 已标记为 Accepted，并构成当前冻结的长期约束：

- 本地优先的 Python 模块化单体；远程推理只能作为用户显式选择的 provider（ADR-0001）。
- 源 stream 的整数 PTS 与 rational timebase 是 canonical 时间真值，float seconds 只用于显示或查询输入（ADR-0002、ADR-0006）。
- `HierarchyLink`、`DescriptiveObservation`/`ObservedRelation` 与 `EditorialAssessment` 分层；`good_next_shot` 不能成为无上下文的永久事实（ADR-0003）。
- V0.1 以 Video、Shot、Moment 为可靠基础，Scene/Event 只保留可扩展契约，不作为自动分析前置依赖（ADR-0004）。
- SQLite 是权威结构化存储，向量和其他索引属于可重建派生层（ADR-0005）。
- Semantic Timeline Contract v1 使用纯 Python domain objects 表达媒体、时间轴层和时间段；`shot`、`moment` 通过 `TemporalSegment.kind` 表达，未来可扩展 `scene`/`event`（ADR-0007）。

### Next

- 完成 representative frame、temporal window 和 audio window 的 Sampling pipeline，并记录精确 source reference、用途、选择理由和 artifact 引用。
- 在固定 fixture 和评估集上继续验证 frame-accurate ingest 与 Shot boundary 行为，再扩大到可恢复、幂等的本地 stage runner。
- 定义并实现第一批分析器 ports，先保存带证据的描述性观察；具体 VLM、ASR、embedding provider 必须继续停留在 adapter 层。
- 在有稳定观察数据和 benchmark 后，再实现结构化意图检索和实验性的 Find Next Shot ranking；Scene/Event 自动推理、完整 NLE 和自动成片仍不在 V0.1 范围内。

[Unreleased]: https://github.com/linlinlaile/AI-Editing-Intelligence/compare/v0.1.0-alpha...HEAD

