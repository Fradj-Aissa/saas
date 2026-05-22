import asyncio
import uuid
from pathlib import Path
from typing import Optional

import sentry_sdk
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import AsyncSessionLocal
from app.models.document import Document, DocumentStatus
from app.models.output import Output
from app.utils.pdf_detector import detect_pdf_type
from app.workers.celery_app import celery_app
from app.workers.tasks.build_markdown import build_markdown
from app.workers.tasks.extract_images import extract_images
from app.workers.tasks.extract_tables import extract_tables
from app.workers.tasks.extract_text import extract_text

logger = structlog.get_logger()
settings = Settings()


async def _get_document(session: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
    result = await session.execute(select(Document).where(Document.id == document_id))
    return result.scalar_one_or_none()


async def _update_document(
    session: AsyncSession,
    document: Document,
    status: Optional[DocumentStatus] = None,
    progress: Optional[int] = None,
    error_message: Optional[str] = None,
    pdf_type: Optional[str] = None,
    total_pages: Optional[int] = None,
) -> None:
    if status is not None:
        document.status = status
    if progress is not None:
        document.progress = progress
    if error_message is not None:
        document.error_message = error_message
    if pdf_type is not None:
        document.pdf_type = pdf_type
    if total_pages is not None:
        document.total_pages = total_pages
    session.add(document)
    await session.commit()
    await session.refresh(document)


def _get_pdf_path(document: Document) -> Path:
    return Path(settings.local_storage_path) / Path(document.storage_path)


async def _process_document(document_id: str) -> None:
    parsed_id = uuid.UUID(document_id)
    async with AsyncSessionLocal() as session:
        document = await _get_document(session, parsed_id)
        if document is None:
            raise ValueError("Document not found")

        await _update_document(session, document, status=DocumentStatus.queued, progress=10)

        pdf_path = _get_pdf_path(document)
        if not pdf_path.exists():
            raise FileNotFoundError("Document file is missing")

        detection = detect_pdf_type(pdf_path)
        await _update_document(
            session,
            document,
            status=DocumentStatus.processing,
            progress=20,
            pdf_type=detection.type,
            total_pages=detection.total_pages,
        )

        page_texts = extract_text(pdf_path, detection.type, document_id)
        await _update_document(session, document, status=DocumentStatus.ocr, progress=40)

        tables = extract_tables(pdf_path, detection.type)
        await _update_document(session, document, progress=60)

        image_paths = await extract_images(pdf_path, document.user_id or "default_user")
        await _update_document(session, document, status=DocumentStatus.formatting, progress=80)

        markdown_path = await build_markdown(
            page_texts,
            tables,
            image_paths,
            document_id,
            document.user_id or "default_user",
        )
        await _update_document(session, document, progress=90)

        output = Output(
            document_id=document.id,
            markdown_path=markdown_path,
            pdf_path=None,
            docx_path=None,
        )
        session.add(output)
        await session.commit()

        await _update_document(session, document, status=DocumentStatus.completed, progress=100)


async def _mark_document_failed(document_id: str, error_message: str) -> None:
    parsed_id = uuid.UUID(document_id)
    async with AsyncSessionLocal() as session:
        document = await _get_document(session, parsed_id)
        if document is not None:
            await _update_document(
                session,
                document,
                status=DocumentStatus.failed,
                progress=document.progress or 0,
                error_message=error_message,
            )


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str) -> None:
    try:
        asyncio.run(_process_document(document_id))
    except Exception as exc:
        logger.error("pdf_processor_failed", document_id=document_id, error=str(exc))
        sentry_sdk.capture_exception(exc)
        try:
            asyncio.run(_mark_document_failed(document_id, str(exc)))
        except Exception as update_exc:
            logger.warning(
                "failed_to_update_document_after_error",
                document_id=document_id,
                error=str(update_exc),
            )
        if self.request.retries >= self.max_retries:
            raise
        raise self.retry(exc=exc)
