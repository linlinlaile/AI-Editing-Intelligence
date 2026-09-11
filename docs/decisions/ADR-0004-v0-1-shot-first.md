# ADR-0004：V0.1 先做 Shot，不把 Scene/Event 作为前置依赖

- 状态：Accepted
- 日期：2026-09-11

## 背景

Scene 和 Event 是长期目标，但它们需要跨 Shot 的语义聚类、事件边界和评估数据。若先实现，会拖慢素材检索闭环并诱导系统产生没有证据的层级。

## 决策

V0.1 只要求可靠生成 Video、Shot 和 Moment。Semantic Timeline 契约保留 `scene`、`event` 的可扩展 kind，但不要求 V0.1 自动填充。Shot detection、代表帧/时序采样、语义观察、意图检索和实验性下一镜头排序优先。

## 后果

- V0.1 可以在没有 Scene/Event 的情况下交付可用检索。
- `same_event_probability` 等推断必须和未来明确的 Event 归属区分。
- 后续加入 Scene/Event 时，应通过新的 layer/run 和 migration，而不是改变 Shot 的含义。
