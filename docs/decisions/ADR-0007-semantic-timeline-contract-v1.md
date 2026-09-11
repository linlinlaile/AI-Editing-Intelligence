# ADR-0007：Semantic Timeline Contract v1 schema

- 状态：Accepted
- 日期：2026-09-11

v1 只固化媒体身份、媒体流、时间轴层和时间段四类可重算基础对象，并将未来的 observation/evidence/run 保留为独立扩展表。领域对象使用纯 Python 值对象，SQLite 仅在 adapter/storage 层实现持久化；ffprobe 输出作为输入适配数据，不直接成为领域模型。`shot` 与 `moment` 通过 `TemporalSegment.kind` 表达，`scene`/`event` 可在未来扩展而不破坏已有契约。
