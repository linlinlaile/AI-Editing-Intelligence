import hashlib
import sqlite3
from PIL import Image
from aei.adapters.artifact_payload import LocalArtifactPayloadLoader
from aei.adapters.vision.analyzer import VisionAnalyzer
from aei.application.shot_observation import ShotAnalysisRequest, ShotObservationAggregationUseCase
from aei.domain.models import Artifact, Rational, Sample, TemporalSegment, TimePoint, TimeSpan
from aei.domain.models import AnalysisRun, Evidence, Observation, ObservationStatus
from aei.adapters.repository import SemanticTimelineRepository
from aei.storage.migrations import migrate
from aei.ports.analyzer import AnalyzerContext
from aei.ports.vision_model import Prediction


def test_shot_orchestration_aggregates_multiple_artifacts_and_materializes(tmp_path):
    samples=[]; artifacts=[]
    for i, color in enumerate(((255,0,0),(0,255,0))):
        rel=f"artifacts/{i}.png"; path=tmp_path/rel; path.parent.mkdir(exist_ok=True)
        Image.new("RGB", (2,2), color).save(path)
        point=TimePoint("v", 100+i, Rational(1,100), i)
        sid=f"s{i}"; aid=f"a{i}"
        samples.append(Sample(sid, "sampling", "asset", "representative", "frame", TimeSpan(point,point), i, segment_id="shot", artifact_ids=(aid,)))
        artifacts.append(Artifact(aid, "vision", "asset", sid, "frame_image", "image/png", rel, hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size, point, 2, 2))
    shot=TemporalSegment("shot", "layer", "shot", TimeSpan(TimePoint("v",100,Rational(1,100),0), TimePoint("v",102,Rational(1,100),2)))
    class Model:
        producer_ref="vision:test@1"; taxonomy="test"
        def predict(self, data): return Prediction("red", 1, .9) if b"" else Prediction("x", 1, .9)
    result=ShotObservationAggregationUseCase(VisionAnalyzer({a.id:a for a in artifacts}, LocalArtifactPayloadLoader(tmp_path), Model())).execute(ShotAnalysisRequest(shot,tuple(samples),tuple(artifacts),AnalyzerContext("vision","vision:test@1"),"agg","so","se","test"))
    assert result.observation.target_id == "shot"
    assert result.observation.evidence_ids == ("se",)
    assert result.evidence.run_id == "agg"
    assert result.observation.value["analyzed_sample_count"] == 2
    assert result.evidence.metadata["upstream_observation_ids"]


def test_shot_orchestration_failure_and_missing_artifact_are_partial(tmp_path):
    p=tmp_path/"f.png"; p.parent.mkdir(exist_ok=True); Image.new("RGB",(2,2),(1,2,3)).save(p)
    pt=TimePoint("v",10,Rational(1,100),0)
    s0=Sample("s0","sampling","asset","representative","frame",TimeSpan(pt,pt),0,segment_id="shot",artifact_ids=("a0",))
    s1=Sample("s1","sampling","asset","representative","frame",TimeSpan(pt,pt),1,segment_id="shot",artifact_ids=("missing",))
    a=Artifact("a0","vision","asset","s0","frame_image","image/png","f.png",hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_size,pt,2,2)
    shot=TemporalSegment("shot","layer","shot",TimeSpan(pt,TimePoint("v",11,Rational(1,100),1)))
    class Bad:
        producer_ref="vision:test@1"; taxonomy="test"
        def predict(self,data): raise RuntimeError("boom")
    result=ShotObservationAggregationUseCase(VisionAnalyzer({"a0":a},LocalArtifactPayloadLoader(tmp_path),Bad())).execute(ShotAnalysisRequest(shot,(s0,s1),(a,),AnalyzerContext("vision","vision:test@1"),"agg","so","se","test"))
    assert len(result.failed_inputs)==2
    assert result.observation.value_status.value == "FAILED"
    assert result.observation.evidence_ids == ("se",)


def test_execute_and_persist_creates_new_run_and_preserves_upstream(tmp_path):
    pt=TimePoint("v",10,Rational(1,100),0)
    sample=Sample("s0","sampling","asset","representative","frame",TimeSpan(pt,pt),0,segment_id="shot",artifact_ids=("a0",))
    artifact=Artifact("a0","vision","asset","s0","frame_image","image/png","frame.png","h",1,pt,1,1)
    shot=TemporalSegment("shot","layer","shot",TimeSpan(pt,TimePoint("v",11,Rational(1,100),1)))
    class Analyzer:
        name="vision"; version="1"
        def analyze(self, inp, ctx):
            ev=Evidence("up-e",ctx.analysis_run_id,"artifact_classification_input",external_artifact_ref="frame.png",artifact_hash="h",metadata={"sample_id":"s0","artifact_id":"a0","source_point":{"stream_id":"v","pts":10,"time_base":{"numerator":1,"denominator":100},"presentation_frame_index":0},"producer_ref":ctx.producer_ref})
            ob=Observation("up-o",ctx.analysis_run_id,"artifact","a0","vision.classification",{"label":"x","class_id":1,"taxonomy":"tax"},evidence_ids=(ev.id,),producer_ref=ctx.producer_ref)
            from aei.ports.analyzer import AnalysisResult
            return AnalysisResult((ob,),(ev,))
    req=ShotAnalysisRequest(shot,(sample,),(artifact,),AnalyzerContext("vision-run","vision:test"),"agg-1","so-1","se-1","tax")
    conn=sqlite3.connect(":memory:"); migrate(conn); conn.execute("insert into media_assets(id,uri,fingerprint) values ('asset','asset','fp')"); repo=SemanticTimelineRepository(conn)
    use=ShotObservationAggregationUseCase(Analyzer())
    use.execute_and_persist(req,AnalysisRun("agg-1","asset","shot-aggregation",parent_run_ids=("vision-run",)),repo)
    req2=ShotAnalysisRequest(shot,(sample,),(artifact,),AnalyzerContext("vision-run","vision:test"),"agg-2","so-2","se-2","tax")
    use.execute_and_persist(req2,AnalysisRun("agg-2","asset","shot-aggregation",parent_run_ids=("vision-run",)),repo)
    assert conn.execute("select count(*) from analysis_runs where id like 'agg-%'").fetchone()[0] == 2
    assert conn.execute("select count(*) from observations where target_type='segment'").fetchone()[0] == 2
    assert conn.execute("select count(*) from observation_evidence").fetchone()[0] == 2
    assert conn.execute("select count(*) from evidences where id='up-e'").fetchone()[0] == 0

