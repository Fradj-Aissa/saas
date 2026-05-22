from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
import easyocr
import structlog

logger = structlog.get_logger()
_reader: Optional[easyocr.Reader] = None


@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str = "easyocr"


def _get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["ar", "en"], gpu=False)
        logger.info("easyocr_initialized")
    return _reader


def _decode_image(image_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image bytes for EasyOCR")
    return image


def extract_text(image_bytes: bytes) -> OCRResult:
    image = _decode_image(image_bytes)
    reader = _get_reader()
    results = reader.readtext(image)
    if not results:
        return OCRResult(text="", confidence=0.0)

    text = "\n".join([item[1] for item in results])
    confidences = [item[2] for item in results if item[2] is not None]
    average_confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
    logger.info("easyocr_extracted", confidence=average_confidence)
    return OCRResult(text=text, confidence=average_confidence)
