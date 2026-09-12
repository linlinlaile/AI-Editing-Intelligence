import hashlib
from pathlib import Path
import pytest
from aei.adapters.artifact_payload import LocalArtifactPayloadLoader
from aei.adapters.vision.analyzer import VisionAnalyzer
from aei.adapters.vision.images import InvalidImageError, decode_image
from aei.domain.models import Artifact, Rational, TimePoint
from aei.ports.analyzer import AnalysisInput, AnalyzerContext
from aei.ports.artifact_payload import ArtifactPayloadError
from aei.ports.vision_model import Prediction

def _artifact(tmp_path, data=b"payload"):
    rel = "artifacts/frame.png"; path = tmp_path / rel; path.parent.mkdir(); path.write_bytes(data)
    return Artifact("art", "run", "asset", "sample", "frame_image", "image/png", rel, hashlib.sha256(data).hexdigest(), len(data), TimePoint("v", 9000, Rational(1, 1000), 2), 2, 2)

def test_payload_loader_returns_bytes_and_rejects_missing_or_tampered_payload(tmp_path):
    artifact = _artifact(tmp_path); payload = LocalArtifactPayloadLoader(tmp_path).load(artifact)
    assert payload.data == b"payload" and payload.content_hash == artifact.content_hash
    (tmp_path / artifact.uri).write_bytes(b"changed")
    with pytest.raises(ArtifactPayloadError, match="SHA-256|byte size"): LocalArtifactPayloadLoader(tmp_path).load(artifact)
    (tmp_path / artifact.uri).unlink()
    with pytest.raises((ArtifactPayloadError, FileNotFoundError)): LocalArtifactPayloadLoader(tmp_path).load(artifact)

def test_vision_analyzer_maps_prediction_to_observation_and_evidence(tmp_path):
    from PIL import Image
    path = tmp_path / "artifacts/frame.png"; path.parent.mkdir(); Image.new("RGB", (2, 2), (255, 0, 0)).save(path, format="PNG")
    artifact = Artifact("art", "run", "asset", "sample", "frame_image", "image/png", "artifacts/frame.png", hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size, TimePoint("v", 9000, Rational(1, 1000), 2), 2, 2)
    class Model:
        producer_ref = "vision:test-model@1"; taxonomy = "test-taxonomy"
        def predict(self, image_bytes):
            assert image_bytes.startswith(b"\x89PNG"); return Prediction("red fixture", 7, .875)
    context = AnalyzerContext("run", Model.producer_ref)
    result = VisionAnalyzer({"art": artifact}, LocalArtifactPayloadLoader(tmp_path), Model()).analyze(AnalysisInput(artifact_ids=("art",)), context)
    observation, evidence = result.observations[0], result.evidences[0]
    assert observation.feature == "vision.classification" and observation.target_type == "artifact" and observation.target_id == "art"
    assert observation.value == {"label": "red fixture", "class_id": 7, "taxonomy": "test-taxonomy"}
    assert observation.confidence == .875 and observation.producer_ref == context.producer_ref
    assert evidence.artifact_hash == artifact.content_hash and evidence.external_artifact_ref == artifact.uri
    assert evidence.metadata["source_point"]["pts"] == 9000

def test_corrupt_or_wrong_sized_image_is_rejected_before_model(tmp_path):
    with pytest.raises(InvalidImageError): decode_image(b"not an image", "image/png", (2, 2))

@pytest.mark.real_model
def test_real_resnet18_is_opt_in_and_uses_pinned_local_weights():
    import os
    if os.environ.get("RUN_REAL_MODEL") != "1": pytest.skip("set RUN_REAL_MODEL=1 to run explicit local-weight inference")
    from aei.adapters.vision.resnet18 import ResNet18VisionModel, PRODUCER_REF
    model = ResNet18VisionModel(Path(".venv/models/resnet18-f37072fd.pth")); assert model.producer_ref == PRODUCER_REF
    data = Path("tests/fixtures/vision/dog.jpg").read_bytes()
    prediction = model.predict(data)
    assert prediction.label and 0 <= prediction.class_id < 1000 and 0 <= prediction.score <= 1
