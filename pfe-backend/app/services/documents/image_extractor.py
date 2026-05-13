from __future__ import annotations

import io
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}


def extract_text_from_image(
    filename: str,
    file_bytes: bytes,
    use_openai_vision: bool = True,
) -> str:
    """
    Extract text from an image file.

    Two strategies (tried in order):
      1. OpenAI Vision (gpt-4o) — best accuracy for formatted documents,
         invoices, tables, handwriting. Requires OPENAI_API_KEY.
      2. Tesseract OCR — free, local, good for clean printed text.

    Returns the extracted text as a plain string.
    """
    if use_openai_vision:
        try:
            return _extract_with_openai_vision(filename, file_bytes)
        except Exception as exc:
            logger.warning(
                "OpenAI Vision failed for '%s' (%s), falling back to Tesseract.",
                filename, exc,
            )

    return _extract_with_tesseract(filename, file_bytes)


def build_image_source(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    """
    Full pipeline: extract text from image → build a source dict compatible
    with the scoring pipeline (same format as PDF/website sources).
    """
    text = extract_text_from_image(filename, file_bytes)
    if not text.strip():
        raise ValueError(f"No text could be extracted from image '{filename}'.")

    return {
        "type":     "document",
        "url":      None,
        "label":    filename,
        "text":     text,
        "sections": _build_sections(text),
        "anchors":  {},
    }


# ---------------------------------------------------------------------------
# Strategy 1 — OpenAI Vision
# ---------------------------------------------------------------------------

def _extract_with_openai_vision(filename: str, file_bytes: bytes) -> str:
    """
    Send the image to gpt-4o-mini with a prompt asking it to transcribe
    all visible text, preserving structure.
    Works for invoices, questionnaires, tables, handwritten notes.
    """
    import base64
    from openai import OpenAI
    from app.core.config import settings

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured.")

    # Detect MIME type
    ext = filename.rsplit(".", 1)[-1].lower()
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "webp": "image/webp",
        "tiff": "image/tiff", "tif": "image/tiff",
        "bmp": "image/bmp",
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    # Encode to base64
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    client = OpenAI(api_key=settings.openai_api_key, timeout=60.0)
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=3000,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a document digitisation assistant. "
                    "Transcribe ALL text visible in the image, preserving structure. "
                    "Output each fact on its own line in the format: 'Label : Valeur'. "
                    "Do not summarise or paraphrase — output the raw text only."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url, "detail": "high"},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"This image is named '{filename}'. "
                            "Please transcribe all its text content exactly, one fact per line."
                        ),
                    },
                ],
            },
        ],
    )
    text = response.choices[0].message.content or ""
    logger.info(
        "OpenAI Vision extracted %d chars from '%s'", len(text), filename
    )
    return text


# ---------------------------------------------------------------------------
# Strategy 2 — Tesseract OCR
# ---------------------------------------------------------------------------

def _extract_with_tesseract(filename: str, file_bytes: bytes) -> str:
    """
    Local OCR using Tesseract via pytesseract.

    Preprocessing steps applied before OCR:
      1. Convert to grayscale
      2. Adaptive thresholding (binarize) — improves contrast
      3. Light denoising

    Language: French + English (add more with tesseract-ocr-<lang> packages).
    """
    try:
        import cv2
        import numpy as np
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            f"Tesseract dependencies not installed ({exc}). "
            "Run: poetry add Pillow pytesseract opencv-python-headless "
            "and: sudo apt install tesseract-ocr tesseract-ocr-fra"
        ) from exc

    # Load image
    pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    img = np.array(pil_img)

    # Preprocessing pipeline
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # Adaptive threshold — handles uneven lighting
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=10,
    )
    # Mild denoise
    denoised = cv2.fastNlMeansDenoising(binary, h=10)

    # Run OCR — French + English, document layout mode (psm=3)
    processed_pil = Image.fromarray(denoised)
    text = pytesseract.image_to_string(
        processed_pil,
        lang="fra+eng",
        config="--psm 3 --oem 3",
    )

    logger.info(
        "Tesseract extracted %d chars from '%s'", len(text), filename
    )
    return text.strip()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _build_sections(text: str) -> List[Dict[str, str]]:
    """Split extracted text into sections for semantic chunking."""
    sections = []
    for para in re.split(r"\n{2,}", text):
        para = para.strip()
        if len(para.split()) >= 5:
            sections.append({"heading": "", "text": para[:1000]})
        if len(sections) >= 20:
            break
    return sections or [{"heading": "", "text": text[:1000]}]


def is_image_file(filename: str) -> bool:
    """Return True if the filename has an image extension."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in IMAGE_EXTENSIONS
