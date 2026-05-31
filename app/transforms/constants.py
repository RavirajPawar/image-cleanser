"""Constants for the ImageTransformer pipeline."""

from pathlib import Path

# Denoise parameter
DENOISE_H = 10

# CLAHE clip limit
CLAHE_CLIP = 2.0

# Threshold for deciding whether to apply adaptive binarization (std of gray)
BINARIZE_STD_THRESH = 40.0

# Adaptive threshold params
ADAPTIVE_BLOCKSIZE = 15
ADAPTIVE_C = 9

# Input validation defaults
MAX_DIM = 4000
MAX_BYTES = 10 * 1024 * 1024

# Paths
RAW_IMAGES_DIR = Path(__file__).parents[1] / "raw_images"
ARTIFACTS_DIR = Path.cwd() / "artifacts"
