from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
from paddleocr import PaddleOCR
import structlog

logger = structlog.get_logger()
_reader: Optional[PaddleOCR] = None


@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str = "paddleocr"


def _get_reader() -> PaddleOCR:
    global _reader
    if _reader is None:
        _reader = PaddleOCR(lang="arabic", use_angle_cls=True, use_gpu=False)
        logger.info("paddleocr_initialized")
    return _reader


def _decode_image(image_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image bytes for PaddleOCR")
    return image


def extract_text(image_bytes: bytes) -> OCRResult:
    image = _decode_image(image_bytes)
    reader = _get_reader()
    results = reader.ocr(image, cls=True)
    if not results:
        return OCRResult(text="", confidence=0.0)

    lines = []
    confidences = []
    for page in results:
        for line in page:
            text = line[1][0].strip()
            confidence = float(line[1][1] or 0.0)
            if text:
                lines.append(text)
                confidences.append(confidence)

    average_confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
    return OCRResult(text="\n".join(lines), confidence=average_confidence)
