from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4
from aei.domain.models import AnalysisRun, Evidence, TemporalSegment, TimelineLayer, TimePoint, TimeSpan, MediaAsset, MediaStream

@dataclass(frozen=True)
class ShotBoundary:
    start_pts: int
    end_pts: int
    start_frame_index: int
    end_frame_index: int

class ShotDetector(Protocol):
    name: str
    version: str
    config: dict[str, Any]
    def detect(self, asset: MediaAsset, stream: MediaStream) -> list[ShotBoundary]: ...

class PySceneDetectAdapter:
    name = 'pyscenedetect'
    version = '0.6'
    def __init__(self, config: dict[str, Any] | None = None): self.config = config or {'detector': 'content'}
    def detect(self, asset: MediaAsset, stream: MediaStream) -> list[ShotBoundary]:
        try:
            from scenedetect import open_video, SceneManager
            from scenedetect.detectors import ContentDetector
        except ImportError as e: raise RuntimeError('PySceneDetect is not installed') from e
        video=open_video(asset.uri); manager=SceneManager(); manager.add_detector(ContentDetector(**{k:v for k,v in self.config.items() if k != 'detector'})); manager.detect_scenes(video)
        out=[]
        fps=stream.average_frame_rate or stream.nominal_frame_rate
        if fps is None: raise ValueError('PySceneDetect adapter requires a stream frame rate for PTS mapping')
        start_pts=stream.start_pts or 0
        def to_pts(frame: int) -> int:
            # FrameTimecode is frame-accurate; map CFR frame numbers into source ticks.
            return start_pts + (frame * fps.denominator * stream.time_base.denominator) // (fps.numerator * stream.time_base.numerator)
        for start,end in manager.get_scene_list():
            sf,ef=start.get_frames(),end.get_frames()
            out.append(ShotBoundary(to_pts(sf), to_pts(ef), sf, ef))
        return out

def persist_shots(detector: ShotDetector, asset: MediaAsset, stream: MediaStream, run: AnalysisRun, repository) -> list[TemporalSegment]:
    boundaries=detector.detect(asset, stream)
    ordered=sorted(boundaries, key=lambda b:(b.start_pts,b.end_pts))
    previous=None
    previous_frame=None
    for b in ordered:
        if (b.start_pts >= b.end_pts or b.start_frame_index < 0 or
            b.start_frame_index >= b.end_frame_index or
            (previous is not None and b.start_pts < previous) or
            (previous_frame is not None and b.start_frame_index < previous_frame)):
            raise ValueError('shot boundaries must be ordered, non-overlapping, and non-empty')
        previous=b.end_pts
        previous_frame=b.end_frame_index
    repository.save_analysis_run(run)
    layer=TimelineLayer(f'{run.id}:shots',asset.id,'shot',f'{detector.name}:{detector.version}'); repository.save_layer(layer)
    result=[]
    for i,b in enumerate(ordered):
        sid=f'{layer.id}:{i}'
        span=TimeSpan(TimePoint(stream.id,b.start_pts,stream.time_base,b.start_frame_index),TimePoint(stream.id,b.end_pts,stream.time_base,b.end_frame_index))
        seg=TemporalSegment(sid,layer.id,'shot',span); repository.save_segment(seg)
        ev=Evidence(f'{sid}:evidence',run.id,'detector_output',description='shot boundary detected',source_span=span,frame_start=b.start_frame_index,frame_end=b.end_frame_index,metadata={'detector':detector.name,'detector_version':detector.version,'config':detector.config}); repository.save_evidence(ev)
        result.append(seg)
    return result
