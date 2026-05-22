from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass
class PdfDetectionResult:
    type: str
    text_ratio: float
    image_ratio: float
    total_pages: int


def detect_pdf_type(pdf_path: Path) -> PdfDetectionResult:
    document = fitz.open(pdf_path)
    total_pages = document.page_count
    text_pages = 0
    image_pages = 0

    for page in document:
        page_text = page.get_text("text")
        has_text = bool(page_text.strip())
        image_count = len(page.get_images(full=True))

        if has_text:
            text_pages += 1
        if image_count > 0:
            image_pages += 1

    text_ratio = text_pages / total_pages if total_pages else 0.0
    image_ratio = image_pages / total_pages if total_pages else 0.0

    if text_ratio > 0.8:
        pdf_type = "text"
    elif image_ratio > 0.8:
        pdf_type = "scanned"
    elif text_ratio > 0.3 and image_ratio > 0.3:
        pdf_type = "mixed"
    else:
        pdf_type = "handwritten"

    return PdfDetectionResult(
        type=pdf_type,
        text_ratio=round(text_ratio, 3),
        image_ratio=round(image_ratio, 3),
        total_pages=total_pages,
    )
