from __future__ import annotations
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Optional

@dataclass(frozen=True)
class Rational:
    numerator: int
    denominator: int
    def __post_init__(self):
        if self.denominator == 0: raise ValueError('denominator cannot be zero')
    def as_fraction(self) -> Fraction: return Fraction(self.numerator, self.denominator)

@dataclass(frozen=True)
class TimePoint:
    stream_id: str
    pts: int
    time_base: Rational
    presentation_frame_index: Optional[int] = None

@dataclass(frozen=True)
class TimeSpan:
    start: TimePoint
    end: TimePoint
    def __post_init__(self):
        if self.start.stream_id != self.end.stream_id: raise ValueError('span endpoints must use same stream')
        if self.start.pts > self.end.pts: raise ValueError('span must be non-decreasing')

@dataclass(frozen=True)
class MediaAsset:
    id: str; uri: str; byte_size: Optional[int]; fingerprint: str; format_name: Optional[str] = None

@dataclass(frozen=True)
class MediaStream:
    id: str; asset_id: str; index: int; kind: str; codec: Optional[str]
    time_base: Rational; start_pts: Optional[int]; duration_pts: Optional[int]
    width: Optional[int] = None; height: Optional[int] = None; pixel_format: Optional[str] = None
    average_frame_rate: Optional[Rational] = None; nominal_frame_rate: Optional[Rational] = None
    rotation: Optional[int] = None; sample_aspect_ratio: Optional[Rational] = None
    display_aspect_ratio: Optional[Rational] = None; color_metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class TemporalSegment:
    id: str; layer_id: str; kind: str; span: TimeSpan

@dataclass(frozen=True)
class TimelineLayer:
    id: str; asset_id: str; kind: str; detector_revision: str

def rational(value: Any) -> Optional[Rational]:
    if value in (None, '', '0/0'): return None
    if isinstance(value, Rational): return value
    if isinstance(value, (int, float)): return Rational(int(value), 1)
    n, d = str(value).split('/'); return Rational(int(n), int(d))
