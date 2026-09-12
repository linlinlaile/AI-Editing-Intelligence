# Shot Boundary Detection Vertical Slice

`ShotDetector` is a domain-facing protocol whose adapter returns only integer PTS/frame boundary values. `PySceneDetectAdapter` owns all PySceneDetect imports and structures. `persist_shots` validates ordering and non-overlap, creates a `shot` layer and `TemporalSegment` values using the source stream rational timebase, then records detector-output `Evidence` and `shot_boundary_detected` observations for every segment.

SQLite stores segment PTS, frame indices, and timebase numerator/denominator in `temporal_segments`; detector provenance is retained on `TimelineLayer`, `AnalysisRun`, evidence metadata, and observation producer reference.
