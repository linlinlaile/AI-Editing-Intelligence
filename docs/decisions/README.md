# Architecture Decision Records

这里记录会影响长期方向、数据契约或可替换性的决策。普通实现细节不需要新增 ADR；如果实现与现有 ADR 冲突，应先更新决策并说明迁移影响。

当前已冻结的决策：

- [ADR-0001：模块化单体和本地优先](ADR-0001-modular-monolith-local-first.md)
- [ADR-0002：PTS 和 rational timebase 是时间真值](ADR-0002-frame-accurate-time.md)
- [ADR-0003：Semantic Timeline 的事实/判断分层](ADR-0003-semantic-timeline-separation.md)
- [ADR-0004：V0.1 先做 Shot，不把 Scene/Event 作为前置依赖](ADR-0004-v0-1-shot-first.md)
- [ADR-0005：权威 SQLite，派生索引可重建](ADR-0005-authoritative-store-and-derived-index.md)

## 尚未决定的问题

这些问题会影响实现参数或后续优化，但不阻塞第一个 ingest vertical slice：

- 首批支持的硬件档位、GPU 可用性和可接受的首次分析时长
- 真实素材的编码、VFR 比例、平均时长和项目规模上限
- 是否要求完全离线，还是允许用户显式启用远程模型
- 第一批 benchmark 的素材来源、标注流程和许可证
- 默认的本地图文 embedding、VLM、音频分类器和 ASR provider
- 未来优先支持的 NLE 或交换格式（Premiere、Resolve、OTIO 等）
