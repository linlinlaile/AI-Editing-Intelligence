# ADR-0008：Phase 5.1 Observation Contract

- 状态：Accepted
- 日期：2026-09-12

Observation 使用 `ObservationStatus` 五值枚举：`SUCCESS`、`FAILED`、`UNKNOWN`、`NOT_COVERED`、`PARTIAL`。旧数据库值 `observed`、`failed`、`unknown`、`not_applicable` 保留在原行中，并由 repository 映射为正式枚举；新写入只使用正式值。Observation value 仅允许 JSON 可序列化的标量、数组和对象，引用以结构化 reference 表达；原始模型响应、prompt、Artifact payload 和大型 embedding 向量不属于契约。Evidence 关系与 Phase 0-4 保持不变。
