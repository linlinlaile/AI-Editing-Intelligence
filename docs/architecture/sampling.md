# Representative Sampling

Representative sampling converts temporal segments into deterministic media observation points. `RepresentativeSampler` is a sampling port; frame index to source PTS resolution belongs to the media/time `FrameLocator` port.

The initial `UniformSampler` selects five ratios (0%, 25%, 50%, 75%, 100%) over the presentation-frame interval. The end boundary is exclusive, so 100% resolves to the last frame inside the segment. PTS and rational timebase always come from `FrameLocator`, including VFR and non-zero-PTS media.

Samples remain semantic-free. Sampling creates source-reference Evidence, while future analyzers create Observations from one or more Samples.
