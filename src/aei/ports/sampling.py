from typing import Protocol
from aei.domain.models import AnalysisRun, MediaStream, Sample, TemporalSegment
from aei.ports.media import FrameLocator


class RepresentativeSampler(Protocol):
    name: str
    version: str

    def sample_segment(
        self, segment: TemporalSegment, stream: MediaStream,
        frame_locator: FrameLocator, run: AnalysisRun,
    ) -> list[Sample]: ...
