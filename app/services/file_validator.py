import magic
from pathlib import Path
from typing import Tuple

from app.core.config import Settings
from app.core.exceptions import bad_request

settings = Settings()


def get_safe_filename(filename: str) -> str:
    return Path(filename).name


def validate_pdf_upload(file_bytes: bytes, filename: str) -> Tuple[str, str]:
    safe_name = get_safe_filename(filename)
    if not safe_name.lower().endswith(".pdf"):
        raise bad_request("Uploaded file must be a PDF")

    if len(file_bytes) > settings.max_upload_size_mb * 1024 * 1024:
        raise bad_request(f"File size exceeds {settings.max_upload_size_mb} MB")

    file_type = magic.from_buffer(file_bytes, mime=True)
    if file_type != "application/pdf":
        raise bad_request("Invalid file type: expected PDF")

    return safe_name, file_type
