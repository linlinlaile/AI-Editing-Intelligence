# Semantic Timeline 契约

Semantic Timeline 是模型可以反复替换、但下游检索和推荐仍然可以工作的长期数据契约。它不是某个模型输出的 caption JSON，也不是某个向量库的表结构。

## 1. 核心对象

### MediaAsset / MediaStream

`MediaAsset` 表示用户导入的源文件身份和容器信息；`MediaStream` 表示其中的视频、音频等 stream。

至少保留：

- asset ID、原始 URI、文件大小和指纹
- stream index、codec、分辨率、像素格式
- stream timebase、start PTS、duration PTS
- average/nominal frame rate 作为元数据
- rotation、SAR/DAR、色彩元数据

路径、文件名和 float duration 都不能单独作为身份或时间真值。

### TimelineLayer / TemporalSegment

`TimelineLayer` 表示一次结构分析的版本，例如某次 Shot detection。`TemporalSegment` 表示一个带时间范围的节点，`kind` 可以是 `shot`、`moment`、未来的 `scene` 或 `event`。

同一个 Asset 可以存在多个 Shot layer。重新运行 detector 应创建新 layer，不应覆盖旧边界。应用通过显式 active layer 选择当前视图。

V0.1 只要求可靠生成 `shot` 和 `moment`。

### Sample

Sample 是分析输入，不等同于 Moment：

- representative frame
- short temporal window
- audio window
- detector-specific sample

每个 Sample 都有精确 source reference、用途、选择理由和 artifact 引用。

## 2. 时间语义

```text
TimePoint:
  stream_id
  pts: integer
  time_base: rational
  presentation_frame_index: integer | null

TimeSpan:
  start: TimePoint       # inclusive
  end: TimePoint         # exclusive
```

规则：

1. canonical 时间使用源 stream 的整数 PTS 和 rational timebase。
2. frame index 是 presentation order；不能把 decode index 当成显示顺序。
3. `fps` 只用于显示、估计或兼容外部工具，不能替代 PTS。
4. VFR、非零起始 PTS、B-frame 和缺失 duration 必须可表达。
5. float seconds 只用于 UI、查询输入和日志展示。
6. Proxy 或转码产生的新时间轴必须通过显式映射回到 source 坐标。

## 3. 描述性观察

`DescriptiveObservation` 描述一个目标的可观察特征，但不宣称绝对真理：

```json
{
  "schema_version": "1.0",
  "id": "obs_123",
  "target": {"type": "segment", "id": "shot_123"},
  "feature": "camera.motion",
  "value": {"label": "pan_left", "speed": "slow"},
  "value_status": "observed",
  "confidence": 0.81,
  "confidence_kind": "heuristic",
  "coverage": 0.74,
  "evidence_ids": ["evidence_1", "evidence_2"],
  "producer_ref": "producer_7",
  "analysis_run_id": "run_456"
}
```

建议的 feature namespace：

- `content.subject`, `content.object`, `content.location`, `content.action`
- `camera.shot_size`, `camera.angle`, `camera.motion`
- `person.entry_exit`, `person.screen_direction`, `person.distance_change`, `person.gaze_direction`
- `emotion.valence`, `emotion.arousal`, `emotion.coarse_mood`
- `quality.blur`, `quality.shake`, `quality.exposure`, `quality.occlusion`
- `audio.speech`, `audio.music`, `audio.ambient`
- `embedding.visual_text`, `embedding.audio`, `embedding.transcript`

`value_status` 至少区分 `observed`、`unknown`、`not_applicable` 和 `failed`。没有观测到不等于确认不存在。

`coverage` 表示观测覆盖了目标时间范围的多少；例如“没有人物”必须有足够的全片段覆盖，不能因为某一张代表帧没检测到人物就成立。

## 4. Evidence 和 Provenance

### Evidence

Evidence 可以引用：

- 单帧或帧范围
- 视频时间窗口
- 音频时间窗口
- ROI / bounding box / track
- 光流、清晰度、曝光等数值
- transcript 或分类器片段

Evidence 应引用 source 坐标和 artifact hash，而不是只保存一段无法复核的自然语言解释。

### ProducerRef / AnalysisRun

每次分析记录：

- adapter/provider 名称
- model name 和 model revision/hash
- prompt/template revision（如适用）
- code revision
- config hash
- 输入 artifact / 上游 run
- 开始、结束和状态

这使模型替换、失败重跑和结果比较成为可能。

## 5. 关系和编辑判断

三种东西不能混成一个“关系图”：

### HierarchyLink

结构关系，例如 Shot 属于某个未来 Scene，或 Moment 位于某个 Shot。

### ObservedRelation

描述性/推断性关系，例如：

- `same_subject`
- `same_location`
- `continues_action`
- `same_event_probability`
- `visual_similarity`
- `motion_similarity`

### EditorialAssessment

带上下文的编辑判断，例如：

- `match_for_intent`
- `good_next_shot`
- `continuity_score`
- `contrast_score`

`EditorialAssessment` 必须带 current shot、candidate shot、edit intent、ranker revision、输入 observation IDs 和分项评分。它可以被重新计算或废弃，不能被当作永恒事实。

## 6. 事实、置信度和评分

- `confidence`：系统认为观察或推断正确的程度。
- `coverage`：观测覆盖目标范围的程度。
- `similarity`：两个对象在某一维度的相似程度。
- `suitability/relevance score`：在某个查询或编辑意图下的匹配程度。

这些数值不能互相替代，也不能只存一个总分。

## 7. 版本和更新规则

1. 新分析 run 追加结果，不静默修改旧 run。
2. schema 的破坏性变化必须迁移并增加 major version。
3. feature key 使用命名空间，新增 feature 不应破坏未知字段的读取。
4. 数据库 schema、domain schema、模型 revision 和索引 schema 分开版本化。
5. 当前视图是 projection，不是唯一真相。
6. 每个契约对象都要有 JSON golden test；跨版本读取要有 migration test。

## 8. 存储映射

SQLite 是权威存储，建议使用独立表表达结构实体、观察、证据、run 和关系；特征 JSON 只承载经过 schema 验证的值。常用检索字段可以建立 materialized projection，但 projection 删除后必须能由 observations 重建。

embedding、缩略图、光流结果和向量索引放在 artifact/derived 层，不成为领域契约的一部分。
