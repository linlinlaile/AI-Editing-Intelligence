import sqlite3
from aei.domain.models import Artifact, AnalysisRun, Rational, Sample, TimePoint
from aei.storage.migrations import migrate
from aei.adapters.repository import SemanticTimelineRepository

def test_artifact_round_trip_and_queries():
    c=sqlite3.connect(':memory:'); migrate(c)
    c.execute("insert into media_assets values ('a','file:///a',1,'fp','mp4')")
    repo=SemanticTimelineRepository(c); repo.save_analysis_run(AnalysisRun('r','a','extractor'))
    repo.save_sample(Sample('s','r','a','p','frame',source_frame_index=2))
    art=Artifact('art','r','a','s','frame_image','image/png','artifacts/art.png','hash',4,TimePoint('v',9000,Rational(1,1000),2),2,2)
    repo.save_artifact(art)
    assert repo.get_artifact('art') == art
    assert repo.get_artifacts_for_sample('s') == [art]
    assert repo.get_artifacts('r') == [art]
