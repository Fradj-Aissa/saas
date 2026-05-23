from pathlib import Path
from typing import Tuple, Optional

from app.core.config import Settings
from app.core.exceptions import bad_request

settings = Settings()

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


def get_safe_filename(filename: str) -> str:
    return Path(filename).name


def validate_pdf_upload(file_bytes: bytes, filename: str) -> Tuple[str, str]:
    safe_name = get_safe_filename(filename)
    if not safe_name.lower().endswith(".pdf"):
        raise bad_request("Uploaded file must be a PDF")

    if len(file_bytes) > settings.max_upload_size_mb * 1024 * 1024:
        raise bad_request(f"File size exceeds {settings.max_upload_size_mb} MB")

    # Use magic for MIME type validation if available
    if HAS_MAGIC:
        file_type = magic.from_buffer(file_bytes, mime=True)
        if file_type != "application/pdf":
            raise bad_request("Invalid file type: expected PDF")
    else:
        # Fallback: check PDF magic bytes (header)
        if not file_bytes.startswith(b"%PDF"):
            raise bad_request("Invalid file type: expected PDF")
        file_type = "application/pdf"

    return safe_name, file_type
