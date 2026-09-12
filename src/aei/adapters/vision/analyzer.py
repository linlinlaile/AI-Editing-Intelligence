import hashlib
import json
from dataclasses import asdict
from typing import Mapping

from aei.domain.models import Artifact, Evidence, Observation, ObservationStatus
from aei.ports.analyzer import AnalysisInput, AnalysisResult, AnalyzerContext
from aei.ports.artifact_payload import ArtifactPayloadError, ArtifactPayloadLoader
from aei.ports.vision_model import VisionModel
from aei.adapters.vision.images import decode_image


class VisionAnalyzer:
    name = "vision-classification"
    version = "1"

    def __init__(self, artifacts: Mapping[str, Artifact], loader: ArtifactPayloadLoader, model: VisionModel):
        self._artifacts = dict(artifacts)
        self._loader = loader
        self._model = model

    def analyze(self, input: AnalysisInput, context: AnalyzerContext) -> AnalysisResult:
        if len(input.artifact_ids) != 1 or input.sample_ids or input.audio_segment_ids:
            raise ValueError("vision classification requires exactly one Artifact and no other inputs")
        if context.producer_ref != self._model.producer_ref:
            raise ValueError("context producer_ref does not match actual model identity")
        if context.configuration:
            raise ValueError("version 1 has fixed preprocessing and accepts no configuration overrides")
        artifact = self._artifacts[input.artifact_ids[0]]
        if artifact.id != input.artifact_ids[0]:
            raise ValueError("Artifact snapshot ID mismatch")
        if artifact.kind != "frame_image" or artifact.media_type not in {"image/png", "image/jpeg"}:
            raise ValueError("only PNG/JPEG frame image Artifacts are supported")
        payload = self._loader.load(artifact)
        digest = hashlib.sha256(payload.data).hexdigest()
        if (payload.metadata.get("artifact_id") != artifact.id or payload.metadata.get("uri") != artifact.uri
                or payload.metadata.get("source_point") != artifact.source_point
                or payload.media_type != artifact.media_type
                or payload.content_hash != digest or digest != artifact.content_hash
                or len(payload.data) != artifact.byte_size):
            raise ArtifactPayloadError("loader payload does not match Artifact metadata")
        with decode_image(payload.data, artifact.media_type, (artifact.width, artifact.height)):
            pass
        prediction = self._model.predict(payload.data)
        key = json.dumps([context.analysis_run_id, context.producer_ref, artifact.id,
                          digest, self.name, self.version], ensure_ascii=True)
        identity = hashlib.sha256(key.encode()).hexdigest()
        evidence = Evidence(
            id=f"vision:{identity}:evidence", run_id=context.analysis_run_id,
            kind="artifact_classification_input", external_artifact_ref=artifact.uri,
            artifact_hash=digest,
            metadata={"artifact_id": artifact.id, "asset_id": artifact.asset_id,
                      "sample_id": artifact.sample_id, "artifact_run_id": artifact.run_id,
                      "source_point": asdict(artifact.source_point),
                      "producer_ref": self._model.producer_ref, "analyzer_revision": self.version},
        )
        observation = Observation(
            id=f"vision:{identity}:observation", run_id=context.analysis_run_id,
            target_type="artifact", target_id=artifact.id, feature="vision.classification",
            value={"label": prediction.label, "class_id": prediction.class_id,
                   "taxonomy": self._model.taxonomy},
            value_status=ObservationStatus.SUCCESS, confidence=prediction.score,
            confidence_kind="uncalibrated_softmax", coverage=None,
            producer_ref=self._model.producer_ref, evidence_ids=(evidence.id,),
        )
        result = AnalysisResult((observation,), (evidence,))
        result.validate(context)
        return result
