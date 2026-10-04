"""Single private image per record; storage keys never enter API responses."""
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol
from uuid import UUID
import os
import warnings

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from backend.core.config import get_settings

MAX_UPLOAD = 5 * 1024 * 1024
FORMATS = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}


class ImageStorage(Protocol):
    """Adapters must implement atomic replacement and private, bounded reads."""
    def read(self, key: str) -> bytes | None: ...
    def replace(self, key: str, content: bytes) -> None: ...
    def remove(self, key: str) -> None: ...


class PrivateLocalImageStorage:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Invalid storage key")
        return path

    def read(self, key: str) -> bytes | None:
        try:
            with self._path(key).open("rb") as stream:
                content = stream.read(MAX_UPLOAD + 1)
            if len(content) > MAX_UPLOAD:
                raise OSError("Invalid stored image size")
            return content
        except FileNotFoundError:
            return None

    def replace(self, key: str, content: bytes) -> None:
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = None
        try:
            with NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def remove(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


@lru_cache
def get_image_storage() -> ImageStorage:
    return PrivateLocalImageStorage(Path(get_settings().private_image_root))


def image_key(company_id: UUID, resource: str, record_id: UUID) -> str:
    if resource not in {"customers", "assets"}:
        raise ValueError("Invalid image resource")
    return f"{company_id}/{resource}/{record_id}.webp"


def process_image(content: bytes, mime: str) -> bytes:
    if len(content) > MAX_UPLOAD:
        raise HTTPException(413, "Image must be 5 MB or smaller.")
    if mime not in FORMATS:
        raise HTTPException(415, "Choose a JPEG, PNG or WebP image.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content), formats=list(FORMATS.values())) as source:
                if source.format != FORMATS[mime]:
                    raise ValueError("MIME mismatch")
                if max(source.size) > 4096 or source.width * source.height > 16_000_000:
                    raise ValueError("Image dimensions exceeded")
                if getattr(source, "n_frames", 1) != 1:
                    raise ValueError("Animated image")
                source.verify()
            with Image.open(BytesIO(content), formats=list(FORMATS.values())) as source:
                source.load()
                oriented = ImageOps.exif_transpose(source)
                oriented.thumbnail((1024, 1024))
                # Fresh pixel-only image: no EXIF, ICC, XMP, comments or PNG metadata.
                pixels = oriented.convert("RGBA")
                clean = Image.new("RGBA", pixels.size)
                clean.paste(pixels)
                output = BytesIO()
                clean.save(output, format="WEBP", quality=85, method=4)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
            Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise HTTPException(422, "Invalid image. Use a static JPEG, PNG or WebP up to 4096px and 16 MP.") from None
