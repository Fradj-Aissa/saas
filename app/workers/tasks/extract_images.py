from pathlib import Path
from typing import List

import fitz
import structlog

from app.services.storage_service import get_storage

logger = structlog.get_logger()


async def extract_images(pdf_path: Path, user_id: str) -> List[str]:
    document = fitz.open(pdf_path)
    storage = get_storage()
    saved_paths: List[str] = []

    for page_number, page in enumerate(document, start=1):
        for image_index, image_info in enumerate(page.get_images(full=True), start=1):
            try:
                xref = image_info[0]
                image_data = document.extract_image(xref)
                image_bytes = image_data["image"]
                extension = image_data.get("ext", "png")
                filename = f"page_{page_number}_image_{image_index}.{extension}"
                relative_path = Path("outputs") / user_id / "images" / filename
                await storage.save(image_bytes, relative_path)
                saved_paths.append(str(relative_path))
            except Exception as exc:
                logger.warning("extract_image_failed", page=page_number, image_index=image_index, error=str(exc))

    return saved_paths
