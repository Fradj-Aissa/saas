from pathlib import Path
import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import internal_error, not_found
from app.db.session import get_db
from app.models.document import Document, DocumentStatus
from app.models.output import Output
from app.schemas.document import DocumentResultResponse, DocumentStatusResponse, UploadResponse
from app.services.file_validator import validate_pdf_upload
from app.services.storage_service import get_storage
from app.utils.exporter import export_content_from_markdown
from app.workers.pdf_processor import process_document

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
        document.status = DocumentStatus.queued
        document.progress = 10
        await db.commit()
        await db.refresh(document)

        process_document.delay(str(document.id))

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


@router.websocket("/ws/{document_id}/progress")
async def document_progress_ws(websocket: WebSocket, document_id: str) -> None:
    await websocket.accept()

    try:
        parsed_id = uuid.UUID(document_id)
    except ValueError:
        await websocket.send_json({"error": "Invalid document id"})
        await websocket.close()
        return

    try:
        while True:
            async with get_db() as db:
                result = await db.execute(select(Document).where(Document.id == parsed_id))
                document = result.scalar_one_or_none()

            if document is None:
                await websocket.send_json({"error": "Document not found"})
                break

            await websocket.send_json(
                {
                    "id": str(document.id),
                    "status": document.status,
                    "progress": document.progress,
                    "error_message": document.error_message,
                }
            )

            if document.status in {DocumentStatus.completed, DocumentStatus.failed}:
                break

            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return
    finally:
        await websocket.close()


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


@router.get("/{document_id}/download/{export_format}")
async def download_document_output(
    document_id: str,
    export_format: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    supported_formats = {"markdown": "text/markdown", "pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if export_format not in supported_formats:
        raise HTTPException(status_code=400, detail="Unsupported export format")

    parsed_id = uuid.UUID(document_id)
    result = await db.execute(select(Document).where(Document.id == parsed_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise not_found("Document not found")

    output_result = await db.execute(select(Output).where(Output.document_id == document.id))
    output = output_result.scalar_one_or_none()
    if output is None or output.markdown_path is None:
        raise not_found("Document output not available")

    storage = get_storage()
    markdown_bytes = await storage.get(Path(output.markdown_path))
    if export_format == "markdown":
        content = markdown_bytes
        filename = f"{document.id}.md"
    else:
        try:
            markdown_text = markdown_bytes.decode("utf-8")
            content = export_content_from_markdown(markdown_text, export_format)
        except RuntimeError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
        filename = f"{document.id}.{export_format}"

        if export_format == "pdf" and output.pdf_path is None:
            output.pdf_path = str(Path("outputs") / (document.user_id or "default_user") / filename)
            await db.commit()
            await db.refresh(output)
        if export_format == "docx" and output.docx_path is None:
            output.docx_path = str(Path("outputs") / (document.user_id or "default_user") / filename)
            await db.commit()
            await db.refresh(output)

        await storage.save(content, Path(output.pdf_path if export_format == "pdf" else output.docx_path))

    return StreamingResponse(
        io.BytesIO(content),
        media_type=supported_formats[export_format],
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
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
