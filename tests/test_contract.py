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
