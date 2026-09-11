# ADR-0005：权威 SQLite，派生索引可重建

- 状态：Accepted
- 日期：2026-09-11

## 背景

Semantic Timeline 需要长期稳定、可迁移、可审计；向量索引和全文索引会随着模型、字段和规模变化。让向量库成为事实源会把可替换模型和基础设施写进领域契约。

## 决策

SQLite 保存媒体、时间层、样本、observations、evidence、runs 和关系等权威数据。embedding、缩略图、光流、全文索引、向量索引和聚合 projection 都是派生数据，必须记录来源并可从权威数据重建。

首个检索实现可使用 NumPy exact cosine；只有 benchmark 显示规模或延迟需要时，再引入 LanceDB 或其他索引 adapter。

## 后果

- 更容易做模型替换、迁移、审计和失败重跑。
- 首版不需要承担额外向量数据库服务的运维复杂度。
- 必须为 projection 和 index 编写重建命令与一致性测试。
