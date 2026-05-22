from pathlib import Path
from typing import Dict

import cv2
import fitz
import numpy as np
import structlog

from app.ai.image_processor import preprocess_for_ocr
from app.ai.ocr.ocr_manager import OCRManager

logger = structlog.get_logger()
ocr_manager = OCRManager()


def _render_page_image(page: fitz.Page) -> bytes:
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    return pix.tobytes("png")


def _decode_page_image(page_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(page_bytes, np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode PDF page image for OCR")
    return image


def extract_text(pdf_path: Path, pdf_type: str, document_id: str) -> Dict[int, str]:
    doc = fitz.open(pdf_path)
    page_texts: Dict[int, str] = {}

    for page_number, page in enumerate(doc, start=1):
        try:
            if pdf_type == "text":
                page_texts[page_number] = page.get_text("text").strip()
                continue

            page_bytes = _render_page_image(page)
            image = _decode_page_image(page_bytes)
            processed_image = preprocess_for_ocr(image)
            success, encoded = cv2.imencode(".png", processed_image)
            if not success:
                raise ValueError("Failed to encode preprocessed image")

            ocr_result, warning = ocr_manager.run_ocr(encoded.tobytes(), document_id)
            page_texts[page_number] = getattr(ocr_result, "text", "") or ""
            if warning:
                logger.warning("ocr_warning", page=page_number, warning=warning)
        except Exception as exc:
            logger.error("extract_text_error", page=page_number, error=str(exc))
            page_texts[page_number] = ""

    return page_texts
