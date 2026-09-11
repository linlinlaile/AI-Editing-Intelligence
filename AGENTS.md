# 开发 Agent 指南

本文件面向后续 Codex、Claude 和其他开发 Agent。它描述当前项目的工作边界，不是通用模板。

## 项目目标

AI Editing Intelligence 要把本地视频素材转化为可检索、可解释、可重算的镜头级语义数据。长期数据核心是 Semantic Timeline：

```text
Video → Scene → Event → Shot → Moment / Frame
```

当前只需要可靠地建设 Video、Shot、Moment 及其证据；未来的 Scene/Event 和 Shot Relationship Graph 必须能够在不破坏已有契约的情况下加入。

## 当前阶段

项目处于 V0.1 设计固化阶段，仓库暂时没有实现代码。当前第一个编码目标是：

> Semantic Timeline Contract v1 + Frame-accurate Ingest Vertical Slice

这一阶段不接入 VLM、ASR、embedding 或云服务。

## 开始工作前必须阅读

按以下顺序阅读，避免把长期愿景误当成当前需求：

1. `README.md`：项目定位和当前入口。
2. `docs/product/v0.1.md`：产品范围、用户流程和非目标。
3. `docs/architecture/overview.md`：模块边界、数据流和技术栈。
4. `docs/architecture/semantic-timeline.md`：领域契约、时间语义和事实/判断分层。
5. 与本次改动相关的 `docs/decisions/ADR-*.md`。

如果代码与文档冲突，先停止扩大改动范围，说明冲突，并优先通过 ADR 或文档变更解决。

## 不可违反的工程原则

1. **Local-first**：源视频默认不上传、不修改；任何远程推理必须是显式可选的适配器。
2. **契约优先**：Semantic Timeline 是长期资产。领域契约不能依赖某个模型、数据库、推理框架或 UI。
3. **模型可替换**：Qwen、Whisper、某个 CLIP 或具体 VLM 都只能存在于 adapter，不得写入领域模型的固定逻辑。
4. **Frame-accurate**：持久化 canonical 时间必须使用源 stream 的整数 PTS 和 rational timebase；float seconds 只能用于显示或查询输入。
5. **Evidence-first**：模型结论必须尽量关联帧、时间窗口、音频窗口或可复核的数值证据；不确定时返回 `unknown`，不要猜测。
6. **事实与判断分离**：`DescriptiveObservation` / `ObservedRelation` 不得与 `EditorialAssessment` 混成同一语义层。
7. **版本可重算**：分析结果带 `AnalysisRun`、producer/model/config/code revision；新分析不能静默覆盖旧结果。
8. **Benchmark first**：新增重要能力时同时新增固定 fixture、标注格式或评估指标，不能只凭 demo 判断质量。
9. **边界清晰**：优先模块化单体和明确 ports/adapters，不要把逻辑塞进单文件，也不要在 V0.1 过早拆微服务。
10. **最小实现**：不要因为长期愿景而提前实现 NLE、自动成片、Scene/Event 推理或复杂 UI。

## 当前明确不做

V0.1 不做完整 NLE、复杂 timeline editor、自动字幕编辑器、AI 视频/图片/音乐生成、Motion Graphics、完整自动成片、调色、团队协作、手机端，也不把 transcript 剪辑作为核心入口。

Scene/Event 可以在 schema 中表达，但在没有可靠算法和评估集前不生成“看起来完整”的虚假层级。`good_next_shot` 也不能作为不带上下文的永久事实。

## 修改代码前的检查

- 确认改动对应 `docs/product/v0.1.md` 中的目标，而不是未来功能。
- 检查是否会改变 Semantic Timeline 契约；若会，先新增或更新 ADR 和 schema 版本。
- 检查是否把模型、ORM、索引或 UI 类型泄漏进 `domain`。
- 检查时间处理是否保留 PTS、timebase、frame index 以及 VFR 情况。
- 检查失败、unknown、低 coverage 是否与“没有检测到”区分开。
- 对新分析结果确认是否能追溯到证据和 producer。

## 测试和验证要求

至少运行与改动相关的单元测试、契约 golden tests 和集成测试；涉及时间或媒体时必须覆盖：

- CFR 视频
- VFR 视频
- 非零起始 PTS
- B-frame 或解码顺序与呈现顺序不同的素材
- 旋转/色彩元数据
- 读取失败或缺少某种 stream 的素材

涉及检索或推荐时，必须报告固定 benchmark 的 Recall@K / nDCG@K、负条件违例率或 pairwise preference 等适用指标，不能只展示一个示例结果。测试失败时不要通过放宽断言来掩盖契约问题。

## 文档纪律

实现新阶段前更新相关产品或架构文档；做出会影响长期方向的选择时新增 ADR。文档应引用其他文档，而不是复制大段内容。
