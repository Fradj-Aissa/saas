import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Output(Base):
    __tablename__ = "outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    markdown_path = Column(String(512), nullable=True)
    pdf_path = Column(String(512), nullable=True)
    docx_path = Column(String(512), nullable=True)

    def __repr__(self) -> str:
        return f"<Output document_id={self.document_id} markdown_path={self.markdown_path}>"
