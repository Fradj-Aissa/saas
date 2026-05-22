from pathlib import Path

import pytest
from app.models.document import Document, DocumentStatus
from app.models.output import Output


@pytest.mark.asyncio
async def test_document_status_endpoint_returns_document(client, test_session):
    document = Document(
        user_id="default_user",
        filename="sample.pdf",
        content_type="application/pdf",
        storage_path="documents/default_user/sample.pdf",
        status=DocumentStatus.uploaded,
        progress=0,
    )
    test_session.add(document)
    await test_session.commit()
    await test_session.refresh(document)

    response = await client.get(f"/api/v1/documents/{document.id}/status")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(document.id)
    assert body["status"] == document.status.value
    assert body["progress"] == document.progress
    assert body["error_message"] is None


@pytest.mark.asyncio
async def test_download_document_output_markdown_returns_file(client, test_session, tmp_storage_path):
    document = Document(
        user_id="default_user",
        filename="sample.pdf",
        content_type="application/pdf",
        storage_path="documents/default_user/sample.pdf",
        status=DocumentStatus.completed,
        progress=100,
    )
    test_session.add(document)
    await test_session.flush()

    output = Output(
        document_id=document.id,
        markdown_path="outputs/default_user/sample.md",
        pdf_path=None,
        docx_path=None,
    )
    test_session.add(output)
    await test_session.commit()
    await test_session.refresh(document)

    output_file = tmp_storage_path / output.markdown_path
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("# اختبار محتوى\nهذا هو المحتوى.", encoding="utf-8")

    response = await client.get(f"/api/v1/documents/{document.id}/download/markdown")

    assert response.status_code == 200
    assert response.headers["content-disposition"].endswith('.md"')
    assert b"# اختبار محتوى" in response.content


@pytest.mark.asyncio
async def test_download_document_output_invalid_format_returns_400(client):
    response = await client.get("/api/v1/documents/00000000-0000-0000-0000-000000000000/download/unknown")
    assert response.status_code == 400
