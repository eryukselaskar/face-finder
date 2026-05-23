import numpy as np
from deepface import DeepFace
from pathlib import Path
from typing import Callable, Optional
from core.database import init, clear_folder, insert_faces, save_folder_stats

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    _HEIC_OK = True
except ImportError:
    _HEIC_OK = False

EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
if _HEIC_OK:
    EXTS |= {".heic", ".heif"}

_MODEL = "ArcFace"
_DETECTOR = "retinaface"


def collect_images(folder: str) -> list:
    return [f for f in Path(folder).rglob("*") if f.suffix.lower() in EXTS]


def index_folder(
    folder: str,
    progress: Optional[Callable[[int, int, str], None]] = None,
    cancelled: Optional[Callable[[], bool]] = None,
) -> tuple[int, int]:
    init()
    clear_folder(folder)
    files = collect_images(folder)
    total = len(files)
    face_count = 0

    for i, path in enumerate(files):
        if cancelled and cancelled():
            break
        try:
            results = DeepFace.represent(
                img_path=str(path),
                model_name=_MODEL,
                detector_backend=_DETECTOR,
                enforce_detection=True,
            )
            encodings = [np.array(r["embedding"]) for r in results]
            if encodings:
                insert_faces(str(path), folder, encodings)
                face_count += len(encodings)
        except Exception:
            pass
        if progress:
            progress(i + 1, total, path.name)

    save_folder_stats(folder, total, face_count)
    return total, face_count
