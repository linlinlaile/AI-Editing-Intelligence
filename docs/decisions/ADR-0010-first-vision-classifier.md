# ADR-0010: First Vision Classifier (Phase 5.3.1)

- Status: Accepted
- Date: 2026-09-12

Use a single-image, local CPU ResNet18 IMAGENET1K_V1 classifier. The weight file is supplied explicitly and verified against a fixed SHA-256 before deserialization. No adapter or test downloads weights. Torch/Torchvision are optional, lazy imports; no Transformers, OpenCV, caption, embedding, or video semantics are introduced.

ArtifactPayloadLoader accepts an Artifact reference and returns bytes, media type, verified hash and the immutable Artifact metadata. A filesystem implementation validates containment, size and hash. VisionAnalyzer receives an input metadata snapshot, a loader and a VisionModel; it never accesses a repository. VisionModel accepts image bytes and returns Prediction. Evidence binds the verified payload URI/hash to the original source TimePoint, preserving integer PTS and rational timebase without inventing a time span.

Only one image Artifact is accepted. Unsupported inputs, missing/corrupt payloads and inference errors raise explicit exceptions and emit no successful result; the caller handles failed runs. Classification confidence is an uncalibrated softmax score, not truth probability. Coverage is unspecified because preprocessing crops the input. Existing schemas/tables/contracts are unchanged. See ../architecture/vision-classification.md for usage and validation.
