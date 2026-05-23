import logging
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

_MODEL    = "ArcFace"
_DETECTOR = "retinaface"

# ── File logger ──────────────────────────────────────────
_LOG_PATH = Path.home() / ".face_finder" / "indexer.log"
_LOG_PATH.parent.mkdir(exist_ok=True)

_log = logging.getLogger("face_finder")
if not _log.handlers:
    _fh = logging.FileHandler(_LOG_PATH, encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                                       datefmt="%Y-%m-%d %H:%M:%S"))
    _log.addHandler(_fh)
    _log.setLevel(logging.DEBUG)


def _reason(exc: Exception) -> str:
    msg = str(exc).lower()
    if "face could not be detected" in msg or "cannot find any face" in msg:
        return "Yüz bulunamadı"
    if "no such file" in msg or "cannot identify image file" in msg:
        return "Dosya okunamadı"
    if "truncated" in msg or "corrupt" in msg or "invalid" in msg:
        return "Bozuk görüntü"
    return f"{type(exc).__name__}"


def collect_images(folder: str) -> list:
    return [f for f in Path(folder).rglob("*") if f.suffix.lower() in EXTS]


def index_folder(
    folder: str,
    progress:  Optional[Callable[[int, int, str], None]] = None,
    cancelled: Optional[Callable[[], bool]] = None,
    warn_cb:   Optional[Callable[[str, str], None]] = None,
) -> tuple[int, int]:
    init()
    clear_folder(folder)
    files = collect_images(folder)
    total = len(files)
    face_count = 0
    skip_count = 0

    _log.info(f"Başladı  → {folder}  ({total} dosya)")

    for i, path in enumerate(files):
        if cancelled and cancelled():
            _log.info(f"İptal edildi  → {folder}")
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
                _log.debug(f"OK  {path.name}  ({len(encodings)} yüz)")
        except Exception as exc:
            reason = _reason(exc)
            skip_count += 1
            _log.warning(f"Atlandı  {path.name}  —  {reason}")
            if warn_cb:
                warn_cb(path.name, reason)
        if progress:
            progress(i + 1, total, path.name)

    _log.info(
        f"Bitti  → {folder}  |  "
        f"{face_count} yüz  /  {total - skip_count} indekslendi  /  {skip_count} atlandı"
    )
    save_folder_stats(folder, total, face_count)
    return total, face_count
