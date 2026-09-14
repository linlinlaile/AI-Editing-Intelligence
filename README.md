# AI Editing Intelligence

AI Editing Intelligence（暂定名）是一个 local-first 的视频素材理解、检索和镜头推荐系统。它的长期方向是理解剪辑语言并形成 Editing Agent；当前只建设可验证的素材智能层，不替代 Premiere、DaVinci Resolve 或其他 NLE。

## 当前阶段

项目已完成 V0.1 的 **Phase 5.5.3 Benchmark Revision Comparison**，仓库已包含 Semantic Timeline、Observation、Evidence、Analyzer、评价和 benchmark vertical slice 的实现与契约。当前 benchmark 只覆盖已定义的视觉分类 accuracy v1；不接入云服务，也不把具体模型写入领域契约。

Benchmark Revision Comparison 支持两个既有 `BenchmarkReport` 的比较，通过 `EvaluationBasisIdentity` 表达固定评价基础、`RevisionIdentity` 记录被比较的分析来源，并按 `CaseOutcome` 进行 case transition analysis，为 revision regression comparison 提供基础。不可比报告的迁移统计仅作为诊断信息；当前未实现 benchmark persistence 或自动 quality gate。实现范围与限制见 [Phase 5.5.3 Summary](docs/phases/PHASE_5_5_3_SUMMARY.md)。

V0.1 的最小闭环是：

```text
video → ingest → shot detection → representative frame/window sampling
      → semantic analysis → Semantic Timeline → experimental retrieval foundation
      → experimental Find Next Shot ranking
```

产品化路线的第一阶段定位是 **AI Video Asset Intelligence**：帮助创作者导入、理解、组织和检索视频素材，逐步建立个人视频知识库。长期方向是在既有 Video Understanding 基础上形成 Semantic Video Memory、Editing Intelligence、AI Editing Assistant，最终走向 AI Editing Agent。详见 [Vision and Roadmap](docs/product/VISION_AND_ROADMAP.md) 与 [Long-term Principles](docs/product/PRINCIPLES.md)。

## V0.1 要解决的问题

目标用户是拥有大量原始素材的独立剪辑师、小型创作团队，以及旅行、纪录片、活动、婚礼和品牌视频创作者。

两个入口：

1. **Search by Intent**：根据“湖边夕阳、无人、远景、缓慢横移、平静、适合结尾”等意图寻找镜头。
2. **Search by Context / Find Next Shot**：给定当前 Shot，寻找若干可接镜头，并说明同一事件、动作、运动方向、景别、视线、情绪或视觉匹配等理由。

## 重要边界

- 原始视频默认只在本地处理；远程模型必须显式选择。
- Shot 是 V0.1 的主要结构单元；Scene/Event 只进入契约，不作为 V0.1 的自动分析前置条件。
- 事实性观察与编辑判断必须分开存储。
- 所有重要判断都应尽量带 confidence、evidence、source/model 和 analysis run。
- 时间轴的 canonical truth 是源视频 PTS + rational timebase，不是 float seconds。
- “适合接在后面”必须带 edit intent 和可解释的分项评分，不是永久客观标签。

## 文档入口

- [Agent 开发约束](AGENTS.md)
- [V0.1 产品范围](docs/product/v0.1.md)
- [架构总览](docs/architecture/overview.md)
- [Semantic Timeline 契约](docs/architecture/semantic-timeline.md)
- [架构决策记录](docs/decisions/)

开发前应先读 `AGENTS.md`，再按任务阅读上述相关文档。

## 当前不做

V0.1 不开发完整 NLE、复杂 timeline editor、自动字幕编辑器、AI 视频/图片/音乐生成、Motion Graphics、完整自动成片、调色、团队协作和手机端。

## 下一步

下一步应在既有契约和 benchmark 基线上继续扩展可验证能力；新增分析维度必须保留证据、运行 provenance 和可重算边界，并配套固定 fixture 或适用的 benchmark 评估。当前阶段不把 Scene/Event 推理、完整 NLE 或自动成片提前纳入实现范围。
