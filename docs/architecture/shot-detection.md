# Shot Boundary Detection Vertical Slice

`ShotDetector` is a domain-facing protocol whose adapter returns only integer PTS/frame boundary values. `PySceneDetectAdapter` owns all PySceneDetect imports and structures. `persist_shots` validates ordering and non-overlap in both canonical PTS and presentation frame-index coordinates, creates a `shot` layer and `TemporalSegment(kind="shot")` values using the source stream rational timebase, then records detector-output `Evidence` for every segment.

Shot Detection is responsible for shot boundaries, temporal structure, detector provenance, and detection evidence. It does not produce semantic observations, VLM output, or video understanding results. Those are produced later by analyzers from Artifact inputs and linked to Evidence.

SQLite stores segment PTS, frame indices, and timebase numerator/denominator in `temporal_segments`; detector provenance is retained on `TimelineLayer`, `AnalysisRun`, and evidence metadata. Historical observations, if present from earlier runs, remain readable but new Shot Detection runs do not create them.

Phase 3.5 contract fixtures cover CFR, VFR, non-zero start PTS, and B-frame metadata. Contract tests assert ordering, non-overlap, PTS/timebase round-trip, and presentation frame-index consistency before representative sampling is introduced.
