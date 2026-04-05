import shutil
import uuid
from pathlib import Path

from app.config import get_settings

CONTENT_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def cat_upload_dir(cat_id: int) -> Path:
    return get_settings().upload_root / "cats" / str(cat_id)


def delete_cat_upload_dir(cat_id: int) -> None:
    d = cat_upload_dir(cat_id)
    if d.is_dir():
        shutil.rmtree(d, ignore_errors=True)


def save_cat_photo(cat_id: int, content: bytes, content_type: str) -> str:
    settings = get_settings()
    ext = CONTENT_EXT.get(content_type.split(";")[0].strip().lower())
    if ext is None:
        raise ValueError("unsupported_image_type")
    if len(content) > settings.max_upload_bytes:
        raise ValueError("file_too_large")

    base = cat_upload_dir(cat_id)
    base.mkdir(parents=True, exist_ok=True)
    for old in base.iterdir():
        if old.is_file():
            old.unlink()

    name = f"{uuid.uuid4().hex}{ext}"
    path = base / name
    path.write_bytes(content)
    return f"/uploads/cats/{cat_id}/{name}"
