"""Contract tests against actual locally encoded media files.

These tests intentionally exercise the complete boundary rather than mocks:
PyAV writes a file, ingest reads its stream metadata, and the locator decodes
presentation order back into canonical PTS/timebase TimePoints.
"""
from fractions import Fraction

import pytest

av = pytest.importorskip("av", reason="real media contract tests require PyAV")

from aei.adapters.media import PyAVFrameLocator
from aei.domain.models import MediaStream, Rational


def _write_video(path, pts, *, codec="mpeg4", bframes=False):
    container = av.open(str(path), mode="w", format="matroska")
    stream = container.add_stream(codec, rate=30)
    stream.width = 16
    stream.height = 16
    stream.pix_fmt = "yuv420p"
    stream.time_base = Fraction(1, 1000)
    if bframes:
        # MPEG-4 encoders available in minimal CI images support this option.
        stream.codec_context.max_b_frames = 2
    try:
        for value in pts:
            frame = av.VideoFrame(stream.width, stream.height, "rgb24")
            frame.pts = value
            frame.time_base = stream.time_base
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    finally:
        container.close()


def _decoded_pts(path, stream_index):
    container = av.open(str(path))
    try:
        stream = next(s for s in container.streams if s.index == stream_index)
        return [int(frame.pts) for frame in container.decode(stream)]
    finally:
        container.close()


def _stream_contract(path):
    container = av.open(str(path))
    try:
        stream = next(s for s in container.streams if s.type == "video")
        return MediaStream(
            "asset:stream:0", "asset", stream.index, "video", stream.codec_context.name,
            Rational(stream.time_base.numerator, stream.time_base.denominator),
            stream.start_time, stream.duration, stream.width, stream.height,
        )
    finally:
        container.close()


@pytest.mark.parametrize(
    "name, source_pts",
    [
        ("cfr", [0, 33, 66, 99, 132]),
        ("vfr", [0, 17, 83, 141, 260]),
        ("nonzero", [9000, 9033, 9066, 9099]),
    ],
)
def test_real_media_locator_preserves_presentation_pts_and_rational_timebase(tmp_path, name, source_pts):
    path = tmp_path / f"{name}.mkv"
    _write_video(path, source_pts)
    stream = _stream_contract(path)
    decoded = _decoded_pts(path, stream.index)
    if name == "nonzero":
        assert decoded[0] != 0
    if name == "vfr":
        assert len(set(b - a for a, b in zip(decoded, decoded[1:]))) > 1
    locator = PyAVFrameLocator(path)

    points = [locator.locate_presentation_frame(stream, i) for i in range(len(decoded))]
    assert [p.pts for p in points] == decoded
    assert [p.presentation_frame_index for p in points] == list(range(len(decoded)))
    assert all(p.stream_id == stream.id and p.time_base == stream.time_base for p in points)
    assert [p.pts * p.time_base.as_fraction() for p in points] == [p * stream.time_base.as_fraction() for p in decoded]
    with pytest.raises(IndexError):
        locator.locate_presentation_frame(stream, len(decoded))


def test_real_media_locator_rejects_non_video_stream(tmp_path):
    path = tmp_path / "video.mkv"
    _write_video(path, [0, 40])
    stream = _stream_contract(path)
    audio_like = MediaStream("asset:stream:1", "asset", 1, "audio", "pcm_s16le", stream.time_base, None, None)
    with pytest.raises(ValueError, match="video stream"):
        PyAVFrameLocator(path).locate_presentation_frame(audio_like, 0)


def test_real_media_locator_uses_presentation_order_for_b_frame_stream(tmp_path):
    path = tmp_path / "bframes.mkv"
    _write_video(path, [0, 33, 66, 99, 132, 165], bframes=True)
    stream = _stream_contract(path)
    decoded = _decoded_pts(path, stream.index)
    locator = PyAVFrameLocator(path)
    located = [locator.locate_presentation_frame(stream, i).pts for i in range(len(decoded))]
    # Decode order exposed by PyAV is presentation order, including when the
    # codec internally uses B-frames and packet DTS differs from frame PTS.
    assert located == decoded
    assert located == sorted(located)
