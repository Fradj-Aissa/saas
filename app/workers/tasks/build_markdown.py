from pathlib import Path
from typing import Dict, List, Optional

from app.services.storage_service import get_storage
import structlog

logger = structlog.get_logger()


def _parse_table_page(commented_table: str) -> Optional[tuple[int, str]]:
    header = "<!-- page:"
    if commented_table.startswith(header):
        try:
            end = commented_table.index("-->")
            page_number = int(commented_table[len(header):end].strip())
            table_md = commented_table[end + 3 :].strip()
            return page_number, table_md
        except Exception:
            return None
    return None


def _render_markdown(page_texts: Dict[int, str], tables: List[str], image_paths: List[str]) -> str:
    table_map = {}
    for table in tables:
        parsed = _parse_table_page(table)
        if parsed:
            page, table_md = parsed
            table_map.setdefault(page, []).append(table_md)
        else:
            table_map.setdefault(-1, []).append(table)

    lines: List[str] = ["# تقرير المستند\n"]
    for page_number in sorted(page_texts):
        lines.append(f"## صفحة {page_number}")
        page_text = page_texts.get(page_number, "").strip()
        if page_text:
            lines.append(page_text)
        page_tables = table_map.get(page_number, [])
        for table_md in page_tables:
            lines.append("### جدول الصفحة {}".format(page_number))
            lines.append(table_md)

    orphan_tables = table_map.get(-1, [])
    if orphan_tables:
        lines.append("## الجداول")
        lines.extend(orphan_tables)

    if image_paths:
        lines.append("## الصور المستخرجة")
        for idx, image_path in enumerate(image_paths, start=1):
            lines.append(f"![image_{idx}]({image_path})")

    return "\n\n".join(lines).strip()


async def build_markdown(
    page_texts: Dict[int, str],
    tables: List[str],
    image_paths: List[str],
    document_id: str,
    user_id: str,
) -> str:
    raw_markdown = _render_markdown(page_texts, tables, image_paths)
    formatted = raw_markdown

    try:
        from app.ai.gemini.gemini_client import GeminiClient

        gemini = GeminiClient()
        formatted = await gemini.format_text(raw_markdown)
    except Exception as exc:
        logger.warning("gemini_format_failed", error=str(exc))

    output_path = Path("outputs") / user_id / f"{document_id}.md"
    storage = get_storage()
    await storage.save(formatted.encode("utf-8"), output_path)

    return str(output_path)
