"""Byte-only payload boundary; independent of filesystem and image libraries."""
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from aei.domain.models import Artifact


@dataclass(frozen=True)
class ArtifactPayload:
    data: bytes
    media_type: str
    content_hash: str
    metadata: Mapping[str, Any]


class ArtifactPayloadError(ValueError):
    """Payload cannot be trusted as the supplied Artifact."""


class ArtifactPayloadLoader(Protocol):
    def load(self, artifact: Artifact) -> ArtifactPayload: ...
