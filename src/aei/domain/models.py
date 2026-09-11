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

@dataclass(frozen=True)
class AnalysisRun:
    id: str
    asset_id: str
    producer_name: str
    status: str = 'completed'
    model_name: Optional[str] = None
    model_revision: Optional[str] = None
    code_revision: Optional[str] = None
    config_hash: Optional[str] = None
    input_artifact_ids: tuple[str, ...] = ()
    parent_run_ids: tuple[str, ...] = ()
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass(frozen=True)
class Sample:
    id: str
    run_id: str
    asset_id: str
    purpose: str
    kind: str
    source_span: Optional[TimeSpan] = None
    source_frame_index: Optional[int] = None
    selection_reason: Optional[str] = None
    artifact_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class Evidence:
    id: str
    run_id: str
    kind: str
    description: Optional[str] = None
    source_span: Optional[TimeSpan] = None
    frame_start: Optional[int] = None
    frame_end: Optional[int] = None
    numeric_measurement: Optional[dict[str, Any]] = None
    external_artifact_ref: Optional[str] = None
    artifact_hash: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if self.frame_start is not None and self.frame_end is not None and self.frame_start > self.frame_end:
            raise ValueError('frame range must be non-decreasing')
        if not any((self.source_span is not None, self.frame_start is not None,
                    self.numeric_measurement is not None, self.external_artifact_ref is not None)):
            raise ValueError('evidence must contain a supported reference')

@dataclass(frozen=True)
class Observation:
    id: str
    run_id: str
    target_type: str
    target_id: str
    feature: str
    value: Any
    value_status: str = 'observed'
    confidence: Optional[float] = None
    confidence_kind: Optional[str] = None
    coverage: Optional[float] = None
    evidence_ids: tuple[str, ...] = ()
    producer_ref: Optional[str] = None
    def __post_init__(self):
        if not self.evidence_ids: raise ValueError('observation must reference at least one evidence')
        if self.confidence is not None and not 0 <= self.confidence <= 1: raise ValueError('confidence must be between 0 and 1')
        if self.coverage is not None and not 0 <= self.coverage <= 1: raise ValueError('coverage must be between 0 and 1')
        if self.value_status not in {'observed','unknown','not_applicable','failed'}: raise ValueError('invalid value_status')

def rational(value: Any) -> Optional[Rational]:
    if value in (None, '', '0/0'): return None
    if isinstance(value, Rational): return value
    if isinstance(value, (int, float)): return Rational(int(value), 1)
    n, d = str(value).split('/'); return Rational(int(n), int(d))
