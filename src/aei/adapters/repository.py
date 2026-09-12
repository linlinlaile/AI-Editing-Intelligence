from __future__ import annotations
import json, sqlite3
from aei.domain.models import AnalysisRun, Sample, Artifact, Evidence, Observation, ObservationStatus, TemporalSegment, TimelineLayer, TimeSpan, TimePoint, Rational
_LEGACY_STATUS = {'observed': ObservationStatus.SUCCESS, 'failed': ObservationStatus.FAILED, 'unknown': ObservationStatus.UNKNOWN, 'not_applicable': ObservationStatus.NOT_COVERED}

def _span_values(span):
    if span is None: return (None, None, None, None, None, None, None, None, None)
    return (span.start.stream_id, span.start.pts, span.start.time_base.numerator, span.start.time_base.denominator, span.end.pts, span.end.time_base.numerator, span.end.time_base.denominator, span.start.presentation_frame_index, span.end.presentation_frame_index)

def _span(stream_id, start, end, sf, ef):
    if stream_id is None or start is None or end is None: return None
    return TimeSpan(TimePoint(stream_id, start, Rational(1, 1), sf), TimePoint(stream_id, end, Rational(1, 1), ef))

def _span_from_values(stream_id, start, start_num, start_den, end, end_num, end_den, sf, ef):
    if stream_id is None or start is None or end is None: return None
    return TimeSpan(TimePoint(stream_id, start, Rational(start_num or 1, start_den or 1), sf), TimePoint(stream_id, end, Rational(end_num or 1, end_den or 1), ef))

class SemanticTimelineRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    def save_analysis_run(self, run: AnalysisRun):
        self.conn.execute('INSERT INTO analysis_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (run.id,run.asset_id,run.producer_name,run.status,run.model_name,run.model_revision,run.code_revision,run.config_hash,json.dumps(run.input_artifact_ids),json.dumps(run.parent_run_ids),run.started_at,run.completed_at)); self.conn.commit()
    def save_layer(self, layer: TimelineLayer):
        self.conn.execute('INSERT INTO timeline_layers VALUES (?,?,?,?)',(layer.id,layer.asset_id,layer.kind,layer.detector_revision)); self.conn.commit()
    def save_segment(self, segment: TemporalSegment):
        s,e=segment.span.start,segment.span.end
        self.conn.execute('INSERT INTO temporal_segments(id,layer_id,kind,stream_id,tb_num,tb_den,start_pts,end_pts,start_frame_index,end_frame_index) VALUES (?,?,?,?,?,?,?,?,?,?)',(segment.id,segment.layer_id,segment.kind,s.stream_id,s.time_base.numerator,s.time_base.denominator,s.pts,e.pts,s.presentation_frame_index,e.presentation_frame_index)); self.conn.commit()
    def get_segments(self, layer_id: str):
        rows=self.conn.execute('SELECT id,layer_id,kind,stream_id,tb_num,tb_den,start_pts,end_pts,start_frame_index,end_frame_index FROM temporal_segments WHERE layer_id=? ORDER BY start_pts,id',(layer_id,)).fetchall()
        return [TemporalSegment(r[0],r[1],r[2],TimeSpan(TimePoint(r[3],r[6],Rational(r[4],r[5]),r[8]),TimePoint(r[3],r[7],Rational(r[4],r[5]),r[9]))) for r in rows]
    def save_sample(self, sample: Sample):
        sid,sp,sn,sd,ep,en,ed,sf,ef=_span_values(sample.source_span)
        self.conn.execute('INSERT INTO samples(id,run_id,asset_id,purpose,kind,stream_id,start_pts,start_tb_num,start_tb_den,end_pts,end_tb_num,end_tb_den,start_frame_index,end_frame_index,source_frame_index,selection_reason,artifact_ids_json,segment_id,sampling_method) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(sample.id,sample.run_id,sample.asset_id,sample.purpose,sample.kind,sid,sp,sn,sd,ep,en,ed,sf,ef,sample.source_frame_index,sample.selection_reason,json.dumps(sample.artifact_ids),sample.segment_id,sample.sampling_method)); self.conn.commit()
    def get_samples(self, run_id: str):
        rows=self.conn.execute('SELECT id,run_id,asset_id,purpose,kind,stream_id,start_pts,start_tb_num,start_tb_den,end_pts,end_tb_num,end_tb_den,start_frame_index,end_frame_index,source_frame_index,selection_reason,artifact_ids_json,segment_id,sampling_method FROM samples WHERE run_id=? ORDER BY COALESCE(start_pts,0),id',(run_id,)).fetchall()
        return [Sample(r[0],r[1],r[2],r[3],r[4],_span_from_values(r[5],r[6],r[7],r[8],r[9],r[10],r[11],r[12],r[13]),r[14],r[15],tuple(json.loads(r[16])),r[17],r[18]) for r in rows]
    def save_artifact(self, artifact: Artifact):
        p = artifact.source_point
        self.conn.execute('INSERT INTO artifacts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (artifact.id,artifact.run_id,artifact.asset_id,artifact.sample_id,artifact.kind,artifact.media_type,artifact.uri,artifact.content_hash,artifact.byte_size,p.stream_id,p.pts,p.time_base.numerator,p.time_base.denominator,p.presentation_frame_index,artifact.width,artifact.height))
        self.conn.commit()
    def get_artifact(self, artifact_id: str) -> Artifact:
        r=self.conn.execute('SELECT id,run_id,asset_id,sample_id,kind,media_type,uri,content_hash,byte_size,stream_id,source_pts,source_tb_num,source_tb_den,source_frame_index,width,height FROM artifacts WHERE id=?',(artifact_id,)).fetchone()
        if r is None: raise KeyError(artifact_id)
        return Artifact(r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],TimePoint(r[9],r[10],Rational(r[11],r[12]),r[13]),r[14],r[15])
    def get_artifacts_for_sample(self, sample_id: str):
        ids=[r[0] for r in self.conn.execute('SELECT id FROM artifacts WHERE sample_id=? ORDER BY id',(sample_id,))]
        return [self.get_artifact(i) for i in ids]
    def get_artifacts(self, run_id: str):
        ids=[r[0] for r in self.conn.execute('SELECT id FROM artifacts WHERE run_id=? ORDER BY id',(run_id,))]
        return [self.get_artifact(i) for i in ids]
    def save_evidence(self, evidence: Evidence):
        sid,sp,sn,sd,ep,en,ed,sf,ef=_span_values(evidence.source_span)
        self.conn.execute('INSERT INTO evidences VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(evidence.id,evidence.run_id,evidence.kind,evidence.description,sid,sp,sn,sd,ep,en,ed,evidence.frame_start,evidence.frame_end,json.dumps(evidence.numeric_measurement) if evidence.numeric_measurement is not None else None,evidence.external_artifact_ref,evidence.artifact_hash,json.dumps(evidence.metadata))); self.conn.commit()
    def save_observation(self, observation: Observation):
        self.conn.execute('INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?)',(observation.id,observation.run_id,observation.target_type,observation.target_id,observation.feature,json.dumps(observation.value),observation.value_status.value,observation.confidence,observation.confidence_kind,observation.coverage,observation.producer_ref))
        self.conn.executemany('INSERT INTO observation_evidence(observation_id,evidence_id) VALUES (?,?)',[(observation.id,e) for e in observation.evidence_ids]); self.conn.commit()
    def get_observation(self, observation_id: str) -> Observation:
        row=self.conn.execute('SELECT id,run_id,target_type,target_id,feature,value_json,value_status,confidence,confidence_kind,coverage,producer_ref FROM observations WHERE id=?',(observation_id,)).fetchone()
        if row is None: raise KeyError(observation_id)
        ev=tuple(r[0] for r in self.conn.execute('SELECT evidence_id FROM observation_evidence WHERE observation_id=? ORDER BY evidence_id',(observation_id,)))
        status = _LEGACY_STATUS[row[6]] if row[6] in _LEGACY_STATUS else ObservationStatus(row[6])
        return Observation(row[0],row[1],row[2],row[3],row[4],json.loads(row[5]),status,row[7],row[8],row[9],ev,row[10])
    def list_observations_by_run(self, run_id: str):
        return [self.get_observation(r[0]) for r in self.conn.execute('SELECT id FROM observations WHERE run_id=? ORDER BY id',(run_id,))]
    def list_observations_by_subject(self, target_type: str, target_id: str):
        return [self.get_observation(r[0]) for r in self.conn.execute('SELECT id FROM observations WHERE target_type=? AND target_id=? ORDER BY id',(target_type,target_id))]



