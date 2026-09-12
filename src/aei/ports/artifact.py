from pathlib import Path
from typing import Protocol
from aei.domain.models import Artifact, MediaStream, Sample
from aei.ports.media import FrameLocator

class FrameArtifactExtractor(Protocol):
    def extract_frame(self, sample: Sample, stream: MediaStream, frame_locator: FrameLocator, output_dir: Path) -> Artifact: ...
