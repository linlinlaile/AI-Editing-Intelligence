from aei.domain.evaluation import EvaluationInput, EvaluationStatus
from aei.domain.models import Evidence, Observation, ObservationStatus
from aei.evaluation.grounding import EvidenceGroundingEvaluator

def obs(ids=("e",), run="r"):
    return Observation("o", run, "artifact", "a", "f", "x", ObservationStatus.SUCCESS, evidence_ids=ids, producer_ref="p")
def test_pass():
    e=Evidence("e","r","frame",frame_start=1,frame_end=1)
    assert EvidenceGroundingEvaluator().evaluate(EvaluationInput(obs(),(e,),"er",{"run_id":"r"})).status is EvaluationStatus.PASS
def test_missing():
    r=EvidenceGroundingEvaluator().evaluate(EvaluationInput(obs(),(),"er",{"run_id":"r"}))
    assert r.status is EvaluationStatus.FAIL and r.findings[0].code=="missing_evidence_reference"
def test_mismatch():
    e=Evidence("e","x","frame",frame_start=1,frame_end=1)
    r=EvidenceGroundingEvaluator().evaluate(EvaluationInput(obs(),(e,),"er",{"run_id":"r"}))
    assert r.status is EvaluationStatus.FAIL and any(f.code=="provenance_mismatch" for f in r.findings)
