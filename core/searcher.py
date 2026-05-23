import numpy as np
from deepface import DeepFace
from typing import List, Optional, Tuple
from core.database import get_all_encodings

_MODEL = "ArcFace"
_DETECTOR = "retinaface"


def get_encoding(image_path: str) -> Optional[np.ndarray]:
    try:
        results = DeepFace.represent(
            img_path=image_path,
            model_name=_MODEL,
            detector_backend=_DETECTOR,
            enforce_detection=True,
        )
        return np.array(results[0]["embedding"]) if results else None
    except Exception:
        return None


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 1.0
    return 1.0 - float(np.dot(a, b) / (norm_a * norm_b))


def search(ref_enc: np.ndarray, tolerance: float = 0.55) -> List[Tuple[str, str, float]]:
    all_data = get_all_encodings()
    best: dict = {}
    for fp, fd, enc in all_data:
        d = _cosine_distance(ref_enc, enc)
        if d <= tolerance and (fp not in best or d < best[fp][2]):
            best[fp] = (fp, fd, d)
    return sorted(best.values(), key=lambda x: x[2])
