"""Pillow stays inside the vision adapter."""
from io import BytesIO


class InvalidImageError(ValueError):
    pass


def decode_image(data: bytes, media_type: str | None = None, size: tuple[int, int] | None = None):
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(BytesIO(data)) as image:
            actual_type = {"PNG": "image/png", "JPEG": "image/jpeg"}.get(image.format)
            if actual_type is None or (media_type is not None and actual_type != media_type):
                raise InvalidImageError("unsupported image format or media type mismatch")
            if size is not None and image.size != size:
                raise InvalidImageError("image dimensions do not match Artifact metadata")
            if getattr(image, "n_frames", 1) != 1:
                raise InvalidImageError("only a single still image is supported")
            image.load()
            return image.convert("RGB")
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise InvalidImageError("corrupt or unsafe image payload") from exc
