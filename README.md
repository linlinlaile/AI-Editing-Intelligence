# AI Editing Intelligence

AI Editing Intelligence（暂定名）是一个 local-first 的视频素材理解、检索和镜头推荐系统。它的长期方向是理解剪辑语言并形成 Editing Agent；当前只建设可验证的素材智能层，不替代 Premiere、DaVinci Resolve 或其他 NLE。

## 当前阶段

项目处于 V0.1 设计固化阶段，仓库暂不包含实现代码，也不接入具体 VLM、ASR 或 embedding 模型。首个实现目标是建立稳定的 Semantic Timeline 契约，并完成 frame-accurate ingest 的最小 vertical slice。

V0.1 的最小闭环是：

```text
video → ingest → shot detection → representative frame/window sampling
      → semantic analysis → Semantic Timeline → retrieval
      → experimental Find Next Shot ranking
```

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

建议先实现 **Semantic Timeline Contract v1 + Frame-accurate Ingest Vertical Slice**：建立时间、媒体、Segment、Evidence、Provenance 的契约和 SQLite migration，并用 ffprobe/PyAV 完成可重复的本地 ingest。该任务不涉及模型集成。
