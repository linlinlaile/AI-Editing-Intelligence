# VibeCut Phase 5.3 Summary

## 1. Phase 5.3.1 Goals

Phase 5.3.1 建立第一个真实 Vision Analyzer vertical slice：

```text
Artifact
  ↓
VisionAnalyzer
  ↓
Observation
  ↓
Evidence
```

本阶段只支持单个图像 Artifact 的固定标签集 image classification，不实现 caption、VLM、ASR、embedding 或视频级理解。

## 2. Architecture

Vision Analyzer 位于 `src/aei/adapters/vision/`，通过 ports 与领域契约隔离：

```text
AnalysisInput + AnalyzerContext
              ↓
        VisionAnalyzer
          ↙          ↘
   ArtifactPayload   VisionModel
       Loader            ↓
                    Prediction
              ↓
        AnalysisResult
         ↙          ↘
   Observation     Evidence
```

`VisionAnalyzer` 不访问 repository、SQLite 或 migration。应用层可以对返回的 `AnalysisResult` 进行校验和持久化。

Artifact payload 必须经过实际 bytes 的 byte size、SHA-256、媒体类型和图像尺寸校验。原始 payload 不进入 domain Observation。

## 3. Added Components

- `ArtifactPayload`：只读 bytes、media type、content hash 和 metadata。
- `ArtifactPayloadLoader`：读取 Artifact payload 的 port。
- `LocalArtifactPayloadLoader`：本地文件实现，校验路径 containment、大小和 hash。
- `Prediction`：模型输出的 label、class ID 和 score。
- `VisionModel`：只负责 image bytes → Prediction。
- `VisionAnalyzer`：负责输入约束、payload 校验、模型调用和 Observation/Evidence 映射。
- `ResNet18VisionModel`：固定本地权重的 CPU 分类模型实现。
- Pillow 图像解码和损坏图片检查。

Phase 5.3.1 不新增 SQLite 表、不新增 migration，也没有修改 MediaAsset、MediaStream、Rational、TimePoint、TimeSpan、TemporalSegment、Sample 或 Artifact contract。

## 4. Model Decision

第一版选择 Torchvision ResNet18 `IMAGENET1K_V1`：

```text
model: torchvision/resnet18
revision: IMAGENET1K_V1
taxonomy: imagenet-1k
runtime: torch 2.8.0+cpu / torchvision 0.23.0+cpu
preprocessing: rgb-cpu-v1
```

权重必须由操作者显式放置在：

```text
.venv/models/resnet18-f37072fd.pth
```

代码在加载前校验固定 SHA-256：

```text
f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec
```

不会隐式下载模型权重。模型身份通过 `producer_ref` 固化，并写入 Evidence metadata。

## 5. Observation / Evidence Example

Observation：

```json
{
  "target_type": "artifact",
  "target_id": "art-001",
  "feature": "vision.classification",
  "value": {
    "label": "red fixture",
    "class_id": 7,
    "taxonomy": "test-taxonomy"
  },
  "value_status": "SUCCESS",
  "confidence": 0.875,
  "confidence_kind": "uncalibrated_softmax",
  "producer_ref": "vision:test-model@1"
}
```

Evidence：

```json
{
  "kind": "artifact_classification_input",
  "external_artifact_ref": "artifacts/frame.png",
  "artifact_hash": "sha256:...",
  "metadata": {
    "artifact_id": "art-001",
    "asset_id": "asset-001",
    "sample_id": "sample-001",
    "source_point": {
      "stream_id": "video:0",
      "pts": 9000,
      "time_base": {"numerator": 1, "denominator": 1000},
      "presentation_frame_index": 2
    }
  }
}
```

`confidence` 是模型 score，不是事实可信度；单张 Artifact 分类不声明整个 Shot 的 coverage。

## 6. Tests

新增测试覆盖：

- Artifact payload bytes、大小和 SHA-256 校验。
- 缺失 payload 和损坏图片。
- 媒体类型和图像尺寸校验。
- Prediction → Observation 映射。
- Observation → Evidence 关联。
- run、producer 和 source provenance。
- 固定模型身份和本地权重 hash。

默认完整测试：

```text
38 passed, 1 skipped
```

跳过项是显式 opt-in 的真实模型测试。启用本地权重后的真实模型 smoke test：

```text
1 passed, 3 deselected
```

## 7. Limitations

- 只支持单个 PNG/JPEG 图像 Artifact。
- 只支持 ImageNet-1K 闭集分类。
- 不支持 caption、VLM、ASR、embedding 或视频时序分析。
- 未实现多 Artifact 输入和批量推理。
- 依赖本地 PyTorch CPU wheel 和显式权重文件。
- 分类 score 未做 calibration。
- 不根据单帧结果推断 Shot、Scene 或整段视频语义。
- 没有新增批量结果事务或 analyzer orchestration service。
- 现有 README、Phase 0-4 Summary 的部分阶段描述仍是历史基线，不能当作当前实现清单。

## 8. Next Phase Boundary

后续阶段可以在现有 `VisionModel` 和 `Analyzer` ports 上增加受控模型或输入能力，但必须继续保持：

- 模型实现位于 adapter。
- Analyzer 不访问 repository。
- Observation 必须关联 Evidence。
- 权重和模型 revision 可追溯。
- 大型 embedding vector 不进入 Observation value。
- 不修改既有媒体时间和 Artifact contract。

本总结不启动 Phase 5.3.2，也不引入新的模型、Analyzer Registry、云服务或检索能力。
