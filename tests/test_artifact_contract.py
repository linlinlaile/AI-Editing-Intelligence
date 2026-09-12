import pytest
from aei.domain.models import Artifact, Rational, TimePoint

def test_artifact_contract_is_fixed_and_portable():
    point=TimePoint('s',9000,Rational(1001,30000),4)
    a=Artifact('a','r','asset','sample','frame_image','image/png','artifacts/a.png','abc',3,point,2,2)
    assert a.source_point.pts == 9000
    with pytest.raises(ValueError):
        Artifact('a','r','asset','sample','frame_image','image/png','C:/a.png','abc',3,point,2,2)
