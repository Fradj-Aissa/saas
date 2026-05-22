from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
import pytesseract
import structlog

logger = structlog.get_logger()


@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str = "tesseract"


def _decode_image(image_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image bytes for Tesseract")
    return image


def extract_text(image_bytes: bytes) -> OCRResult:
    image = _decode_image(image_bytes)
    data = pytesseract.image_to_data(image, lang="ara+eng", output_type=pytesseract.Output.DICT)
    text_segments = []
    confidences = []

    for idx, word in enumerate(data.get("text", [])):
        if not word or word.strip() == "":
            continue
        try:
            confidence = float(data.get("conf", [])[idx] or 0.0)
        except (ValueError, IndexError):
            confidence = 0.0

        text_segments.append(word)
        confidences.append(confidence)

    average_confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
    text = " ".join(text_segments)
    logger.info("tesseract_extracted", confidence=average_confidence)
    return OCRResult(text=text, confidence=average_confidence)
