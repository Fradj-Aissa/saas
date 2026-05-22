from datetime import datetime
from enum import Enum
from pathlib import Path
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    queued = "queued"
    processing = "processing"
    ocr = "ocr"
    formatting = "formatting"
    completed = "completed"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(64), nullable=True, default="default_user")
    filename = Column(String(255), nullable=False)
    content_type = Column(String(127), nullable=False)
    storage_path = Column(String(512), nullable=False)
    status = Column(SQLEnum(DocumentStatus), nullable=False, default=DocumentStatus.uploaded)
    progress = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename} status={self.status} progress={self.progress}>"
