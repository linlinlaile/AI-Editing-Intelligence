# Phase 5.3.2 Observation Evaluation Summary

## 1. Goal

建立 `Observation → Evaluator → EvaluationResult` 的独立评价层。应用层可以提供已有 Observation 与 Evidence 快照进行评价，无需重新运行 Analyzer。本阶段只提供结构契约、证据关联和 provenance 检查，以及 benchmark 扩展点。

## 2. Architecture

```text
Artifact
  ↓
Analyzer
  ↓
Observation + Evidence
  ↓
Evaluator
  ↓
EvaluationResult
```

应用层准备 `EvaluationInput`，其中包含单个 Observation、Evidence snapshot、AnalysisRun metadata snapshot 和 evaluation run 标识。Evaluator 只消费这些输入，不查询 repository、SQLite 或文件系统；应用层负责调用和处理返回结果。

## 3. Added Components

- **EvaluationResult**：独立评价结果，包含 Observation 引用、evaluation run、evaluator 版本引用、评价类型、状态、scores 和 findings。
- **EvaluationFinding**：通过 `code`、`message` 和 `details` 说明评价发现及原因。
- **EvaluationStatus**：`PASS`、`FAIL`、`NOT_EVALUABLE` 三值枚举。
- **EvaluationKind**：评价类型概念；当前由 `EvaluationResult.evaluation_kind: str` 表达，使用 `contract`、`evidence_grounding`、`benchmark`。当前代码没有独立的 `EvaluationKind` 类型或枚举。
- **EvaluationInput**：应用层准备的评价输入快照。
- **Evaluator port**：定义 `name`、`version` 和 `evaluate(input) → EvaluationResult`，支持运行时 protocol 检查。
- **ContractEvaluator**：Observation 自身结构检查。
- **EvidenceGroundingEvaluator**：Evidence 引用、关联及 provenance 检查。
- **BenchmarkEvaluator extension point**：保留 benchmark 接口，不执行 benchmark。

领域对象位于 `src/aei/domain/evaluation.py`，port 位于 `src/aei/ports/evaluator.py`，评价器位于 `src/aei/evaluation/`。

## 4. Evaluator Responsibilities

### ContractEvaluator

检查 Observation 的必填字段、`ObservationStatus`、`producer_ref` 和 value 结构。value 检查包含 JSON 可序列化性、NaN / infinity，以及 raw response、Artifact payload 等保留字段限制。结构违规以 finding 返回 `FAIL`，检查通过返回 `PASS`，`evaluation_kind="contract"`。不判断标签与现实是否相符。

### EvidenceGroundingEvaluator

检查 Observation 引用的 Evidence 是否存在于输入快照中；缺失引用返回 `missing_evidence_reference`，空引用集合返回 `invalid_evidence_relation`。对被引用 Evidence 检查其 `run_id` 与 Observation 是否一致；当 AnalysisRun metadata 提供 `run_id` 时，也参与一致性检查。不一致返回 `provenance_mismatch`。

若没有上述失败，但被引用 Evidence 缺少 source、artifact 或数值测量来源，返回 `NOT_EVALUABLE` 和 `untraceable_evidence`。完整匹配返回 `PASS`，`evaluation_kind="evidence_grounding"`。检查不判断证据是否足以证明现实世界语义。

### BenchmarkEvaluator

保留符合 Evaluator protocol 的扩展点，`evaluation_kind="benchmark"`。调用固定返回 `NOT_EVALUABLE`，并通过 `benchmark_not_implemented` finding 说明当前阶段只定义扩展点。没有 dataset loader、runner、ground truth comparison 或指标计算。

## 5. Storage

- No migration：没有新增 migration。
- No SQLite table：没有新增 SQLite 表。
- No Observation schema change：没有修改 Observation schema。
- Evidence storage 和 `observation_evidence` relation 保持不变。

EvaluationResult 当前仅作为独立领域结果返回，不写入 semantic storage。未来持久化需要新的 ADR 单独决定。

## 6. Tests

Step 4 完成时使用项目解释器运行完整测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

最终结果：

```text
49 passed, 1 skipped
```

跳过项是需要显式启用 `RUN_REAL_MODEL=1` 的本地真实模型测试。新增测试文件为 `test_contract_evaluator.py`、`test_evidence_grounding_evaluator.py` 和 `test_benchmark_evaluator_interface.py`，覆盖结构检查、Evidence 匹配与 run 不一致，以及 benchmark protocol 与扩展点返回结果。本次收尾仅编写文档，没有新增测试或重新运行测试。

## 7. Architecture Decisions

依据 [ADR-0011: Observation Evaluation Layer](../decisions/ADR-0011-observation-evaluation-phase5-3-2.md)：

- **EvaluationResult 不属于 Observation**：不添加 Observation 评价字段，也不覆盖原始分析结果。
- **Evaluator 不访问 repository**：输入准备和结果处理由应用层负责，评价器不依赖 SQLite 或文件系统。
- **Evaluation 是独立层**：Analyzer 产生理解结果，Evaluator 根据输入快照评价这些结果。
- **NOT_EVALUABLE 区别于 FAIL**：材料不足或评价器不适用不等同于 Observation 错误；执行异常由应用层作为运行错误处理。

ADR 要求 evaluation run 与分析 run 分离。当前实现中，调用方未提供 `evaluation_run_id` 时仍回退到 Observation 的 `run_id`；要保持两者分离，调用方需显式传入独立的评价运行标识。本次文档收尾记录此限制，不修改代码。

## 8. Limitations

当前不支持：

- Benchmark dataset 加载或 benchmark pipeline。
- Human annotation 或 annotation format。
- Semantic correctness evaluation、标签准确率或现实语义验证。
- Task utility evaluation、editing usefulness 或模型质量评价。
- Quality gate，以及驱动搜索、排序或推荐的下游流程。
- Accuracy、F1、Recall、nDCG 或 calibration metrics。

当前 grounding 检查允许缺省 AnalysisRun metadata；只有提供其 `run_id` 时才能完成三方 provenance 比较。`EvaluationKind` 仍以字符串字段表达。上述限制不改变本阶段只建立最小独立评价层的范围。
