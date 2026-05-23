import face_recognition
import numpy as np
from typing import List, Optional, Tuple
from core.database import get_all_encodings


def get_encoding(image_path: str) -> Optional[np.ndarray]:
    img = face_recognition.load_image_file(image_path)
    encs = face_recognition.face_encodings(img)
    return encs[0] if encs else None


def search(ref_enc: np.ndarray, tolerance: float = 0.55) -> List[Tuple[str, str, float]]:
    all_data = get_all_encodings()
    best: dict = {}
    for fp, fd, enc in all_data:
        d = float(face_recognition.face_distance([enc], ref_enc)[0])
        if d <= tolerance and (fp not in best or d < best[fp][2]):
            best[fp] = (fp, fd, d)
    return sorted(best.values(), key=lambda x: x[2])
