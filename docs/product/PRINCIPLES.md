# VibeCut Long-term Principles

## 1. Facts and judgments stay separate

`Observation != Editorial Assessment`。

Observation 描述由分析器从素材中观察到的事实、状态和关系，并带有 producer、run 和 evidence。Editorial Assessment 是带上下文和编辑意图的判断，例如“适合接在后面”或“可作为结尾”。判断可以引用 Observation，但不能伪装成媒体事实，也不能覆盖原始观察。

## 2. Evidence first

AI 理解结果必须尽量：

- 可追溯到 source span、frame、Artifact 或可复核的数值测量；
- 可验证，能够由固定输入和明确版本重新检查；
- 能回到 source evidence，而不是只保留无法解释的标签或分数。

Unknown、failed 和未覆盖必须保持可区分。Benchmark 是对固定任务和数据的证据，不是全局正确性的永久声明。

## 3. User feedback is independent from AI observation

```text
Observation ≠ Human Preference
```

用户收藏、跳过、修正、选择、拒绝和编辑结果表达行为或偏好。它们可以用于个性化和后续评估，但不能直接改写某个 Observation 的事实内容，也不能把一次选择解释为模型已经观察到的证据。

## 4. Product Layer must not pollute Video Intelligence Layer

各层职责保持清晰：

| Layer | Responsibility |
|---|---|
| **Media Foundation** | 负责媒体事实、stream 元数据、整数 PTS、rational timebase、帧顺序和可定位的源引用。 |
| **Observation** | 负责 AI 对素材做出的描述性观察事实、状态和关系，并保留 provenance 与 Evidence。 |
| **Editorial Assessment** | 负责带上下文、任务和编辑意图的编辑判断、排序理由和建议。 |
| **User Feedback** | 负责用户行为、选择、修正和偏好；它是产品输入，不是 AI Observation。 |

Product Layer 可以组织、检索和呈现 Video Intelligence Layer 的内容，也可以产生新的编辑任务和反馈数据；它不能把 UI 状态、推荐结果或用户偏好写回媒体事实和 Observation 契约。

## 5. Contracts precede capabilities

新增重要能力先定义稳定契约、证据边界、版本和适用 benchmark，再接入模型、存储或 UI。模型、数据库、推理框架和云服务属于 adapter 或 infrastructure，不能成为领域契约的隐含前提。

## 6. Recompute and provenance remain first-class

分析结果必须能追溯到 AnalysisRun、producer、model、config 和 code revision。新分析不能静默覆盖旧结果；不同 revision 的结果必须可以并列比较，并在证据不足时明确标记不可比。

