import sqlite3
from aei.domain.models import *
from aei.storage.migrations import migrate
from aei.adapters.repository import SemanticTimelineRepository
from aei.adapters.sampling import UniformSampler, persist_samples

class Locator:
    def __init__(self, points): self.points=points
    def locate_presentation_frame(self, stream, frame_index): return self.points[frame_index]

def test_uniform_sampling_uses_vfr_pts_and_preserves_timebase():
    c=sqlite3.connect(':memory:'); migrate(c)
    c.execute("insert into media_assets values ('a','file:///a',1,'fp','mp4')")
    c.execute("insert into analysis_runs(id,asset_id,producer_name,status) values ('r','a','uniform','completed')")
    c.execute("insert into media_streams(id,asset_id,stream_index,kind,codec,tb_num,tb_den,start_pts,duration_pts) values ('s','a',0,'video','h264',1001,30000,9000,1000)")
    stream=MediaStream('s','a',0,'video','h264',Rational(1001,30000),9000,1000)
    seg=TemporalSegment('seg','layer','shot',TimeSpan(TimePoint('s',9000,stream.time_base,2),TimePoint('s',9100,stream.time_base,7)))
    points={i:TimePoint('s',9000+i*13,stream.time_base,i) for i in range(2,7)}
    repo=SemanticTimelineRepository(c); run=AnalysisRun('r','a','uniform')
    out=persist_samples(UniformSampler(),[seg],stream,run,repo,Locator(points))
    assert [s.source_frame_index for s in out] == [2,3,4,5,6]
    assert [s.source_span.start.pts for s in repo.get_samples('r')] == [9026,9039,9052,9065,9078]
    assert all(s.segment_id=='seg' and s.sampling_method=='uniform' for s in out)
