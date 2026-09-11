from __future__ import annotations
import hashlib, json, os, subprocess
from dataclasses import dataclass
from typing import Any
from aei.domain.models import MediaAsset, MediaStream, rational

@dataclass
class IngestResult:
    asset: MediaAsset
    streams: list[MediaStream]
    raw_probe: dict[str, Any] | None = None

def _fingerprint(path: str) -> str:
    h=hashlib.sha256()
    with open(path,'rb') as f:
        h.update(f.read(1024*1024)); f.seek(max(0,os.path.getsize(path)-1024*1024)); h.update(f.read(1024*1024))
    return h.hexdigest()

def ingest(path: str, ffprobe_bin: str='ffprobe') -> IngestResult:
    stat=os.stat(path)
    cmd=[ffprobe_bin,'-v','error','-print_format','json','-show_format','-show_streams',path]
    try: raw=json.loads(subprocess.check_output(cmd, text=True))
    except (FileNotFoundError, subprocess.CalledProcessError) as e: raise RuntimeError('ffprobe is required for ingest') from e
    aid='asset_'+_fingerprint(path)[:24]
    fmt=raw.get('format',{})
    asset=MediaAsset(aid,os.path.abspath(path),stat.st_size,_fingerprint(path),fmt.get('format_name'))
    streams=[]
    for s in raw.get('streams',[]):
        sid=f'{aid}:stream:{s["index"]}'
        streams.append(MediaStream(sid,aid,s['index'],s.get('codec_type','unknown'),s.get('codec_name'),rational(s.get('time_base')) or rational('1/1'),s.get('start_pts'),s.get('duration_ts'),s.get('width'),s.get('height'),s.get('pix_fmt'),rational(s.get('avg_frame_rate')),rational(s.get('r_frame_rate')),int(s['tags'].get('rotate')) if s.get('tags',{}).get('rotate') else None,rational(s.get('sample_aspect_ratio')),rational(s.get('display_aspect_ratio')),{k:s.get(k) for k in ('color_space','color_transfer','color_primaries','color_range') if s.get(k) is not None}))
    return IngestResult(asset,streams,raw)

def ingest_pyav(path: str) -> IngestResult:
    """Probe through PyAV when an application chooses that adapter.

    PyAV objects are translated immediately into domain values; they never
    escape this adapter boundary.
    """
    try:
        import av
    except ImportError as e:
        raise RuntimeError('PyAV is not installed') from e
    container=av.open(path)
    stat=os.stat(path); aid='asset_'+_fingerprint(path)[:24]
    asset=MediaAsset(aid,os.path.abspath(path),stat.st_size,_fingerprint(path),getattr(container,'format',None) and container.format.name)
    streams=[]
    for s in container.streams:
        rate=getattr(s,'average_rate',None)
        nominal=getattr(s,'base_rate',None)
        streams.append(MediaStream(f'{aid}:stream:{s.index}',aid,s.index,s.type,getattr(s.codec_context,'name',None),Rational(s.time_base.numerator,s.time_base.denominator),getattr(s,'start_time',None),getattr(s,'duration',None),getattr(s,'width',None),getattr(s,'height',None),getattr(s.codec_context,'format',None) and s.codec_context.format.name,rational(rate),rational(nominal)))
    return IngestResult(asset,streams)
