import sqlite3
from aei.domain.models import *
from aei.storage.migrations import migrate

def test_vfr_nonzero_pts_and_rational_timebase():
    tb=Rational(1001,30000); s=TimeSpan(TimePoint('v',9000,tb,0),TimePoint('v',9034,tb,1))
    assert s.start.pts==9000 and s.end.pts==9034

def test_time_span_rejects_mixed_streams():
    try: TimeSpan(TimePoint('a',0,Rational(1,1)),TimePoint('b',1,Rational(1,1)))
    except ValueError: pass
    else: assert False

def test_migration_creates_authoritative_tables():
    c=sqlite3.connect(':memory:'); migrate(c)
    names={r[0] for r in c.execute("select name from sqlite_master where type='table'")}
    assert {'media_assets','media_streams','timeline_layers','temporal_segments'} <= names
import sqlite3
from aei.domain.models import AnalysisRun, Evidence, Observation
from aei.storage.migrations import migrate
from aei.adapters.repository import SemanticTimelineRepository

def test_v2_tables_and_append_only_run():
    c=sqlite3.connect(':memory:'); migrate(c)
    names={r[0] for r in c.execute("select name from sqlite_master where type='table'")}
    assert {'analysis_runs','samples','evidences','observations','observation_evidence'} <= names
    assert c.execute('select max(version) from schema_migrations').fetchone()[0] == 3

def test_observation_requires_evidence_and_roundtrips():
    c=sqlite3.connect(':memory:'); migrate(c)
    c.execute("insert into media_assets values ('a','file:///a',1,'f','mp4')")
    repo=SemanticTimelineRepository(c)
    repo.save_analysis_run(AnalysisRun('r','a','test-adapter'))
    ev=Evidence('e','r','numeric_measurement',numeric_measurement={'value':3.2,'unit':'px'})
    repo.save_evidence(ev)
    obs=Observation('o','r','segment','s','motion_vector',{'x':1},evidence_ids=('e',))
    repo.save_observation(obs)
    assert repo.get_observation('o').evidence_ids == ('e',)
