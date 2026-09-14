import pytest

from aei.benchmark import EvaluationBasisIdentityValidator, RevisionIdentityValidator
from aei.domain.benchmark import EvaluationBasisIdentity, RevisionIdentity


def test_complete_revision_identity():
    identity = RevisionIdentity("p", "m", "c", "code", ("run",), "input:f")
    assert RevisionIdentityValidator.validate(identity) == "COMPLETE"


@pytest.mark.parametrize("identity, status", [(RevisionIdentity(), "MISSING"), (RevisionIdentity(producer_ref="p"), "INCOMPLETE")])
def test_missing_or_incomplete_revision_identity(identity, status):
    assert RevisionIdentityValidator.validate(identity) == status


def test_revision_identity_rejects_invalid_fingerprint():
    with pytest.raises(ValueError):
        RevisionIdentity("p", "m", "c", "code", (), "")
        RevisionIdentityValidator.validate(RevisionIdentity("p", "m", "c", "code", (), ""))


def test_evaluation_basis_identity_validation():
    EvaluationBasisIdentityValidator.validate(EvaluationBasisIdentity("ds:f", "d1", "ann:f", "a1", "cases:f", "task", "feature", "tax"))
