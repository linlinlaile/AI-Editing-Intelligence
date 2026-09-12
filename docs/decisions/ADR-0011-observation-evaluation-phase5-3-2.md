# ADR-0011: Observation Evaluation Layer

## Status

Accepted

## Context

当前系统已经具备以下分析链路：

```text
Artifact
  ↓
Analyzer
  ↓
Observation + Evidence
```

Observation 表示 Analyzer 产生的结构化理解结果，Evidence 表示该结果的来源和可复核依据。现有契约支持分析结果的追溯和持久化，但尚未提供独立的结果评价能力。

如果由 Analyzer 同时负责产生和评价 Observation，评价标准会与具体模型和分析器耦合，也无法在不重新运行 Analyzer 的情况下重新评价已有结果。因此需要建立独立的评价链路：

```text
Observation + Evidence
          ↓
       Evaluator
          ↓
   EvaluationResult
```

Phase 5.3.2 只建立最小的评价基础设施，不扩展为完整的评价平台。

## Decision

### 1. 独立的 Evaluation Layer

Evaluator 是 Analyzer 之后独立的评价层。Analyzer 负责产生 Observation 和 Evidence；Evaluator 负责根据既有输入快照评价这些结果。

### 2. EvaluationResult 的独立语义

EvaluationResult 不属于 Observation，也不是 Observation 的附加字段。它表达某个 Evaluator 在某个 evaluation run 中对某个 Observation 得到的评价结果。

### 3. 不修改 Observation Contract

Phase 5.3.2 不修改现有 Observation Contract，不向 Observation 增加质量、可用性或评价字段。

EvaluationResult 不写入 Observation，也不覆盖 Observation 的原始分析结果。

### 4. Evaluator 的依赖边界

Evaluator 不访问 repository、SQLite、migration 或文件系统。Evaluator 只接收应用层准备的 EvaluationInput。

应用层负责：

- 准备 EvaluationInput
- 调用 Evaluator
- 处理 EvaluationResult

Evaluator 不负责查询输入、持久化结果或驱动下游系统。

## EvaluationResult v1

EvaluationResult v1 包含以下字段：

- `id`
- `observation_id`
- `evaluation_run_id`
- `evaluator_ref`
- `evaluation_kind`
- `status`
- `scores`
- `findings`

其中：

- `evaluation_run_id` 标识评价运行，与 Observation 的 `run_id` 分离。
- `evaluator_ref` 标识评价器及其版本。
- `evaluation_kind` 标识评价类型，例如 `contract`、`evidence_grounding` 或 `benchmark`。
- `scores` 是可选的结构化数值结果；Phase 5.3.2 不定义统一的总质量分数或复杂指标。
- `findings` 保存评价发现及其原因，用于解释通过或失败结果。

`status` 只允许以下值：

- `PASS`
- `FAIL`
- `NOT_EVALUABLE`

`NOT_EVALUABLE` 表示当前输入不足或评价器不适用，不等同于 Observation 错误。Evaluator 执行异常由应用层作为运行错误处理，不伪装成评价失败。

Phase 5.3.2 不加入以下字段或语义：

- `quality_score`
- `editing_score`
- `usefulness`
- `human_label`

## First Evaluators

### ContractEvaluator

ContractEvaluator 只检查 Observation 的结构契约：

- Observation schema
- `value`
- `status`
- `producer_ref`

ContractEvaluator 不判断标签是否符合现实世界，也不判断结果是否适合剪辑。

### EvidenceGroundingEvaluator

EvidenceGroundingEvaluator 只检查：

- Observation-Evidence relation
- Evidence 引用是否存在于 EvaluationInput
- Observation、Evidence 和 AnalysisRun metadata 的 provenance consistency

它不判断 Evidence 是否足以证明现实世界语义，也不执行人工标注或任务效用评价。

### BenchmarkEvaluator

BenchmarkEvaluator 只保留扩展接口，不在 Phase 5.3.2 实现复杂指标、数据集加载、批量运行或统计报告。

## Storage

Phase 5.3.2：

- 不新增 migration
- 不新增 SQLite table
- 不修改现有 Observation storage
- 不修改现有 Evidence storage
- 不修改 `observation_evidence` relation

EvaluationResult v1 先作为独立的领域结果和应用层结果存在，不写入现有 semantic storage。

未来如果需要持久化 EvaluationResult，必须通过新的 ADR 单独决定 storage contract、migration 和查询方式。

## Non Goals

Phase 5.3.2 不做：

- Evaluation Platform
- annotation system
- benchmark pipeline
- Editing Quality Model
- Task Utility Evaluation
- Quality Gate

Phase 5.3.2 也不驱动搜索、排序、推荐或 Editing Agent 等下游系统。
