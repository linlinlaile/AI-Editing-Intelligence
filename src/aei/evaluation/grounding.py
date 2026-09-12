"""Evidence relationship and provenance evaluation."""
from __future__ import annotations

from aei.domain.evaluation import EvaluationFinding, EvaluationInput, EvaluationResult, EvaluationStatus


class EvidenceGroundingEvaluator:
    name = "evidence-grounding"
    version = "v1"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        observation = input.observation
        findings: list[EvaluationFinding] = []
        by_id = {e.id: e for e in input.evidences}
        referenced_ids = tuple(getattr(observation, "evidence_ids", ()) or ())

        missing = [eid for eid in referenced_ids if eid not in by_id]
        if missing:
            findings.append(EvaluationFinding(
                "missing_evidence_reference",
                "Observation references Evidence IDs absent from the evaluation input",
                {"evidence_ids": missing},
            ))

        if not referenced_ids:
            findings.append(EvaluationFinding(
                "invalid_evidence_relation",
                "Observation must reference at least one Evidence in the evaluation input",
            ))

        # Only referenced evidence participates in relation and provenance checks.
        referenced = [by_id[eid] for eid in referenced_ids if eid in by_id]
        run_id = getattr(observation, "run_id", None)
        metadata_run_id = input.analysis_run_metadata.get("run_id")
        for evidence in referenced:
            if evidence.run_id != run_id or (metadata_run_id is not None and evidence.run_id != metadata_run_id):
                findings.append(EvaluationFinding(
                    "provenance_mismatch",
                    "Observation, Evidence and AnalysisRun metadata must share run_id",
                    {"observation_run_id": run_id, "evidence_id": evidence.id, "evidence_run_id": evidence.run_id, "analysis_run_id": metadata_run_id},
                ))

        if metadata_run_id is not None and metadata_run_id != run_id:
            findings.append(EvaluationFinding(
                "provenance_mismatch",
                "Observation and AnalysisRun metadata must share run_id",
                {"observation_run_id": run_id, "analysis_run_id": metadata_run_id},
            ))

        untraceable = [e.id for e in referenced if not any((e.source_span, e.frame_start is not None, e.numeric_measurement, e.external_artifact_ref, e.artifact_hash))]
        status = EvaluationStatus.FAIL if findings else EvaluationStatus.PASS
        if not findings and untraceable:
            findings.extend(EvaluationFinding("untraceable_evidence", "Evidence has no source, artifact or measurable provenance", {"evidence_ids": untraceable}) for _ in [0])
            status = EvaluationStatus.NOT_EVALUABLE

        return EvaluationResult(
            id=f"evaluation:{getattr(observation, 'id', 'unknown')}:{self.version}:grounding",
            observation_id=getattr(observation, "id", "unknown") or "unknown",
            evaluation_run_id=input.evaluation_run_id or run_id or "unknown",
            evaluator_ref=f"{self.name}:{self.version}",
            evaluation_kind="evidence_grounding",
            status=status,
            findings=tuple(findings),
        )


__all__ = ["EvidenceGroundingEvaluator"]
