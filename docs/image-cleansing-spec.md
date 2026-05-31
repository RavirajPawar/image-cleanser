# Image Cleansing Service — Technical Specification

This document contains the technical design and engineer-level guidance specifically scoped for the proof-of-concept: a minimal, synchronous image-cleaning service with a single endpoint. The proof-of-concept accepts a raw image as a multipart binary upload only, validates the file, applies deterministic preprocessing transforms, and returns a cleaned image and metadata. The proof-of-concept intentionally excludes asynchronous queues, workers, orchestration, PDF ingestion, and URL-based ingestion.

API contract (proof-of-concept)

POST /clean
- Request (multipart/form-data):
   - image: binary file (required). For the proof-of-concept, only multipart binary uploads are supported; do not submit PDF files or URIs.
   - request_id: string (optional)
   - hints: { language: string, expected_orientation: bool, skip_ml_enhance: bool } (optional)

- Response (application/json):
   - request_id: string
   - cleaned_image: base64-encoded PNG (inlined in the response) or a small local URL when configured
   - width: integer
   - height: integer
   - transforms: array of objects describing applied deterministic transforms and parameters
   - quality_score: float (range 0 to 100)
   - processing_time_ms: integer
   - warnings: array of strings

Errors
- 400: invalid input
- 413: payload too large
- 500: transient internal error (retryable)

Preprocessing pipeline (engineer-level detail)

1. Ingest & quick validation
   - Validate input type (image formats: JPEG, PNG, WEBP) and max size (configurable).
   - Reject very large images with a clear error; for PoC, do not accept PDFs (optional extension later).

2. Normalize
   - Convert images to RGB and to 8-bit depth.
   - If image dimensions exceed a configured limit (e.g., 4000px), downscale with Lanczos.

3. Heuristic detection
   - Orientation: compute moments / use text-orientation heuristic.
   - Blur: variance of Laplacian.
   - Noise: estimate via local variance.
   - Low contrast: use histogram spread or CLAHE response.

4. Deterministic transforms
   - Deskew: estimate skew angle via Hough lines or moments; rotate to correct.
   - Denoise: Non-local Means (`cv2.fastNlMeansDenoisingColored`) or bilateral filter.
   - Contrast: CLAHE on the luminance channel.
   - Gamma adjust: apply if image is under/over exposed.
   - Binarize: adaptive threshold (Gaussian or Otsu) if suitable.
   - Morphology: open/close with kernel sizes depending on image DPI.

5. Region detection (future enhancement)
   - For the proof-of-concept we do not produce per-region crops. The proof-of-concept returns a single cleaned full-image.
   - Per-region crops and line/word segmentation are planned for a future iteration after validating full-image cleaning improves OCR accuracy.

6. Optional machine learning enhancement (future)
   - For the proof-of-concept, machine learning enhancements are out of scope. Keep clear hooks in the codebase so Real-ESRGAN, learned denoisers, or stroke-enhancement models can be added behind feature flags in later iterations.

Production design (future)
- Packaging & storage (production only):
   - Store artifacts under structured keys: `/{env}/cleaned/{yyyy}/{mm}/{dd}/{request_id}/{image_id}.png`.
   - Persist metadata in a production metadata database (for example: Postgres) with records for request_id, artifact URIs, transforms applied, quality_score, and timing information.

Note: these production storage and database decisions are outside the proof-of-concept scope and are documented here for future implementation.

Quality scoring
- Implement metrics such as blur score, contrast score, text density, and script detection confidence.
- Normalize the combined metrics into a quality score in the range 0 to 100.
- Include human-readable reasons for low scores in the metadata to support routing and debugging.

Operational considerations (proof-of-concept)
- Keep the proof-of-concept synchronous and simple: no external queues; run as a single FastAPI process.
- Store cleaned artifacts to a local `./artifacts` folder for manual inspection; signed URLs are not required for the proof-of-concept.
- Add basic logging and timing metrics; integrate Prometheus and tracing in production iterations only.


Proof-of-concept guidance (focused)
- Build a minimal FastAPI server with a single synchronous `/clean` endpoint that executes steps 1-4 and returns the cleaned full-image in the response.
- The proof-of-concept must:
   - Validate input and return deterministic error codes.
   - Execute deterministic transforms only (deskew, denoise, contrast enhancement, adaptive binarization when useful).
   - Return the cleaned image (base64-encoded PNG) and JSON metadata in a single response.
   - Store artifacts locally under `./artifacts/{request_id}` for manual review.
- Provide unit tests for transform functions (deskew, denoise, threshold) using small sample images in `tests/fixtures`.


Acceptance & testing
- Provide a script `tools/evaluate.py` that accepts a folder of input images and outputs cleaned artifacts and JSON metadata for evaluation by an external OCR harness.

Point of view
- For the proof-of-concept, focus purely on deterministic image transforms. The goal is not to build a full feature platform but to answer the question: "Do deterministic cleaning transforms improve optical character recognition results enough to justify further investment?"
- Practical steps:
   1. Implement deskew, denoise, contrast enhancement (CLAHE), and optional adaptive binarization. Keep parameters configurable.
   2. Run the cleaned images through one or two optical character recognition providers (for example: Google Vision and Tesseract) offline and compute the change in character error rate versus the raw images.
   3. If deterministic transforms produce a measurable and cost-justifying improvement, implement per-region crops and consider machine learning-based enhancement behind feature flags.
   4. Instrument the proof-of-concept to collect simple metrics: per-image processing time, quality_score, and optical character recognition character error rate for the test harness.

---
Generated on 2026-05-31

Security
- Validate uploads and scan for executables inside archive inputs.

---
Generated on 2026-05-31
