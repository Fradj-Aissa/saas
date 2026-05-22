from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import structlog

try:
    from app.ai.ocr.easyocr_engine import extract_text as easyocr_extract
except ImportError:
    easyocr_extract = None

try:
    from app.ai.ocr.paddle_engine import extract_text as paddle_extract
except ImportError:
    paddle_extract = None

try:
    from app.ai.ocr.tesseract_engine import extract_text as tesseract_extract
except ImportError:
    tesseract_extract = None

try:
    from app.ai.vision.google_vision import GoogleVisionEngine, VisionCostController
except ImportError:
    GoogleVisionEngine = None  # type: ignore

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
            return True, None

        @classmethod
        def record_call(cls, document_id: str) -> None:
            cls._reset_if_needed()
            cls._document_calls[document_id] += 1
            cls._daily_calls[cls._current_day] += 1

        @classmethod
        def get_stats(cls) -> Dict[str, Any]:
            cls._reset_if_needed()
            return {
                "date": cls._current_day,
                "daily_calls": cls._daily_calls.get(cls._current_day, 0),
                "calls_per_document": dict(cls._document_calls),
            }

logger = structlog.get_logger()


class OCRManager:
    CONFIDENCE_THRESHOLD = 0.7

    def __init__(self) -> None:
        self.google_engine = GoogleVisionEngine() if GoogleVisionEngine is not None else None
        self.cost_controller = VisionCostController()

    def _log_result(self, engine_name: str, confidence: float) -> None:
        logger.info("ocr_engine_used", engine=engine_name, confidence=confidence)

    def _best_result(self, results: List[Any]) -> Any:
        return max(results, key=lambda result: getattr(result, "confidence", 0.0))

    def run_ocr(self, image_bytes: bytes, document_id: str) -> Tuple[Any, Optional[str]]:
        results: List[Any] = []
        warning: Optional[str] = None

        engines = []
        if easyocr_extract is not None:
            engines.append(("easyocr", easyocr_extract))
        if paddle_extract is not None:
            engines.append(("paddleocr", paddle_extract))
        if tesseract_extract is not None:
            engines.append(("tesseract", tesseract_extract))

        for engine_name, extractor in engines:
            try:
                result = extractor(image_bytes)
                self._log_result(engine_name, result.confidence)
                results.append(result)
                if result.confidence >= self.CONFIDENCE_THRESHOLD:
                    return result, None
            except Exception as exc:
                logger.warning("ocr_engine_failed", engine=engine_name, error=str(exc))

        can_call, reason = self.cost_controller.can_call(document_id)
        if can_call and self.google_engine is not None:
            try:
                google_response = self.google_engine.extract_text(image_bytes)
                self.cost_controller.record_call(document_id)
                confidence = float(google_response.get("confidence", 0.0))
                self._log_result("google_vision", confidence)
                return type("OCRResult", (), {"text": google_response.get("text", ""), "confidence": confidence, "engine": "google_vision"})(), None
            except Exception as exc:
                logger.warning("google_vision_failed", error=str(exc))

        if results:
            best_result = self._best_result(results)
            warning = reason or "Google Vision was not used; returning best available OCR." 
            logger.warning("google_vision_skipped", reason=warning)
            return best_result, warning

        raise RuntimeError("No OCR result could be produced")
