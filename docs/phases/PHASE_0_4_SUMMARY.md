# VibeCut Phase 0-4 Foundation Summary

## 1. Project Vision

VibeCut（项目目录与包名仍使用 AI Editing Intelligence）长期目标是把本地视频素材转化为可检索、可解释、可重算的镜头级语义数据，并逐步支持：

```text
Video Understanding
        ↓
Semantic Timeline
        ↓
Editing Intelligence
        ↓
AI Editing Agent
```

Phase 0-4 的定位是建立可靠的视频理解基础设施：固化媒体时间语义、Semantic Timeline 契约、Shot 边界、代表性采样、真实帧定位和帧 Artifact 生成。本阶段不生成语义理解结果。

## 2. Completed Phases Overview

| Phase | Goal | Status |
|---|---|---|
| Phase 0 | Project foundation | Done |
| Phase 1 | Frame accurate media foundation | Done |
| Phase 2 | Semantic Timeline | Done |
| Phase 3 | Shot detection | Done |
| Phase 3.5 | Contract hardening | Done |
| Phase 4.1 | Representative Sampling | Done |
| Phase 4.2 | Real Frame Resolution | Done |
| Phase 4.2.1 | Real Media Validation | Done |
| Phase 4.3 | Sample Artifact Layer | Done |

## 3. Current Architecture

```text
Video
  ↓
Media Foundation
  ↓
Semantic Timeline
  ↓
Shot (TemporalSegment(kind="shot"))
  ↓
Sample
  ↓
Artifact
  ↓
Evidence / future Observation inputs
```

- **Media Foundation**：读取资产和 stream 元数据，维护 PTS、timebase 和呈现顺序。
- **Semantic Timeline**：保存可版本化的时间段、分析运行和来源关系。
- **Shot**：结构边界，不包含语义标签。
- **Sample**：分析输入用的媒体观察点，记录精确 source reference。
- **Artifact**：从 Sample 派生的媒体 payload 及其 provenance，不是语义结果。
- **Evidence**：保存可复核的 source span、frame reference、artifact hash 或数值证据。

## 4. Media Foundation

已实现的基础对象和能力包括：

- `MediaAsset`
- `MediaStream`
- `Rational`
- `TimePoint`
- `TimeSpan`
- integer PTS 和 rational timebase
- CFR、VFR、non-zero PTS、B-frame presentation order 支持

时间契约：

- canonical time 是源 stream 的整数 PTS 加 rational timebase。
- frame index 表示 presentation order，不能用 decode index 替代。
- `TimeSpan` 为 start-inclusive、end-exclusive。
- float seconds 只用于显示、查询输入和日志，不是持久化时间真值。

## 5. Semantic Timeline Contract

当前核心对象：

- `AnalysisRun`：一次可追溯、可重跑的分析运行。
- `TemporalSegment`：带 `TimeSpan` 的时间轴节点；当前主要使用 `kind="shot"`，也可表达 `moment`。
- `Sample`：分析输入的媒体观察点。
- `Artifact`：Sample 产生的 derived media representation。
- `Evidence`：可复核的来源或测量证据。
- `Observation`：未来分析器产生的描述性观察，目前仅保留契约和存储。

系统采用 Evidence-first 原则：分析结果应尽量关联源时间、帧范围、Artifact hash 或数值测量；未知、失败和未覆盖不能等同于“没有检测到”。

## 6. Shot Understanding

Shot detection 通过 `ShotDetector` protocol 接入，当前实现为 PySceneDetect adapter。检测输出被转换为：

```text
Shot → TemporalSegment(kind="shot")
```

边界保留 source stream、PTS、rational timebase 和 presentation frame index。Detector 负责边界和检测证据，不负责添加语义标签。

## 7. Representative Sampling

`Sample` 是媒体观察点，不是语义结果，也不是图片容器。当前字段包含：

- `segment_id`
- `source_span`
- `source_frame_index`
- `sampling_method`
- `purpose`
- `selection_reason`
- `artifact_ids`

`UniformSampler` 使用 0%、25%、50%、75%、100% 五个比例。由于 segment 结束边界 exclusive，100% 解析为 segment 内最后一个实际呈现帧。

## 8. Frame Resolution

`FrameLocator` 的职责是：

```text
presentation frame index
        ↓
TimePoint
```

