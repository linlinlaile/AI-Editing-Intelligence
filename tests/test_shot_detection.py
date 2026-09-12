import sqlite3
from aei.domain.models import *
from aei.storage.migrations import migrate
from aei.adapters.repository import SemanticTimelineRepository
from aei.adapters.shot_detection import ShotBoundary, persist_shots

class FakeDetector:
    name='fake'; version='1.2'; config={'threshold': 12}
    def detect(self, asset, stream): return [ShotBoundary(100,200,0,9),ShotBoundary(200,350,10,19)]

def test_shot_vertical_slice_preserves_timebase_and_provenance():
    c=sqlite3.connect(':memory:'); migrate(c)
    c.execute("insert into media_assets values ('a','file:///a',1,'fp','mp4')")
    stream=MediaStream('s','a',0,'video','h264',Rational(1001,30000),0,350)
    c.execute("insert into media_streams(id,asset_id,stream_index,kind,codec,tb_num,tb_den,start_pts,duration_pts) values ('s','a',0,'video','h264',1001,30000,0,350)")
    repo=SemanticTimelineRepository(c); run=AnalysisRun('r','a','fake',config_hash='x')
    segs=persist_shots(FakeDetector(),MediaAsset('a','file:///a',1,'fp'),stream,run,repo)
    assert len(segs)==2 and segs[0].span.start.time_base==Rational(1001,30000)
    assert repo.get_segments('r:shots')[1].span.start.pts==200
    obs=repo.get_observation('r:shots:0:observation'); assert obs.feature=='shot_boundary_detected'
