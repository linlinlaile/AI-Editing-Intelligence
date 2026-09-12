import sqlite3
from aei.domain.models import AnalysisRun, Evidence, Observation, ObservationStatus
from aei.storage.migrations import migrate
from aei.adapters.repository import SemanticTimelineRepository

def test_observation_statuses_and_queries_round_trip():
    c = sqlite3.connect(':memory:'); migrate(c)
    c.execute("insert into media_assets values ('a','file:///a',1,'f5','mp4')")
    repo = SemanticTimelineRepository(c); repo.save_analysis_run(AnalysisRun('r','a','adapter'))
    repo.save_evidence(Evidence('e','r','artifact',artifact_hash='sha256:x'))
    for i, status in enumerate(ObservationStatus):
        repo.save_observation(Observation(f'o{i}','r','artifact','art',f'f{i}',{'label': status.value}, status, .5, 'heuristic', .8, ('e',), 'adapter:v1'))
    rows = repo.list_observations_by_run('r')
    assert {o.value_status for o in rows} == set(ObservationStatus)
    assert repo.list_observations_by_subject('artifact','art') == rows
    assert all(o.evidence_ids == ('e',) and o.producer_ref == 'adapter:v1' for o in rows)

def test_legacy_observation_status_is_read_compatibly():
    c = sqlite3.connect(':memory:'); migrate(c)
    c.execute("insert into media_assets values ('a','file:///a',1,'legacy-f','mp4')")
    c.execute("insert into analysis_runs(id,asset_id,producer_name,status) values ('r','a','old','completed')")
    c.execute("insert into evidences(id,run_id,kind,artifact_hash) values ('e','r','artifact','sha256:x')")
    c.execute("insert into observations values ('o','r','artifact','a','x','1','observed',null,null,null,null)")
    c.execute("insert into observation_evidence values ('o','e')")
    assert SemanticTimelineRepository(c).get_observation('o').value_status is ObservationStatus.SUCCESS

def test_observation_value_rejects_raw_outputs_payloads_large_vectors_and_nonfinite_numbers():
    import math, pytest
    for value in ({'prompt': 'x'}, {'response': 'x'}, {'artifact_payload': 'x'}, [0.0] * 4097, math.nan):
        with pytest.raises(ValueError):
            Observation('bad','r','artifact','a','feature',value,evidence_ids=('e',))
