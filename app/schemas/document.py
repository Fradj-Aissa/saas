from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    queued = "queued"
    processing = "processing"
    ocr = "ocr"
    formatting = "formatting"
    completed = "completed"
    failed = "failed"


class UploadResponse(BaseModel):
    id: str
    filename: str
    status: DocumentStatus
    progress: int


class DocumentStatusResponse(BaseModel):
    id: str
    status: DocumentStatus
    progress: int
    error_message: Optional[str]


class DocumentResultResponse(BaseModel):
    id: str
    status: DocumentStatus
    progress: int
    markdown_path: Optional[str] = None
    pdf_path: Optional[str] = None
    docx_path: Optional[str] = None
    error_message: Optional[str] = None
