# VibeCut Phase 5.2 总结：Analyzer Interface

## 1. Phase Overview

Phase 5.2 的目标是建立统一的 **Analyzer Contract**，为不同 AI 能力提供稳定一致的接入边界。Vision、ASR 和 Embedding 都通过同一套接口进入系统，同时保持领域契约与具体模型实现解耦。

本阶段的核心链路为：

```text
AnalysisInput
   ↓
Analyzer
   ↓
AnalysisResult
   ↓
Observation + Evidence
```

Analyzer 输出继续遵循 Phase 5.1 的 Observation Contract 和 Evidence-first 原则，为后续可重算、可审计的分析运行提供架构基线。

## 2. Architecture

完整流程如下：

```text
AnalysisInput
   ↓
Analyzer
   ↓
AnalysisResult
   ↓
Observation + Evidence
```

- **AnalysisInput**：描述本次分析可使用的输入引用。
- **Analyzer**：执行分析并调用所需的模型能力。
- **AnalysisResult**：同时返回 Observation 和 Evidence。
- **Observation + Evidence**：形成可验证的理解输出，并保留 run 与 producer provenance。

该边界允许 Vision、ASR、Embedding 等能力共享应用层流程，而不把某一种媒体输入、模型 SDK 或持久化实现写入领域接口。

## 3. Analyzer Contract

本阶段新增：

```text
src/aei/ports/analyzer.py
```

该模块定义统一 analyzer port。

### AnalysisInput

`AnalysisInput` 支持以下输入引用：

- `artifact_ids`
- `sample_ids`
- `audio_segment_ids`

输入通过标识引用表达，不绑定单一输入类型。未来视觉分析可以使用 Artifact，音频分析可以使用 audio segment，其他分析也可以组合 Sample 与 Artifact，而无需改变 Analyzer 接口。

### AnalyzerContext

`AnalyzerContext` 包含：

- `analysis_run_id`
- `producer_ref`
- `configuration`

这些字段提供本次运行的追溯信息和分析配置。Context 不包含：

- database
- repository
- model client
- file handle

因此 Analyzer 可以接收应用层提供的能力和上下文，但不会直接依赖存储、文件系统或某个模型供应商。

### AnalysisResult

`AnalysisResult` 包含：

- `observations`
- `evidences`

Analyzer 不能只返回裸 Observation。每个 Observation 都必须能够通过 Evidence 表达其依据；结果对象同时携带两者，交由应用层进行一致性验证和持久化。

## 4. Analyzer Boundary

Analyzer 负责：

- 分析 AnalysisInput 指定的输入。
- 调用所需的模型能力。
- 产生 Observation 和 Evidence。
- 将结果关联到 AnalyzerContext 提供的 run 与 producer provenance。

Analyzer 不负责：

- SQLite
- repository
- migration
- persistence

应用层负责验证 AnalysisResult，并通过既有 repository 和存储适配器保存结果。这样可以保持 domain/ports 与数据库、ORM、模型客户端之间的边界清晰。

## 5. FakeAnalyzer

本阶段新增 `FakeAnalyzer`，用于验证 analyzer vertical slice：

```text
AnalysisInput
   ↓
Analyzer
   ↓
AnalysisResult
   ↓
Observation
   ↓
Evidence
```

FakeAnalyzer 不包含 AI 或真实模型调用。它提供确定性的测试输出，用来验证接口调用、结果结构、provenance 传递和 Observation-Evidence 关系，为未来真实 Analyzer adapter 提供最小基线。

## 6. Validation

应用层对 AnalysisResult 执行结果验证。

Observation 必须满足：

- `run_id` 与 AnalyzerContext 的 `analysis_run_id` 一致。
- `producer_ref` 存在。
- 所有 Evidence 引用都存在于本次 AnalysisResult 中。

Evidence 必须满足：

- `run_id` 与 AnalyzerContext 的 `analysis_run_id` 一致。

禁止产生无 Evidence 的 Observation。无论分析结果是成功、失败、未知、未覆盖还是部分覆盖，Observation 都必须保持可追溯的 Evidence 关系；结果验证失败时应拒绝该结果。

## 7. Storage

Phase 5.2 不需要 migration，也不新增表。

结果复用既有表：

- `observations`
- `evidences`
- `observation_evidence`

Analyzer 只生成领域结果，存储层仍由既有 repository 负责。该设计使不同 AI 能力能够共享同一套持久化结构，同时保留 AnalysisRun、producer 和 Evidence 的可重算与审计能力。

## 8. Tests

最终测试结果：

```text
35 passed
```

覆盖内容包括：

- Analyzer contract
- FakeAnalyzer
- provenance
- evidence relation
- invalid result rejection
- no repository dependency

这些测试确认 Analyzer 接口能够传递统一输入和上下文，输出同时包含 Observation 与 Evidence，并拒绝缺少 Evidence、run provenance 不一致或 producer 缺失的无效结果。

## 9. Architecture Decisions

Phase 5.2 固化以下架构决策：

- **Analyzer 是 AI 能力接入边界**：Vision、ASR、Embedding 等能力通过统一 port 接入。
- **模型不是系统核心**：具体模型、模型客户端和推理框架属于 adapter 或实现层，不进入领域契约。
- **Observation 是统一理解输出**：不同分析能力都以统一的 Observation Contract 表达结果。
- **Evidence 保证可验证性**：每个 Observation 都必须能够回到关联证据，并保留 run 与 producer provenance。
- **应用层负责验证与持久化**：Analyzer 不访问 SQLite、repository，也不执行 migration。

相关接口决策见 [ADR-0009](../decisions/ADR-0009-analyzer-interface-phase5-2.md)。

## 10. Next Phase

下一阶段是 **Phase 5.3 First Vision Model Adapter**。

目标链路为：

```text
Artifact
   ↓
VisionAnalyzer
   ↓
Observation + Evidence
```

Phase 5.3 将首次接入真实视觉模型，并在本阶段 Analyzer Contract、Observation、Evidence 和 AnalysisRun 契约之上实现 VisionAnalyzer adapter。

