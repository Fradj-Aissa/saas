from typing import Any, List, Optional, Tuple

import structlog

from app.ai.ocr.easyocr_engine import extract_text as easyocr_extract
from app.ai.ocr.paddle_engine import extract_text as paddle_extract
from app.ai.ocr.tesseract_engine import extract_text as tesseract_extract
from app.ai.vision.google_vision import GoogleVisionEngine, VisionCostController

logger = structlog.get_logger()


class OCRManager:
    CONFIDENCE_THRESHOLD = 0.7

    def __init__(self) -> None:
        self.google_engine = GoogleVisionEngine()
        self.cost_controller = VisionCostController()

    def _log_result(self, engine_name: str, confidence: float) -> None:
        logger.info("ocr_engine_used", engine=engine_name, confidence=confidence)

    def _best_result(self, results: List[Any]) -> Any:
        return max(results, key=lambda result: getattr(result, "confidence", 0.0))

    def run_ocr(self, image_bytes: bytes, document_id: str) -> Tuple[Any, Optional[str]]:
        results: List[Any] = []
        warning: Optional[str] = None

        engines = [
            ("easyocr", easyocr_extract),
            ("paddleocr", paddle_extract),
            ("tesseract", tesseract_extract),
        ]

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
        if can_call:
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
