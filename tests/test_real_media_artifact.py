import sqlite3
import pytest
pytest.importorskip('PIL')
from aei.adapters.artifact import PyAVFrameArtifactExtractor
from aei.adapters.media import PyAVFrameLocator
from aei.domain.models import AnalysisRun, Sample
from aei.domain.models import MediaStream, Rational
from tests.test_real_media_contract import _write_video

def test_real_cfr_frame_artifact_payload(tmp_path):
    path=tmp_path/'sample.mkv'; _write_video(path,[0,33,66])
    import av
    with av.open(str(path)) as c:
        s=c.streams.video[0]; stream=MediaStream('v','asset',s.index,'video',s.codec_context.name,Rational(s.time_base.numerator,s.time_base.denominator),0,99,s.width,s.height)
    sample=Sample('sample','run','asset','p','frame',source_frame_index=1)
    art=PyAVFrameArtifactExtractor(path).extract_frame(sample,stream,PyAVFrameLocator(path),tmp_path)
    assert (tmp_path/art.uri).exists() and len(art.content_hash)==64 and art.source_point.presentation_frame_index==1
