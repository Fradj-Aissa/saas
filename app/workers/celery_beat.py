import asyncio
from datetime import datetime, timedelta
from pathlib import Path

import structlog
from sqlalchemy import select

from app.core.config import Settings
from app.db.session import AsyncSessionLocal
from app.models.document import Document, DocumentStatus

logger = structlog.get_logger()
settings = Settings()


async def _cleanup_expired_documents() -> None:
    cutoff = datetime.utcnow() - timedelta(days=7)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(
                Document.updated_at < cutoff,
                Document.status.notin_([DocumentStatus.completed, DocumentStatus.failed]),
            )
        )
        documents = result.scalars().all()
        for document in documents:
            document.status = DocumentStatus.failed
            document.error_message = "Document expired after 7 days and was cleaned up."
            session.add(document)
        if documents:
            await session.commit()
            logger.info("expired_documents_updated", count=len(documents))


async def _cleanup_storage_files() -> None:
    storage_root = Path(settings.local_storage_path)
    cutoff = datetime.utcnow().timestamp() - timedelta(days=7).total_seconds()
    if not storage_root.exists():
        return
    for path in storage_root.rglob("*"):
        if path.is_file() and path.stat().st_mtime < cutoff:
            try:
                path.unlink()
                logger.info("deleted_old_file", path=str(path))
            except Exception as exc:
                logger.warning("delete_old_file_failed", path=str(path), error=str(exc))


def cleanup_old_files() -> None:
    try:
        asyncio.run(_cleanup_storage_files())
        asyncio.run(_cleanup_expired_documents())
    except Exception as exc:
        logger.error("cleanup_old_files_failed", error=str(exc))
