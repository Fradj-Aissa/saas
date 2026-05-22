from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import structlog
from google.cloud import vision_v1
from google.cloud.vision_v1 import ImageAnnotatorClient

from app.core.config import Settings

logger = structlog.get_logger()
settings = Settings()
_client: Optional[ImageAnnotatorClient] = None


def _get_client() -> ImageAnnotatorClient:
    global _client
    if _client is None:
        _client = vision_v1.ImageAnnotatorClient()
        logger.info("google_vision_client_initialized")
    return _client


def _calculate_confidence(annotation: vision_v1.types.TextAnnotation) -> float:
    confidences: List[float] = []
    for page in annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    confidences.append(word.confidence)
    if not confidences:
        return 0.0
    return float(sum(confidences) / len(confidences))


def _parse_rows(text: str) -> List[List[str]]:
    rows: List[List[str]] = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        cells = [cell.strip() for cell in line.split("\t") if cell.strip()]
        rows.append(cells if cells else [line.strip()])
    return rows


class VisionCostController:
    _document_calls: Dict[str, int] = defaultdict(int)
    _daily_calls: Dict[str, int] = defaultdict(int)
    _current_day: str = date.today().isoformat()

    @classmethod
    def _reset_if_needed(cls) -> None:
        today = date.today().isoformat()
        if today != cls._current_day:
            cls._current_day = today
            cls._daily_calls.clear()
            cls._document_calls.clear()

    @classmethod
    def can_call(cls, document_id: str) -> Tuple[bool, Optional[str]]:
        cls._reset_if_needed()
        if cls._document_calls[document_id] >= settings.google_vision_max_calls_per_document:
            return False, "Exceeded per-document Google Vision call limit"
        if cls._daily_calls[cls._current_day] >= settings.google_vision_max_calls_per_day:
            return False, "Exceeded daily Google Vision call limit"
        return True, None

    @classmethod
    def record_call(cls, document_id: str) -> None:
        cls._reset_if_needed()
        cls._document_calls[document_id] += 1
        cls._daily_calls[cls._current_day] += 1
        logger.info("google_vision_call_recorded", document_id=document_id, count=cls._document_calls[document_id])

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        cls._reset_if_needed()
        return {
            "date": cls._current_day,
            "daily_calls": cls._daily_calls.get(cls._current_day, 0),
            "calls_per_document": dict(cls._document_calls),
        }


class GoogleVisionEngine:
    def __init__(self) -> None:
        self.client = _get_client()

    def extract_text(self, image_bytes: bytes) -> Dict[str, Any]:
        image = vision_v1.Image(content=image_bytes)
        response = self.client.document_text_detection(
            image=image,
            image_context={"language_hints": ["ar", "en"]},
        )
        if response.error.message:
            logger.error("google_vision_error", error=response.error.message)
            raise RuntimeError(response.error.message)

        annotation = response.full_text_annotation
        text = annotation.text if annotation else ""
        confidence = _calculate_confidence(annotation) if annotation else 0.0
        return {"text": text, "confidence": confidence}

    def extract_handwritten(self, image_bytes: bytes) -> Dict[str, Any]:
        return self.extract_text(image_bytes)

    def extract_table_from_image(self, image_bytes: bytes) -> List[List[str]]:
        image = vision_v1.Image(content=image_bytes)
        response = self.client.document_text_detection(
            image=image,
            image_context={"language_hints": ["ar", "en"]},
        )
        if response.error.message:
            logger.error("google_vision_table_error", error=response.error.message)
            raise RuntimeError(response.error.message)

        annotation = response.full_text_annotation
        if not annotation or not annotation.text:
            return []

        return _parse_rows(annotation.text)
