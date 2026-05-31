from typing import List, Tuple
from PIL import Image
import numpy as np
import cv2
from pathlib import Path

from .constants import (
    DENOISE_H,
    CLAHE_CLIP,
    BINARIZE_STD_THRESH,
    RAW_IMAGES_DIR,
    ARTIFACTS_DIR,
    ADAPTIVE_BLOCKSIZE,
    ADAPTIVE_C,
)
from app.logger import logger
from .utils import TransformerUtility


class ImageTransformer:
    """Deterministic image transformation pipeline.

    Each step is a method so callers can unit-test or extend behavior.
    """

    def __init__(
        self,
        denoise_h: int = DENOISE_H,
        clahe_clip: float = CLAHE_CLIP,
        binarize_std_thresh: float = BINARIZE_STD_THRESH,
    ):
        self.denoise_h = denoise_h
        self.clahe_clip = clahe_clip
        self.binarize_std_thresh = binarize_std_thresh
        logger.info(
            f"Initialized ImageTransformer with denoise_h={denoise_h}, "
            f"clahe_clip={clahe_clip}, binarize_std_thresh={binarize_std_thresh}"
        )

    def deskew(self, img: np.ndarray) -> Tuple[np.ndarray, dict]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        coords = np.column_stack(np.where(gray < 255))
        angle = 0.0
        if coords.size > 0:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            h, w = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            img = cv2.warpAffine(
                img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
            )
        return img, {"name": "deskew", "angle": float(angle)}

    def denoise(self, img: np.ndarray) -> Tuple[np.ndarray, dict]:
        dst = cv2.fastNlMeansDenoisingColored(
            img,
            None,
            h=self.denoise_h,
            hColor=self.denoise_h,
            templateWindowSize=7,
            searchWindowSize=21,
        )
        return dst, {
            "name": "denoise",
            "method": "fastNlMeans",
            "params": {"h": self.denoise_h},
        }

    def enhance_contrast(self, img: np.ndarray) -> Tuple[np.ndarray, dict]:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return final, {"name": "clahe", "clipLimit": float(self.clahe_clip)}

    def adaptive_binarize(self, img: np.ndarray) -> Tuple[np.ndarray, dict]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        th = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            ADAPTIVE_BLOCKSIZE,
            ADAPTIVE_C,
        )
        return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR), {
            "name": "adaptive_binarize",
            "method": "gaussian",
            "blockSize": ADAPTIVE_BLOCKSIZE,
        }

    def compute_quality_score(self, img: np.ndarray) -> float:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        contrast = gray.std()
        score = min(
            100.0, max(0.0, (lap_var / 100.0) * 30.0 + (contrast / 255.0) * 70.0)
        )
        return float(score)

    def transform(
        self, pil_image: Image.Image, skip_ml_enhance: bool = True
    ) -> Tuple[bytes, List[dict], float]:
        img = TransformerUtility.pil_to_cv2(pil_image)
        transforms: List[dict] = []

        img, info = self.deskew(img)
        transforms.append(info)

        img, info = self.denoise(img)
        transforms.append(info)

        img, info = self.enhance_contrast(img)
        transforms.append(info)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if gray.std() < self.binarize_std_thresh:
            img, info = self.adaptive_binarize(img)
            transforms.append(info)

        quality = self.compute_quality_score(img)
        png_bytes = TransformerUtility.cv2_to_png_bytes(img)
        return png_bytes, transforms, quality


def _ensure_dirs():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # Simple CLI to process one sample image from app/raw_images
    _ensure_dirs()
    src = None
    for p in RAW_IMAGES_DIR.glob("*"):
        if p.is_file():
            src = p
            break
    if src is None:
        print(
            f"No sample images found in {RAW_IMAGES_DIR}. Place a file there and re-run."
        )
    else:
        print(f"Processing sample image: {src}")
        img = Image.open(src).convert("RGB")
        t = ImageTransformer()
        png_bytes, transforms, quality = t.transform(img)
        out_path = ARTIFACTS_DIR / f"cleaned_{src.name}.png"
        with open(out_path, "wb") as f:
            f.write(png_bytes)
        meta_path = ARTIFACTS_DIR / f"cleaned_{src.stem}.json"
        import json

        with open(meta_path, "w") as f:
            json.dump({"transforms": transforms, "quality": quality}, f, indent=2)
        print(f"Wrote {out_path} and {meta_path}")
