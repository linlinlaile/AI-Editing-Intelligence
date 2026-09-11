# 架构总览

## 1. 架构形态

V0.1 采用本地运行的模块化单体。模块通过稳定的 domain objects 和 ports 通信，具体模型、媒体库、数据库和向量索引都位于 adapters 中。

```text
domain contracts
      ↑
application use cases
      ↑
ports ───────────── adapters
                       ├─ FFmpeg / ffprobe / PyAV
                       ├─ PySceneDetect
                       ├─ OpenCV / NumPy
                       ├─ local vision/audio providers
                       ├─ SQLite repository
                       └─ derived vector index
```

`domain` 不依赖 PyTorch、OpenCV、SQLAlchemy、具体 VLM 或向量数据库。

## 2. 数据流

```text
源视频
  ↓
Ingest / Probe
  ├─ MediaAsset / MediaStream
  └─ source fingerprint + provenance
  ↓
Shot Detector
  └─ versioned Shot TimelineLayer
  ↓
Sampler
  ├─ representative frames
  ├─ temporal windows
  └─ audio windows
  ↓
Analyzers
  ├─ visual semantic observations
  ├─ motion / quality measurements
  └─ audio observations
  ↓
Semantic Timeline repository
  ↓
rebuildable derived indexes and projections
  ↓
Query Planner / Candidate Retrieval / Reranker
  ↓
Shot results + evidence + score breakdown
```

静态代表帧用于内容和构图；运镜、人物运动、动作连续和声音必须使用短时序窗口，不能由单张代表帧代替。

## 3. 模块边界

### Ingest

负责文件身份、容器和 stream 元数据、时间基、PTS、帧率元数据、旋转和色彩信息。原始文件只读引用；路径不是资产唯一 ID。

### Segmentation

产生版本化的 Shot layer。Detector 只负责边界和检测证据，不负责给 Shot 添加语义标签。

### Sampling

把 Shot 转换为可供不同分析器消费的 frame/window/audio sample，并记录 sample 的位置、目的和选择理由。

### Analysis

分析器实现统一 port，返回描述性 observations、evidence 和 producer 信息。不同分析器可以独立重跑。

### Timeline

SQLite 是权威的结构化存储。分析结果逻辑上追加，不静默覆盖；当前视图由显式 layer/run 选择得到。

### Retrieval

先做结构化过滤和轻量候选召回，再做 embedding、约束和质量重排。向量索引是派生缓存，可以删除后重建。

### Recommendation

Find Next Shot 使用当前 Shot、候选 Shot、edit intent 和描述性特征，输出带分项评分的 EditorialAssessment。它不是一个永久的 Shot-to-Shot 事实边。

## 4. 建议目录映射

```text
src/aei/
  domain/          # 稳定契约，不依赖基础设施
  application/     # ingest/search/recommend 用例
  ports/           # 外部能力接口
  adapters/        # 媒体、模型、存储、索引实现
  pipeline/        # 可恢复、可重跑的 stage runner
  cli/             # 首个用户接口
tests/             # contract/unit/integration
benchmarks/        # 数据集、标注、指标
docs/decisions/    # 会影响长期方向的 ADR
```

## 5. 存储分层

### 权威数据

SQLite 保存：

- MediaAsset、MediaStream
- AnalysisRun、ProducerRef
- TimelineLayer、TemporalSegment、HierarchyLink
- Sample、Artifact、Evidence
- DescriptiveObservation、ObservedRelation
- EditorialAssessment 及其输入引用

### 派生数据

- 代表帧和预览 artifact
- embedding 矩阵
- FTS/向量索引
- Shot feature projections
- 查询缓存

派生数据必须记录来源 run 和 schema/model revision，可以通过 Timeline 重新构建。

## 6. 运行方式

第一阶段只需要 CLI 和本地 stage runner。每个 stage 的输入应可由资产指纹、上游 run、配置和实现版本确定，从而支持幂等执行和失败恢复。没有真实的并发或部署需求前，不引入 Celery、Kafka 或微服务。