当前实现为 `PyAVFrameLocator`（并提供 `FFmpegFrameLocator` 别名）。它惰性解码视频流，按 presentation order 建立 PTS 映射，并支持 CFR、VFR、non-zero PTS 和 B-frame presentation order。缺失 PTS、缺失 timebase、非视频 stream 和越界索引会显式失败。

## 9. Artifact Layer

`Artifact` 是 derived media representation，不是 semantic result、Observation 或 AI output。当前固定 contract 包含：

- `id`
- `run_id`
- `asset_id`
- `sample_id`
- `kind`
- `media_type`
- `uri`
- `content_hash`
- `byte_size`
- `source_point`
- `width`
- `height`

当前 adapter 从 Sample 的 `source_frame_index` 定位并解码帧，编码为 PNG/JPEG，针对实际 payload bytes 计算 SHA-256，并生成 portable 相对 URI，例如 `artifacts/<sample>_artifact_png.png`。`sample_id` 表示当前 frame Artifact 由单个 Sample 生成，不限制未来 Artifact 必须只由一个 Sample 生成。

SQLite 保存 Artifact metadata、source provenance 和 hash；文件系统保存可重建的 derived payload。Artifact 不携带开放 metadata dict，也不包含 caption、classification 或 embedding。

## 10. Evidence-first Design

当前关系应理解为：

```text
Sample → Artifact
             ↓
       source provenance
             ↓
Evidence → future Observation
```

Artifact 为未来观察器提供可复核输入。Observation 未来必须通过 Evidence 表达依据；Evidence 当前继续使用 `external_artifact_ref`、`artifact_hash` 和 `source_span`，没有新增 `artifact_id` 字段。Sample 不是 semantic result，Artifact 不是 understanding，Observation 不是数据库原始字段的转储。

未来的 VLM、ASR 和 embedding 都必须通过独立分析运行产生 Observation，并保留 Evidence 和 producer/run provenance。

## 11. Storage Architecture

当前 SQLite schema version 为 **3**。主要表包括：

- `analysis_runs`
- `temporal_segments`
- `samples`
- `artifacts`
- `evidences`
- `observations`
- `observation_evidence`

`SemanticTimelineRepository` 是 storage adapter，负责 domain object 与 SQLite 行之间的转换和 round-trip。Artifact 提供保存、单项读取以及按 sample/run 查询。SQLite 是权威结构化存储；派生 payload 可删除并根据上游 Sample/run 重建。

## 12. Testing Status

当前完整测试结果：

```text
28 passed
```

覆盖内容包括：

- CFR
- VFR
- non-zero PTS
- B-frame presentation order
- rational timebase
- sampling contract
- Artifact contract
- Artifact persistence round-trip
- real media frame validation
- PNG payload 文件存在性、byte size、SHA-256 和 source point
- 主要错误边界

## 13. Important Architectural Decisions

### Decision 1: Rational Time Model

持久化 canonical 时间使用整数 PTS、rational timebase、stream ID 和可选 presentation frame index。禁止用 float seconds 或 nominal FPS 取代源时间真值。

### Decision 2: Evidence-first

可解释结果必须能够回到 source span、frame、Artifact hash 或数值测量。Observation 与 Evidence 分层保存。

### Decision 3: Sample is an observation point

Sample 表示分析输入位置和选择理由，不等同于 Moment，也不承载语义结论。

### Decision 4: Artifact is derived media representation

Artifact 表示从 Sample 派生的帧媒体 payload 和固定 provenance metadata，不是语义结果或模型输出。

### Decision 5: Local payload + SQLite metadata

源视频默认本地只读。Artifact payload 保存在本地派生目录，SQLite 保存 metadata、hash 和来源关系，以支持审计、迁移和重建。

## 14. Known Limitations

当前尚未实现：

- Visual Observation
- VLM integration
- ASR observation
- Embedding
- Editing Intelligence
- AI Editing Agent
- Scene/Event 自动推理
- 从 Artifact 自动生成语义标签

## 15. Next Phase Entry Point

下一阶段是 **Phase 5 Visual Observation**。

入口目标：

```text
Artifact
   ↓
Observation
   ↓
Evidence
```

第一步应先定义 `Observation Contract`，明确 target、feature、value status、confidence、coverage、producer/run 和 Evidence 引用，然后再接入具体视觉分析器。Phase 5 不应改变当前媒体时间契约、Sample 语义或 Artifact payload contract。
