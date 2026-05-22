from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import internal_error, not_found
from app.db.session import get_db
from app.models.document import Document, DocumentStatus
from app.models.output import Output
from app.schemas.document import DocumentResultResponse, DocumentStatusResponse, UploadResponse
from app.services.file_validator import validate_pdf_upload
from app.services.storage_service import get_storage

router = APIRouter(prefix="/documents", tags=["documents"])

USER_ID = "default_user"


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    try:
        file_bytes = await file.read()
        safe_name, content_type = validate_pdf_upload(file_bytes, file.filename)

        document = Document(
            user_id=USER_ID,
            filename=safe_name,
            content_type=content_type,
            storage_path="",
            status=DocumentStatus.uploaded,
            progress=0,
        )
        db.add(document)
        await db.flush()

        storage = get_storage()
        relative_path = Path("documents") / USER_ID / str(document.id) / safe_name
        await storage.save(file_bytes, relative_path)

        document.storage_path = str(relative_path)
        await db.commit()
        await db.refresh(document)

        return UploadResponse(
            id=str(document.id),
            filename=document.filename,
            status=document.status,
            progress=document.progress,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise internal_error("Unable to upload document") from exc


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentStatusResponse:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise not_found("Document not found")

    return DocumentStatusResponse(
        id=str(document.id),
        status=document.status,
        progress=document.progress,
        error_message=document.error_message,
    )


@router.get("/{document_id}/result", response_model=DocumentResultResponse)
async def document_result(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentResultResponse:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise not_found("Document not found")

    output_result = await db.execute(select(Output).where(Output.document_id == document.id))
    output = output_result.scalar_one_or_none()

    return DocumentResultResponse(
        id=str(document.id),
        status=document.status,
        progress=document.progress,
        markdown_path=output.markdown_path if output else None,
        pdf_path=output.pdf_path if output else None,
        docx_path=output.docx_path if output else None,
        error_message=document.error_message,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise not_found("Document not found")

    storage = get_storage()
    if document.storage_path:
        await storage.delete(Path(document.storage_path))

    await db.delete(document)
    await db.commit()
    return {"detail": "Document deleted successfully"}
