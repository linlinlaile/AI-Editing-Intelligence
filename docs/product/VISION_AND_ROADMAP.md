# VibeCut Vision and Roadmap

## Long-term vision

VibeCut（项目目录与包名仍使用 AI Editing Intelligence）把本地视频素材转化为可检索、可解释、可重算的语义资产。长期目标不是先替代非线性编辑器，而是逐步建立能够理解素材、记住素材并协助编辑的系统：

```text
Video Understanding
        ↓
Semantic Video Memory
        ↓
Editing Intelligence
        ↓
AI Editing Assistant
        ↓
AI Editing Agent
```

## Current product position

第一阶段产品定位是 **AI Video Asset Intelligence**。它帮助创作者导入视频素材、自动理解素材、组织镜头、搜索需要的镜头，并逐步建立个人视频知识库。当前产品以 Shot 为主要结构单元，以 Semantic Timeline、Observation 和 Evidence 形成可追溯的素材智能基础。

V0.1 仍是 local-first 的素材理解、检索和镜头推荐系统；它不替代 Premiere、DaVinci Resolve 或其他 NLE，也不承诺自动成片。现阶段的技术质量以契约、证据、可重算 provenance 和固定 benchmark 为依据。

## Phase 0–10 roadmap

| Phase | Product / architecture goal | Explicit non-goals |
|---|---|---|
| 0–4 | **Media Foundation**：建立媒体读取、整数 PTS 与 rational timebase、Semantic Timeline、Shot、采样、真实帧定位和 Artifact 基础。 | 不生成语义理解，不做 NLE、自动成片或模型绑定。 |
| 5 | **Video Understanding Foundation**：建立 Observation Contract、Analyzer 接口、视觉 Observation、Shot-level Observation 聚合和 Evidence/评价边界。 | 不把具体模型写入领域契约；不把 Observation 当作编辑判断。 |
| 5.6 | **Temporal Observation Foundation**：补齐跨帧、时间窗口和时序变化的可追溯观察，为运动、动作和连续性提供稳定契约与评估入口。 | 不提前生成 Scene/Event 层级；不把 temporal coverage 当作语义准确率。 |
| 6 | **Product Foundation**：把已验证的素材理解能力包装成可用的导入、索引、浏览、运行 provenance 和本地知识库基础。 | 不实现完整剪辑器、团队协作、云端强制依赖或自动成片。 |
| 7 | **Semantic Video Memory / Retrieval**：建立可解释的素材记忆和检索，支持按意图、属性、时间上下文和来源证据寻找镜头。 | 不把相关性分数写成永久事实；不在缺少 benchmark 时宣称通用检索质量。 |
| 8 | **Editorial Intelligence**：在事实 Observation 之上表达带上下文、意图和理由的编辑判断，例如镜头衔接、节奏和覆盖建议。 | 不把编辑判断混入 Observation；不把 `good_next_shot` 变成无上下文的永久标签。 |
| 9 | **AI Editing Assistant**：让用户以对话或任务方式探索素材、比较方案、得到可解释建议，并保留用户选择和反馈。 | 不静默修改项目或替用户做不可逆编辑；不绕过 Evidence 和用户控制。 |
| 10 | **AI Editing Agent**：在明确授权和可回滚边界内，跨素材记忆、编辑判断和工具执行完成多步编辑协作。 | 不牺牲可审计性、可回滚性和用户最终控制；不把代理行为当作领域事实。 |

阶段不是一次性承诺的功能清单。每一阶段都必须在已有契约、证据和 benchmark 边界内演进；新的 task、指标或持久化能力需要独立契约和决策记录。

## Layer evolution

前半段建设 **Video Intelligence Layer**：

```text
Video → Media Foundation → Shot → Artifact → Observation → Evidence → Evaluation → Benchmark
```

这一层描述媒体事实、可复核的 AI 观察和质量证据。后半段在其上增加 **Editing Intelligence Layer**：

```text
Semantic Video Memory → Editorial Assessment → User Feedback → Assistant → Agent
```

Editing Intelligence 可以引用 Observation 和 Evidence，但不能改写它们的语义。编辑建议必须带有上下文、意图、理由和适用范围；用户反馈记录用户行为与偏好，不能被回填为 AI Observation。这样可以在不破坏既有 Semantic Timeline 和 benchmark 契约的前提下，从素材理解逐步走向编辑协作。

## Relationship to current architecture

Phase 0–4 的 Media Foundation、Phase 5.1–5.4 的 Observation/Analyzer/视觉与 Shot 聚合，以及 Phase 5.5 的 Benchmark Foundation 构成当前已完成基础。Phase 5.5 benchmark 独立于 Observation/Evidence，比较既有报告，不运行 analyzer 或 model，也不改变 Observation、Evidence 或 EvaluationResult；本路线不改变这些边界。

