from __future__ import annotations
from dataclasses import replace
from uuid import uuid4
from aei.domain.models import AnalysisRun, Evidence, MediaStream, Sample, TemporalSegment, TimePoint, TimeSpan
from aei.ports.media import FrameLocator


class UniformSampler:
    name = "uniform"
    version = "1.0"

    def __init__(self, ratios=(0.0, 0.25, 0.5, 0.75, 1.0)):
        self.ratios = tuple(ratios)

    def sample_segment(self, segment: TemporalSegment, stream: MediaStream, frame_locator: FrameLocator, run: AnalysisRun) -> list[Sample]:
        start = segment.span.start.presentation_frame_index
        end = segment.span.end.presentation_frame_index
        if start is None or end is None or end <= start:
            raise ValueError("uniform sampling requires presentation frame indices")
        last = end - 1
        result=[]
        for ordinal, ratio in enumerate(self.ratios):
            if not 0 <= ratio <= 1: raise ValueError("sampling ratios must be between 0 and 1")
            frame_index = round(start + ratio * (last - start))
            point = frame_locator.locate_presentation_frame(stream, frame_index)
            span = TimeSpan(point, point)
            sid = f"{run.id}:{segment.id}:sample:{ordinal}"
            result.append(Sample(sid, run.id, run.asset_id, "representative_sampling", "frame", span, frame_index,
                                 f"uniform_ratio={ratio:g}", (), segment.id, self.name))
        return result


def persist_samples(sampler, segments, stream: MediaStream, run: AnalysisRun, repository, frame_locator: FrameLocator):
    samples=[]
    for segment in sorted(segments, key=lambda s: (s.span.start.pts, s.id)):
        for sample in sampler.sample_segment(segment, stream, frame_locator, run):
            repository.save_sample(sample)
            evidence = Evidence(f"{sample.id}:evidence", run.id, "sample_reference",
                                 description="representative sample source", source_span=sample.source_span,
                                 frame_start=sample.source_frame_index, frame_end=sample.source_frame_index,
                                 metadata={"sampling_method": sampler.name, "segment_id": segment.id})
            repository.save_evidence(evidence)
            samples.append(sample)
    return samples
