# VibeCut Phase 5.1 总结

## 1. Phase Overview

Phase 5.1 的目标是建立 Observation Contract，使分析结果形成稳定、可追溯、可验证的理解层：

```text
Artifact
   ↓
Observation
   ↓
Evidence
```

Observation 必须能够回到产生它的 source、Artifact 或 frame，并通过 Evidence 保留可复核的证明关系。该结构为后续可重算、可审计的 AI 分析提供统一边界。

本阶段包含：

- **Phase 5.1：Observation Contract**
- **Phase 5.1.1：Shot Detection Observation Cleanup**

## 2. Starting Point

Phase 0-4 已完成以下基础链路：

```text
Video
  ↓
Media Foundation
  ↓
Semantic Timeline
  ↓
Shot
  ↓
Sample
  ↓
Artifact
  ↓
Evidence
```

这些阶段建立了整数 PTS、rational timebase、presentation frame index、Shot temporal segment、Sample 输入点、Artifact 派生媒体和 Evidence 证据关系。

Phase 5.1 不修改以下既有契约：

- `MediaAsset`
- `MediaStream`
- Rational Time Model
- `Sample`
- `Artifact`

Observation 只在 Artifact 之后表达分析理解，不改变媒体基础设施或已有 Artifact payload/provenance 语义。

## 3. Observation Contract

最终 Observation contract 包含以下字段：

| 字段 | 含义 |
|---|---|
| `id` | Observation 唯一标识 |
| `run_id` | 产生该结果的 `AnalysisRun` |
| `target_type` | 被观察对象类型 |
| `target_id` | 被观察对象标识 |
| `feature` | 观察特征名称 |
| `value` | 受控的结构化观察值 |
| `value_status` | 观察值状态 |
| `confidence` | 置信度数值 |
| `confidence_kind` | 置信度的语义或校准类型 |
| `coverage` | 分析覆盖程度 |
| `evidence_ids` | 支撑该观察的 Evidence 标识列表 |
| `producer_ref` | 产生结果的 analyzer/model/producer 引用 |

Observation 是描述性理解结果；它不等同于原始模型输出，也不取代 Artifact 或 Evidence。

## 4. ObservationStatus

正式状态枚举为：

- `SUCCESS`
- `FAILED`
- `UNKNOWN`
- `NOT_COVERED`
- `PARTIAL`

旧数据库状态继续兼容映射：

```text
observed       → SUCCESS
failed         → FAILED
unknown        → UNKNOWN
not_applicable → NOT_COVERED
```

历史数据保留原始状态值，并由 repository 映射为正式枚举。新写入只使用正式状态。不会删除旧 Observation，也不会用新结果静默覆盖历史分析运行。

## 5. Controlled Observation Value

`value` 只允许可控、可序列化的结构化数据：

- scalar
- structured object
- reference

以下内容不属于 Observation value contract：

- raw model response
- prompt
- Artifact payload
- large embedding vector
- 非有限数值（`NaN`、正负无穷）

## 6. Storage Changes

SQLite schema version 从 **3** 升级到 **4**。

本次存储变化包括：

- 增加 Observation 查询能力。
- 增加按 subject（`target_type` / `target_id`）查询所需索引。
- 保留既有 `observation_evidence` 关系表及其 Evidence 关联语义。

本阶段没有删除历史数据、删除旧 Observation 状态或新建另一套 semantic storage。

## 7. Phase 5.1.1 Shot Detection Observation Cleanup

实施过程中发现，ShotDetector 曾产生：

```text
shot_boundary_detected Observation
```

清理后，Shot Detection 链路固定为：

```text
ShotDetector
   ↓
TemporalSegment(kind="shot")
   ↓
Evidence
```

ShotDetector 负责 Shot 边界、temporal structure、detector provenance 和检测 Evidence，不再直接生成 Observation。原因是 Shot Detection 属于 temporal structure，不属于 semantic understanding。历史上已经存在的 Observation 仍可读取；新的 Shot Detection run 不再创建该 semantic Observation。

## 8. Tests

Phase 5.1 的最终验收基线为：

```text
31 passed
```

覆盖 Observation status、persistence、Evidence relation、legacy compatibility 和 Shot Detection boundary。当前仓库完整测试结果为 `38 passed, 1 skipped`；跳过项是显式 opt-in 的真实模型测试，31 项基线包含在当前完整测试集中。

## 9. Architecture Decisions

- **Observation 是理解层**：表达针对目标和特征的结构化观察。
- **Artifact 是输入对象**：保存从 Sample 派生的媒体表示和 provenance，不是语义结论。
- **Evidence 是证明关系**：把 Observation 关联回 source span、frame、Artifact 或可复核测量。
- **Detector 不产生 semantic Observation**：ShotDetector 只建立 temporal structure 并记录检测 Evidence。
- **AnalysisRun / producer_ref 保留可重算性**：不同分析运行可以并存，结果可追溯到 producer。

相关状态兼容决策见 [ADR-0008](../decisions/ADR-0008-observation-contract-phase5.md)；Shot Detection 的边界约束见 [Shot Boundary Detection Vertical Slice](../architecture/shot-detection.md)。

## 10. Next Phase

下一阶段是 **Phase 5.2 Analyzer Interface**。

目标链路为：

```text
AnalysisInput
   ↓
Analyzer
   ↓
AnalysisResult
   ↓
Observation + Evidence
```

Phase 5.2 应在已固化的 Observation、Artifact、Evidence 和 AnalysisRun 契约上建立 analyzer 接口，不改变 Phase 5.1 的语义边界。
