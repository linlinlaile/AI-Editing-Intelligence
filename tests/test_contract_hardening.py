import json, sqlite3
from pathlib import Path
import pytest
from aei.domain.models import Rational, TimePoint, TimeSpan, Evidence, Observation
from aei.storage.migrations import migrate
FIXTURE = Path(__file__).parent / 'fixtures' / 'contract-v1-golden.json'
def encode(v):
    if isinstance(v, Rational): return {'numerator': v.numerator, 'denominator': v.denominator}
    if isinstance(v, TimePoint): return {'stream_id':v.stream_id,'pts':v.pts,'time_base':encode(v.time_base),'presentation_frame_index':v.presentation_frame_index}
    if isinstance(v, TimeSpan): return {'start':encode(v.start),'end':encode(v.end)}
    raise TypeError(type(v))
def test_json_golden_time_objects():
    tb=Rational(1001,30000); payload={'schema_version':'1.0','timepoint':encode(TimePoint('video:0',9000,tb,12)), 'timespan':encode(TimeSpan(TimePoint('video:0',9000,tb,12),TimePoint('video:0',9034,tb,13)))}
    assert payload == json.loads(FIXTURE.read_text())
def test_timepoint_timespan_round_trip_preserves_pts_timebase_and_index():
    original=TimeSpan(TimePoint('v',-10,Rational(1001,30000),7),TimePoint('v',23,Rational(1001,30000),8)); raw=json.loads(json.dumps(encode(original)))
    rebuilt=TimeSpan(TimePoint(raw['start']['stream_id'],raw['start']['pts'],Rational(**raw['start']['time_base']),raw['start']['presentation_frame_index']),TimePoint(raw['end']['stream_id'],raw['end']['pts'],Rational(**raw['end']['time_base']),raw['end']['presentation_frame_index']))
    assert rebuilt == original
def test_migration_upgrade_from_v1_preserves_data():
    c=sqlite3.connect(':memory:'); c.executescript("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP); INSERT INTO schema_migrations(version) VALUES (1); CREATE TABLE media_assets(id TEXT PRIMARY KEY, uri TEXT NOT NULL, byte_size INTEGER, fingerprint TEXT NOT NULL UNIQUE, format_name TEXT); INSERT INTO media_assets VALUES ('a','file:///a',1,'fp','mp4');"); migrate(c)
    assert c.execute("SELECT uri FROM media_assets WHERE id='a'").fetchone()[0]=='file:///a'; assert c.execute('SELECT max(version) FROM schema_migrations').fetchone()[0]==3
    migrate(c); assert c.execute('SELECT count(*) FROM schema_migrations').fetchone()[0]==2
def test_observation_and_evidence_constraints():
    with pytest.raises(ValueError): Evidence('e','r','frame',frame_start=3)
    with pytest.raises(ValueError): Evidence('e','r','frame',frame_start=4,frame_end=2)
    assert Evidence('e','r','artifact',artifact_hash='sha256:x')
    with pytest.raises(ValueError): Observation('o','r','segment','s','x',{},evidence_ids=())
    with pytest.raises(ValueError): Observation('o','r','segment','s','x',{},evidence_ids=('e',),confidence=1.1)


def test_schema_declares_evidence_reference_requirement():
    schema = json.loads((Path(__file__).parents[1] / 'schemas' / 'semantic-timeline-v1.json').read_text())
    evidence = schema['$' + 'defs']['evidence']
    assert evidence['allOf'][0]['anyOf']


