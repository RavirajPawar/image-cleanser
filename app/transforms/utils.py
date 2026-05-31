from typing import Tuple
from PIL import Image
import numpy as np
import cv2


class TransformerUtility:
    @staticmethod
    def pil_to_cv2(img: Image.Image) -> np.ndarray:
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    @staticmethod
    def cv2_to_png_bytes(img: np.ndarray) -> bytes:
        is_success, buffer = cv2.imencode(".png", img)
        if not is_success:
            raise RuntimeError("failed to encode PNG")
        return buffer.tobytes()
