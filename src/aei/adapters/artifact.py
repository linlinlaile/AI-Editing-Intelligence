from __future__ import annotations
import hashlib
from pathlib import Path
from aei.domain.models import Artifact, MediaStream, Sample
from aei.ports.media import FrameLocator

class PyAVFrameArtifactExtractor:
    def __init__(self, media_path: str | Path, *, image_format: str = 'png'):
        self.media_path=str(media_path); self.image_format=image_format.lower()
        if self.image_format not in {'png','jpeg','jpg'}: raise ValueError('image_format must be png or jpeg')
    def extract_frame(self, sample: Sample, stream: MediaStream, frame_locator: FrameLocator, output_dir: Path) -> Artifact:
        if sample.source_frame_index is None: raise ValueError('frame artifact requires source_frame_index')
        point=frame_locator.locate_presentation_frame(stream, sample.source_frame_index)
        try:
            import av
        except ImportError as exc: raise RuntimeError('PyAV is required for frame artifact extraction') from exc
        container=av.open(self.media_path)
        try:
            av_stream=next(s for s in container.streams if s.index == stream.index)
            frame=next((f for f in container.decode(av_stream) if f.pts is not None and int(f.pts * f.time_base / stream.time_base.as_fraction()) == point.pts), None)
            if frame is None: raise ValueError('source frame could not be decoded')
            image=frame.to_image(); payload_format='JPEG' if self.image_format in {'jpeg','jpg'} else 'PNG'
            import io
            buf=io.BytesIO(); image.save(buf, format=payload_format); payload=buf.getvalue()
        finally: container.close()
        digest=hashlib.sha256(payload).hexdigest(); aid=f'{sample.id}:artifact:{self.image_format}'
        rel=f'artifacts/{sample.id}_artifact_{self.image_format}.{self.image_format}'
        path=Path(output_dir)/rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload)
        return Artifact(aid,sample.run_id,sample.asset_id,sample.id,'frame_image',f'image/{"jpeg" if payload_format=="JPEG" else "png"}',rel,digest,len(payload),point,image.width,image.height)
