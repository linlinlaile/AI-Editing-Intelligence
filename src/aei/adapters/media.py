"""Media-backed implementations of media ports.

The adapter deliberately keeps PyAV objects private.  The domain receives only
integer PTS values in the stream's declared timebase.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

from aei.domain.models import MediaStream, Rational, TimePoint


class PyAVFrameLocator:
    """Resolve presentation-order frame indices using a local PyAV decode.

    Frames are decoded lazily once per video stream and retained as PTS values,
    which makes repeated sampling deterministic and preserves VFR/B-frame order.
    """

    def __init__(self, path: str | Path, *, container_factory: Callable[[str], Any] | None = None):
        self.path = str(path)
        self._container_factory = container_factory
        self._pts_by_stream: dict[int, tuple[int, ...]] = {}

    def _load(self, stream: MediaStream) -> tuple[int, ...]:
        if stream.kind != "video":
            raise ValueError("frame location requires a video stream")
        if stream.index in self._pts_by_stream:
            return self._pts_by_stream[stream.index]
        if self._container_factory is None:
            try:
                import av
            except ImportError as exc:  # pragma: no cover - environment dependent
                raise RuntimeError("PyAV is required for PyAVFrameLocator") from exc
            factory = av.open
        else:
            factory = self._container_factory
        container = factory(self.path)
        try:
            try:
                av_stream = next(s for s in container.streams if s.index == stream.index)
            except StopIteration as exc:
                raise ValueError(f"stream index {stream.index} not found in media") from exc
            if getattr(av_stream, "type", None) != "video":
                raise ValueError("frame location requires a video stream")
            values: list[int] = []
            for frame in container.decode(av_stream):
                if frame.pts is None:
                    raise ValueError("decoded frame has no presentation PTS")
                frame_tb = getattr(frame, "time_base", None) or getattr(av_stream, "time_base", None)
                if frame_tb is None:
                    raise ValueError("decoded frame has no timebase")
                src = Fraction(int(frame.pts)) * Fraction(frame_tb.numerator, frame_tb.denominator)
                dst = src / stream.time_base.as_fraction()
                if dst.denominator != 1:
                    raise ValueError("decoded PTS cannot be represented in stream timebase")
                values.append(dst.numerator)
            self._pts_by_stream[stream.index] = tuple(values)
            return self._pts_by_stream[stream.index]
        finally:
            close = getattr(container, "close", None)
            if close:
                close()

    def locate_presentation_frame(self, stream: MediaStream, frame_index: int) -> TimePoint:
        if not isinstance(frame_index, int) or isinstance(frame_index, bool):
            raise TypeError("frame_index must be an integer")
        if frame_index < 0:
            raise IndexError("frame_index must be non-negative")
        pts = self._load(stream)
        if frame_index >= len(pts):
            raise IndexError(f"presentation frame index {frame_index} is out of range")
        return TimePoint(stream.id, pts[frame_index], stream.time_base, frame_index)


# Name used by callers that describe the implementation in terms of FFmpeg.
FFmpegFrameLocator = PyAVFrameLocator
