"""Phase 5.4 aggregation contracts and deterministic pure aggregation.

Counts, class assignments, disagreements and statuses are supplied by callers.
Validation checks their representation, never derives an analysis result.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json

from aei.domain.models import Evidence, Observation, ObservationStatus, Rational, Sample, TemporalSegment, TimePoint


__all__ = [
    "FEATURE", "SCHEMA_VERSION", "MissingInputReason", "MissingInput", "AggregationInput",
    "ClassDistributionEntry", "SampledClassificationSummary", "ShotObservationDraft",
    "ObservationSource", "AggregationEvidenceDraft", "AggregationMetadata", "AggregationResult",
    "aggregate_shot_observations", "aggregate_classifications", "aggregate_shot_classification",
    "generate_shot_observation_evidence", "materialize_shot_observation",
]


FEATURE = "vision.sampled_classification_summary"
SCHEMA_VERSION = "1.0"


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _count(value: int, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _tuple_of(values: tuple, item_type: type, name: str) -> None:
    if not isinstance(values, tuple) or any(not isinstance(v, item_type) for v in values):
        raise ValueError(f"{name} must be a tuple of {item_type.__name__}")


def _unique(values: tuple, name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must be unique")


def _ids(values: tuple[str, ...], name: str) -> None:
    _tuple_of(values, str, name)
    for value in values:
        _text(value, name)
    _unique(values, name)


class MissingInputReason(str, Enum):
    ARTIFACT_MISSING = "artifact_missing"
    OBSERVATION_MISSING = "observation_missing"
    FAILED = "failed"
    UNKNOWN = "unknown"
    NOT_COVERED = "not_covered"


@dataclass(frozen=True)
class MissingInput:
    sample_id: str
    reason: MissingInputReason
    artifact_ids: tuple[str, ...] = ()
    detail: str = ""

    def __post_init__(self) -> None:
        _text(self.sample_id, "sample_id")
        if not isinstance(self.reason, MissingInputReason):
            raise ValueError("reason must be a MissingInputReason")
        _ids(self.artifact_ids, "artifact_ids")
        if not isinstance(self.detail, str):
            raise ValueError("detail must be a string")


@dataclass(frozen=True)
class AggregationInput:
    shot: TemporalSegment
    samples: tuple[Sample, ...]
    artifact_observations: tuple[Observation, ...]
    evidences: tuple[Evidence, ...]
    missing_inputs: tuple[MissingInput, ...] = ()
    schema_version: str = field(default=SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.shot, TemporalSegment) or self.shot.kind != "shot":
            raise ValueError("shot must be a TemporalSegment of kind shot")
        _text(self.shot.id, "shot.id")
        _text(self.shot.layer_id, "shot.layer_id")
        for name, kind in (("samples", Sample), ("artifact_observations", Observation),
                           ("evidences", Evidence), ("missing_inputs", MissingInput)):
            _tuple_of(getattr(self, name), kind, name)
        for name in ("samples", "artifact_observations", "evidences"):
            _ids(tuple(item.id for item in getattr(self, name)), f"{name} IDs")
        for sample in self.samples:
            if sample.segment_id != self.shot.id:
                raise ValueError("sample must belong to the target shot")
        sample_ids = {s.id for s in self.samples}
        if any(m.sample_id not in sample_ids for m in self.missing_inputs):
            raise ValueError("missing input must reference an expected sample")
        by_id = {e.id: e for e in self.evidences}
        for observation in self.artifact_observations:
            if observation.target_type != "artifact" or observation.feature != "vision.classification":
                raise ValueError("input observations must be Artifact classifications")
            _text(observation.target_id, "observation.target_id")
            _text(observation.producer_ref, "observation.producer_ref")
            for evidence_id in observation.evidence_ids:
                if evidence_id not in by_id:
                    raise ValueError("observation references missing evidence")
                if by_id[evidence_id].run_id != observation.run_id:
                    raise ValueError("upstream observation and evidence run_id must match")
        # Reject opaque handles, bytes and non-finite JSON in supplied snapshots.
        try:
            json.dumps(asdict(self), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("aggregation snapshots must be finite JSON data") from exc


@dataclass(frozen=True)
class ClassDistributionEntry:
    class_id: int
    label: str
    sample_count: int
    sample_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _count(self.class_id, "class_id")
        _text(self.label, "label")
        _count(self.sample_count, "sample_count")
        _ids(self.sample_ids, "sample_ids")
        if not self.sample_count or self.sample_count != len(self.sample_ids):
            raise ValueError("class sample_count must equal its non-empty sample_ids count")


@dataclass(frozen=True)
class SampledClassificationSummary:
    taxonomy: str
    taxonomy_version: str
    analyzed_sample_count: int
    class_distribution: tuple[ClassDistributionEntry, ...]
    disagreements: tuple[int, ...]
    missing_inputs: tuple[MissingInput, ...]
    schema_version: str = field(default=SCHEMA_VERSION, init=False)
    scope: str = field(default="sampled_frames", init=False)

    def __post_init__(self) -> None:
        _text(self.taxonomy, "taxonomy")
        _text(self.taxonomy_version, "taxonomy_version")
        _count(self.analyzed_sample_count, "analyzed_sample_count")
        _tuple_of(self.class_distribution, ClassDistributionEntry, "class_distribution")
        _tuple_of(self.missing_inputs, MissingInput, "missing_inputs")
        _tuple_of(self.disagreements, int, "disagreements")
        for class_id in self.disagreements:
            _count(class_id, "disagreement class_id")
        _unique(self.disagreements, "disagreements")
        class_ids = tuple(entry.class_id for entry in self.class_distribution)
        _unique(class_ids, "class IDs")
        _unique(tuple(sid for entry in self.class_distribution for sid in entry.sample_ids), "support sample IDs")
        if sum(entry.sample_count for entry in self.class_distribution) != self.analyzed_sample_count:
            raise ValueError("class counts must sum to analyzed_sample_count")
        if (len(class_ids) > 1 and set(self.disagreements) != set(class_ids)) or (
                len(class_ids) <= 1 and self.disagreements):
            raise ValueError("disagreements must list all competing classes, or be empty for consensus")

    def to_value(self) -> dict:
        """Encode the provided feature data; do not aggregate or create an Observation."""
        return json.loads(json.dumps(asdict(self), allow_nan=False))


@dataclass(frozen=True)
class ShotObservationDraft:
    target_id: str
    value: SampledClassificationSummary
    value_status: ObservationStatus
    target_type: str = field(default="segment", init=False)
    feature: str = field(default=FEATURE, init=False)
    confidence: None = field(default=None, init=False)
    confidence_kind: None = field(default=None, init=False)
    coverage: None = field(default=None, init=False)

    def __post_init__(self) -> None:
        _text(self.target_id, "target_id")
        if not isinstance(self.value, SampledClassificationSummary):
            raise ValueError("value must be a SampledClassificationSummary")
        if not isinstance(self.value_status, ObservationStatus):
            raise ValueError("value_status must be an ObservationStatus")


@dataclass(frozen=True)
class ObservationSource:
    observation_id: str
    evidence_id: str
    run_id: str
    sample_id: str
    artifact_id: str
    artifact_uri: str
    artifact_hash: str
    source_point: TimePoint

    def __post_init__(self) -> None:
        for name in ("observation_id", "evidence_id", "run_id", "sample_id", "artifact_id",
                     "artifact_uri", "artifact_hash"):
            _text(getattr(self, name), name)
        if not isinstance(self.source_point, TimePoint):
            raise ValueError("source_point must be a TimePoint")
        point = self.source_point
        _text(point.stream_id, "source stream_id")
        if type(point.pts) is not int:
            raise ValueError("source PTS must be an integer")
        if (type(point.time_base.numerator) is not int or type(point.time_base.denominator) is not int
                or point.time_base.numerator <= 0 or point.time_base.denominator <= 0):
            raise ValueError("source timebase must be positive integer rational")
        if point.presentation_frame_index is not None:
            _count(point.presentation_frame_index, "presentation_frame_index")


@dataclass(frozen=True)
class AggregationEvidenceDraft:
    sources: tuple[ObservationSource, ...]
    missing_inputs: tuple[MissingInput, ...]
    kind: str = field(default="shot_visual_observation_aggregation", init=False)

    def __post_init__(self) -> None:
        _tuple_of(self.sources, ObservationSource, "sources")
        _tuple_of(self.missing_inputs, MissingInput, "missing_inputs")
        _unique(self.sources, "source records")


@dataclass(frozen=True)
class AggregationMetadata:
    producer_ref: str
    rule_name: str
    rule_version: str
    config_hash: str
    parent_run_ids: tuple[str, ...]
    expected_sample_count: int
    analyzed_sample_count: int
    schema_version: str = field(default=SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        for name in ("producer_ref", "rule_name", "rule_version", "config_hash"):
            _text(getattr(self, name), name)
        _ids(self.parent_run_ids, "parent_run_ids")
        _count(self.expected_sample_count, "expected_sample_count")
        _count(self.analyzed_sample_count, "analyzed_sample_count")
        if self.analyzed_sample_count > self.expected_sample_count:
            raise ValueError("analyzed count cannot exceed expected count")


@dataclass(frozen=True)
class AggregationResult:
    observation: ShotObservationDraft
    evidence: AggregationEvidenceDraft
    metadata: AggregationMetadata
    schema_version: str = field(default=SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        for name, kind in (("observation", ShotObservationDraft),
                           ("evidence", AggregationEvidenceDraft), ("metadata", AggregationMetadata)):
            if not isinstance(getattr(self, name), kind):
                raise ValueError(f"{name} must be a {kind.__name__}")
        value = self.observation.value
        if value.analyzed_sample_count != self.metadata.analyzed_sample_count:
            raise ValueError("summary and metadata analyzed counts must match")
        if value.missing_inputs != self.evidence.missing_inputs:
            raise ValueError("summary and evidence missing inputs must match")
        if any(source.run_id not in self.metadata.parent_run_ids for source in self.evidence.sources):
            raise ValueError("source run must be listed in parent_run_ids")
        supported_ids = {source.sample_id for source in self.evidence.sources}
        if any(sid not in supported_ids for entry in value.class_distribution for sid in entry.sample_ids):
            raise ValueError("every class support sample must have source evidence")


def aggregate_shot_observations(
    input: AggregationInput,
    *,
    taxonomy: str | None = None,
    taxonomy_version: str = "1",
    producer_ref: str | None = None,
    model_revision: str | None = None,
    preprocess_version: str | None = None,
    rule_name: str = "shot_visual_observation_aggregation",
    rule_version: str = "1",
    config_hash: str = "sha256:default",
) -> AggregationResult:
    """Aggregate artifact classifications into a shot draft.

    All identity and source information is read from the supplied snapshot and
    evidence metadata.  This function has no repository, media or model
    dependencies and is therefore deterministic and straightforward to
    recompute.
    """
    if not isinstance(input, AggregationInput):
        raise TypeError("input must be an AggregationInput")
    samples = {s.id: s for s in input.samples}
    evidences = {e.id: e for e in input.evidences}
    missing_by_sample = {m.sample_id: m for m in input.missing_inputs}
    if len(missing_by_sample) != len(input.missing_inputs):
        raise ValueError("missing inputs must reference unique samples")

    records = []
    seen_points = set()
    model_revisions = set()
    preprocess_versions = set()
    inferred_taxonomy = taxonomy
    inferred_producer = producer_ref
    for obs in input.artifact_observations:
        if obs.value_status is not ObservationStatus.SUCCESS:
            raise ValueError("non-success artifact observations must be represented as missing inputs")
        if producer_ref is not None and obs.producer_ref != producer_ref:
            raise ValueError("producer provenance mismatch")
        if inferred_producer is None:
            inferred_producer = obs.producer_ref
        if not isinstance(obs.value, dict) or type(obs.value.get("class_id")) is not int or not isinstance(obs.value.get("label"), str):
            raise ValueError("classification observation must contain class_id and label")
        value_taxonomy = obs.value.get("taxonomy")
        if inferred_taxonomy is None:
            inferred_taxonomy = value_taxonomy
        if value_taxonomy is not None and value_taxonomy != inferred_taxonomy:
            raise ValueError("taxonomy mismatch")
        if taxonomy is not None and value_taxonomy != taxonomy:
            raise ValueError("taxonomy mismatch")
        if len(obs.evidence_ids) != 1:
            raise ValueError("classification observation must reference one evidence")
        ev = evidences[obs.evidence_ids[0]]
        meta = ev.metadata
        sample_id = meta.get("sample_id")
        artifact_id = meta.get("artifact_id")
        point = meta.get("source_point")
        if sample_id not in samples or not artifact_id or not isinstance(point, dict):
            raise ValueError("observation provenance is incomplete")
        sample = samples[sample_id]
        if sample.segment_id != input.shot.id or obs.target_id != artifact_id:
            raise ValueError("sample does not belong to target shot")
        if ev.run_id != obs.run_id:
            raise ValueError("upstream observation and evidence run_id must match")
        if meta.get("producer_ref") not in (None, obs.producer_ref):
            raise ValueError("producer provenance mismatch")
        if meta.get("model_revision") is not None:
            model_revisions.add(meta["model_revision"])
        if meta.get("preprocess_version", meta.get("preprocessing")) is not None:
            preprocess_versions.add(meta.get("preprocess_version", meta.get("preprocessing")))
        # Source point is compared by canonical stream/PTS/timebase/frame data.
        try:
            source = TimePoint(point["stream_id"], int(point["pts"]),
                               Rational(int(point["time_base"]["numerator"]), int(point["time_base"]["denominator"])),
                               point.get("presentation_frame_index"))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid source point provenance") from exc
        key = (source.stream_id, source.pts, source.time_base, source.presentation_frame_index)
        if sample.source_span is not None and sample.source_span.start != source:
            raise ValueError("sample and artifact source point mismatch")
        if sample.source_frame_index is not None and source.presentation_frame_index != sample.source_frame_index:
            raise ValueError("sample and artifact frame mismatch")
        if key in seen_points:
            continue
        seen_points.add(key)
        records.append((obs, ev, sample, source, artifact_id, meta))

    if not inferred_taxonomy or not inferred_producer:
        raise ValueError("taxonomy and producer provenance are required")
    if len(model_revisions) > 1 or len(preprocess_versions) > 1:
        raise ValueError("model or preprocess version mismatch")
    # Optional compatibility fields are deliberately strict when requested.
    for _, _, _, _, _, meta in records:
        if model_revision is not None and meta.get("model_revision") != model_revision:
            raise ValueError("model revision mismatch")
        if preprocess_version is not None and meta.get("preprocess_version", meta.get("preprocessing")) != preprocess_version:
            raise ValueError("preprocess version mismatch")
        if meta.get("taxonomy_version") not in (None, taxonomy_version):
            raise ValueError("taxonomy version mismatch")

    classes = {}
    sources = []
    parent_runs = []
    for obs, ev, sample, source, artifact_id, meta in records:
        cid = obs.value["class_id"]
        classes.setdefault(cid, {"label": obs.value["label"], "sample_ids": []})["sample_ids"].append(sample.id)
        uri = ev.external_artifact_ref or meta.get("artifact_uri") or "unknown"
        ahash = ev.artifact_hash or meta.get("artifact_hash") or "unknown"
        sources.append(ObservationSource(obs.id, ev.id, obs.run_id, sample.id, artifact_id, uri, ahash, source))
        if obs.run_id not in parent_runs:
            parent_runs.append(obs.run_id)
    entries = tuple(ClassDistributionEntry(cid, classes[cid]["label"], len(classes[cid]["sample_ids"]), tuple(classes[cid]["sample_ids"])) for cid in sorted(classes))
    disagreements = tuple(sorted(classes)) if len(classes) > 1 else ()
    analyzed = len(records)
    if analyzed == 0:
        status = ObservationStatus.FAILED if any(m.reason is MissingInputReason.FAILED for m in input.missing_inputs) else (ObservationStatus.UNKNOWN if any(m.reason is MissingInputReason.UNKNOWN for m in input.missing_inputs) else ObservationStatus.NOT_COVERED)
    elif input.missing_inputs:
        status = ObservationStatus.PARTIAL
    else:
        status = ObservationStatus.SUCCESS
    summary = SampledClassificationSummary(inferred_taxonomy, taxonomy_version, analyzed, entries, disagreements, input.missing_inputs)
    result = AggregationResult(
        ShotObservationDraft(input.shot.id, summary, status),
        AggregationEvidenceDraft(tuple(sources), input.missing_inputs),
        AggregationMetadata(inferred_producer, rule_name, rule_version, config_hash, tuple(parent_runs), len(input.samples), analyzed),
    )
    return result


aggregate_classifications = aggregate_shot_observations
aggregate_shot_classification = aggregate_shot_observations


def generate_shot_observation_evidence(
    result: AggregationResult,
    *,
    aggregation_run_id: str,
    observation_id: str,
    evidence_id: str,
) -> tuple[Observation, Evidence]:
    """Materialize an aggregation draft as a new Observation and Evidence.

    This is deliberately a pure conversion: it does not persist anything and
    never mutates or reuses upstream Evidence.  IDs are supplied by the
    application layer so this function cannot invent run identity.
    """
    if not isinstance(result, AggregationResult):
        raise TypeError("result must be an AggregationResult")
    for value, name in ((aggregation_run_id, "aggregation_run_id"),
                        (observation_id, "observation_id"),
                        (evidence_id, "evidence_id")):
        _text(value, name)
    if observation_id == evidence_id:
        raise ValueError("observation and evidence IDs must differ")

    draft = result.observation
    sources = result.evidence.sources
    summary = draft.value.to_value()
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "aggregation_rule": {
            "name": result.metadata.rule_name,
            "version": result.metadata.rule_version,
            "producer_ref": result.metadata.producer_ref,
            "config_hash": result.metadata.config_hash,
        },
        "upstream_observation_ids": [s.observation_id for s in sources],
        "upstream_evidence_ids": [s.evidence_id for s in sources],
        "upstream_run_ids": list(result.metadata.parent_run_ids),
        "artifact_references": [
            {"artifact_id": s.artifact_id, "uri": s.artifact_uri,
             "hash": s.artifact_hash, "sample_id": s.sample_id,
             "source_point": {"stream_id": s.source_point.stream_id,
                              "pts": s.source_point.pts,
                              "time_base": {"numerator": s.source_point.time_base.numerator,
                                             "denominator": s.source_point.time_base.denominator},
                              "presentation_frame_index": s.source_point.presentation_frame_index}}
            for s in sources
        ],
        "classification_statistics": {
            "taxonomy": summary["taxonomy"],
            "taxonomy_version": summary["taxonomy_version"],
            "analyzed_sample_count": result.metadata.analyzed_sample_count,
            "expected_sample_count": result.metadata.expected_sample_count,
            "class_distribution": summary["class_distribution"],
            "disagreements": summary["disagreements"],
        },
        "missing_inputs": [
            {"sample_id": m.sample_id, "reason": m.reason.value,
             "artifact_ids": list(m.artifact_ids), "detail": m.detail}
            for m in result.evidence.missing_inputs
        ],
    }
    # Evidence needs a supported reference; the numeric measurement carries
    # aggregate counts while metadata carries the complete provenance.
    evidence = Evidence(
        evidence_id, aggregation_run_id, result.evidence.kind,
        description="shot classification aggregation",
        numeric_measurement={"analyzed_sample_count": result.metadata.analyzed_sample_count,
                             "expected_sample_count": result.metadata.expected_sample_count},
        metadata=metadata,
    )
    observation = Observation(
        observation_id, aggregation_run_id, draft.target_type, draft.target_id,
        draft.feature, summary, value_status=draft.value_status,
        confidence=None, coverage=None, evidence_ids=(evidence.id,),
        producer_ref=result.metadata.producer_ref,
    )
    return observation, evidence


materialize_shot_observation = generate_shot_observation_evidence
