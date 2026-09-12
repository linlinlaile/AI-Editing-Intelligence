"""Read local derived payloads without decoding or altering their bytes."""
import hashlib
from pathlib import Path, PureWindowsPath

from aei.domain.models import Artifact
from aei.ports.artifact_payload import ArtifactPayload, ArtifactPayloadError


class LocalArtifactPayloadLoader:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve(strict=True)

    def load(self, artifact: Artifact) -> ArtifactPayload:
        uri = artifact.uri
        if (PureWindowsPath(uri).drive or PureWindowsPath(uri).root
                or ":" in uri or "\\" in uri or ".." in Path(uri).parts):
            raise ArtifactPayloadError("artifact URI must stay inside payload root")
        path = (self.root / uri).resolve()
        if not path.is_relative_to(self.root):
            raise ArtifactPayloadError("artifact URI escapes payload root")
        # Open once: size and hash apply to the exact bytes returned to the caller.
        with path.open("rb") as source:
            data = source.read(artifact.byte_size + 1)
        if len(data) != artifact.byte_size:
            raise ArtifactPayloadError("artifact byte size mismatch")
        digest = hashlib.sha256(data).hexdigest()
        if digest != artifact.content_hash:
            raise ArtifactPayloadError("artifact SHA-256 mismatch")
        return ArtifactPayload(data, artifact.media_type, digest, {"artifact_id": artifact.id, "uri": artifact.uri, "asset_id": artifact.asset_id, "sample_id": artifact.sample_id, "source_point": artifact.source_point})
