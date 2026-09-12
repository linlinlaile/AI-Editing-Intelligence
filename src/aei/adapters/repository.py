from __future__ import annotations
import json, sqlite3
from aei.domain.models import AnalysisRun, Sample, Evidence, Observation, TimeSpan, TimePoint, Rational

def _span_values(span):
    if span is None: return (None, None, None, None, None, None, None, None, None)
    return (span.start.stream_id, span.start.pts, span.start.time_base.numerator, span.start.time_base.denominator, span.end.pts, span.end.time_base.numerator, span.end.time_base.denominator, span.start.presentation_frame_index, span.end.presentation_frame_index)

def _span(stream_id, start, end, sf, ef):
    if stream_id is None or start is None or end is None: return None
    return TimeSpan(TimePoint(stream_id, start, Rational(1, 1), sf), TimePoint(stream_id, end, Rational(1, 1), ef))

class SemanticTimelineRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    def save_analysis_run(self, run: AnalysisRun):
        self.conn.execute('INSERT INTO analysis_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (run.id,run.asset_id,run.producer_name,run.status,run.model_name,run.model_revision,run.code_revision,run.config_hash,json.dumps(run.input_artifact_ids),json.dumps(run.parent_run_ids),run.started_at,run.completed_at)); self.conn.commit()
    def save_sample(self, sample: Sample):
        sid,sp,sn,sd,ep,en,ed,sf,ef=_span_values(sample.source_span)
        self.conn.execute('INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(sample.id,sample.run_id,sample.asset_id,sample.purpose,sample.kind,sid,sp,sn,sd,ep,en,ed,sf,ef,sample.source_frame_index,sample.selection_reason,json.dumps(sample.artifact_ids))); self.conn.commit()
    def save_evidence(self, evidence: Evidence):
        sid,sp,sn,sd,ep,en,ed,sf,ef=_span_values(evidence.source_span)
        self.conn.execute('INSERT INTO evidences VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(evidence.id,evidence.run_id,evidence.kind,evidence.description,sid,sp,sn,sd,ep,en,ed,evidence.frame_start,evidence.frame_end,json.dumps(evidence.numeric_measurement) if evidence.numeric_measurement is not None else None,evidence.external_artifact_ref,evidence.artifact_hash,json.dumps(evidence.metadata))); self.conn.commit()
    def save_observation(self, observation: Observation):
        self.conn.execute('INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?)',(observation.id,observation.run_id,observation.target_type,observation.target_id,observation.feature,json.dumps(observation.value),observation.value_status,observation.confidence,observation.confidence_kind,observation.coverage,observation.producer_ref))
        self.conn.executemany('INSERT INTO observation_evidence(observation_id,evidence_id) VALUES (?,?)',[(observation.id,e) for e in observation.evidence_ids]); self.conn.commit()
    def get_observation(self, observation_id: str) -> Observation:
        row=self.conn.execute('SELECT id,run_id,target_type,target_id,feature,value_json,value_status,confidence,confidence_kind,coverage,producer_ref FROM observations WHERE id=?',(observation_id,)).fetchone()
        if row is None: raise KeyError(observation_id)
        ev=tuple(r[0] for r in self.conn.execute('SELECT evidence_id FROM observation_evidence WHERE observation_id=? ORDER BY evidence_id',(observation_id,)))
        return Observation(row[0],row[1],row[2],row[3],row[4],json.loads(row[5]),row[6],row[7],row[8],row[9],ev,row[10])



