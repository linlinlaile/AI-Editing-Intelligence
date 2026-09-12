import json
import sqlite3
from pathlib import Path

import pytest

from aei.adapters.repository import SemanticTimelineRepository
from aei.adapters.shot_detection import ShotBoundary, persist_shots
from aei.domain.models import AnalysisRun, MediaAsset, MediaStream, Rational
from aei.storage.migrations import migrate

FIXTURES = Path(__file__).parent / "fixtures"


def _stream(name):
    raw = json.loads((FIXTURES / name).read_text())
    s = raw["streams"][0]
    return MediaStream(
        "asset:stream:0", "asset", s["index"], s["codec_type"], s.get("codec_name"),
        Rational(*map(int, s["time_base"].split("/"))), s.get("start_pts"),
        s.get("duration_ts"), average_frame_rate=(
            Rational(*map(int, s["avg_frame_rate"].split("/")))
            if s.get("avg_frame_rate") not in (None, "0/0") else None
        ), nominal_frame_rate=Rational(*map(int, s["r_frame_rate"].split("/"))),
    )


@pytest.mark.parametrize("fixture", ["probe-cfr.json", "probe-vfr.json", "probe-nonzero-pts.json", "probe-bframe.json"])
def test_fixture_probe_preserves_time_model(fixture):
    stream = _stream(fixture)
    assert stream.time_base.denominator > 0
    assert stream.start_pts is not None
    if fixture == "probe-cfr.json":
        assert stream.average_frame_rate == Rational(30, 1)
    if fixture == "probe-vfr.json":
        assert stream.average_frame_rate is None
    if fixture == "probe-nonzero-pts.json":
        assert stream.start_pts == 5000
    if fixture == "probe-bframe.json":
        assert json.loads((FIXTURES / fixture).read_text())["streams"][0]["has_b_frames"] == 2


def _persist(stream, boundaries):
    c = sqlite3.connect(":memory:"); migrate(c)
    c.execute("insert into media_assets values ('asset','file:///asset',1,'fp','matroska')")
    c.execute("insert into media_streams(id,asset_id,stream_index,kind,codec,tb_num,tb_den,start_pts,duration_pts) values (?,?,?,?,?,?,?,?,?)",
              (stream.id, "asset", 0, "video", stream.codec, stream.time_base.numerator, stream.time_base.denominator, stream.start_pts, stream.duration_pts))
    repo = SemanticTimelineRepository(c)
    return repo, persist_shots(type("D", (), {"name": "fixture", "version": "1", "config": {}, "detect": lambda self, a, s: boundaries})(), MediaAsset("asset", "file:///asset", 1, "fp"), stream, AnalysisRun("run", "asset", "fixture"), repo)


def test_shot_ordering_non_overlap_and_round_trip():
    stream = _stream("probe-vfr.json")
    boundaries = [ShotBoundary(0, 40, 0, 2), ShotBoundary(40, 105, 2, 5), ShotBoundary(105, 200, 5, 9)]
    repo, segs = _persist(stream, boundaries)
    stored = repo.get_segments("run:shots")
    assert [s.span.start.pts for s in stored] == [0, 40, 105]
    assert all(a.span.end.pts <= b.span.start.pts for a, b in zip(stored, stored[1:]))
    assert [(s.span.start.presentation_frame_index, s.span.end.presentation_frame_index) for s in stored] == [(0, 2), (2, 5), (5, 9)]
    assert all(s.span.start.time_base == stream.time_base for s in stored)


@pytest.mark.parametrize("boundaries", [
    [ShotBoundary(0, 10, 0, 3), ShotBoundary(9, 20, 3, 6)],
    [ShotBoundary(0, 10, 3, 2)],
    [ShotBoundary(0, 10, 0, 3), ShotBoundary(10, 20, 2, 5)],
])
def test_shot_contract_rejects_overlap_or_inconsistent_frame_indices(boundaries):
    with pytest.raises(ValueError, match="ordered"):
        _persist(_stream("probe-cfr.json"), boundaries)
