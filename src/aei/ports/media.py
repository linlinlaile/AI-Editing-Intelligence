from typing import Protocol
from aei.domain.models import MediaStream, TimePoint


class FrameLocator(Protocol):
    """Resolve presentation-order frames into source timeline coordinates."""

    def locate_presentation_frame(self, stream: MediaStream, frame_index: int) -> TimePoint:
        ...
