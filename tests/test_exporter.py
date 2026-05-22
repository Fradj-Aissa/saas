import pytest

from app.utils.exporter import export_content_from_markdown


def test_export_content_from_markdown_returns_markdown_bytes():
    markdown = "# عنوان\nهذا نص اختبار"
    content = export_content_from_markdown(markdown, "markdown")

    assert isinstance(content, bytes)
    assert b"# عنوان" in content
    assert b"هذا نص اختبار" in content


def test_export_content_from_markdown_unsupported_format_raises():
    with pytest.raises(ValueError):
        export_content_from_markdown("Hello", "xlsx")
