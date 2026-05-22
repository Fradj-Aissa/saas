from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz
import structlog

logger = structlog.get_logger()


def _get_camelot() -> Any:
    try:
        import camelot

        return camelot
    except ImportError as exc:
        logger.warning("camelot_not_installed", error=str(exc))
        return None


def _get_pandas() -> Any:
    try:
        import pandas as pd

        return pd
    except ImportError as exc:
        logger.warning("pandas_not_installed", error=str(exc))
        return None


def _get_google_vision_engine() -> Optional["GoogleVisionEngine"]:
    try:
        from app.ai.vision.google_vision import GoogleVisionEngine

        return GoogleVisionEngine()
    except ImportError as exc:
        logger.warning("google_vision_not_installed", error=str(exc))
        return None


def _markdown_from_dataframe(df: Any) -> str:
    if hasattr(df, "empty") and df.empty:
        return ""

    headers = [str(column).strip() for column in df.columns]
    rows = [headers]
    for row in df.values.tolist():
        rows.append([str(cell).strip() for cell in row])

    column_count = len(headers)
    separator = ["---"] * column_count
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(separator) + " |"]

    for row in rows[1:]:
        line = "| " + " | ".join(row + [""] * (column_count - len(row))) + " |"
        lines.append(line)

    return "\n".join(lines)


def _commented_table(page_number: int, markdown: str) -> str:
    return f"<!-- page: {page_number} -->\n{markdown}"


def _normalize_page_number(page_index: Any) -> int:
    try:
        page_number = int(page_index)
        return page_number + 1 if page_number >= 0 else page_number
    except Exception:
        return -1


def _extract_camelot_tables(pdf_path: Path) -> List[str]:
    camelot = _get_camelot()
    pd = _get_pandas()
    if camelot is None or pd is None:
        logger.warning("camelot_or_pandas_missing")
        return []

    for flavor in ("lattice", "stream"):
        try:
            tables = camelot.read_pdf(str(pdf_path), flavor=flavor, pages="all")
            if tables and len(tables) > 0:
                markdown_tables: List[str] = []
                for table in tables:
                    md = _markdown_from_dataframe(table.df)
                    if md:
                        try:
                            page_number = int(table.page)
                        except Exception:
                            page_number = -1
                        markdown_tables.append(_commented_table(page_number, md))
                if markdown_tables:
                    return markdown_tables
        except Exception as exc:
            logger.warning("camelot_failed", flavor=flavor, error=str(exc))
    return []


def _extract_handwritten_tables(pdf_path: Path) -> List[str]:
    engine = _get_google_vision_engine()
    if engine is None:
        return []

    doc = fitz.open(pdf_path)
    markdown_tables: List[str] = []

    for page_number, page in enumerate(doc, start=1):
        try:
            image = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes("png")
            rows = engine.extract_table_from_image(image)
            if not rows:
                continue

            headers = rows[0]
            separator = ["---"] * len(headers)
            lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(separator) + " |"]
            for row in rows[1:]:
                lines.append("| " + " | ".join(row + [""] * (len(headers) - len(row))) + " |")
            markdown_tables.append(_commented_table(page_number, "\n".join(lines)))
        except Exception as exc:
            logger.warning("google_vision_table_page_failed", page=page_number, error=str(exc))

    return markdown_tables


def _extract_scanned_tables(pdf_path: Path) -> List[str]:
    try:
        from img2table.document import PDF as Img2TablePDF
        from img2table.ocr import TesseractOCR
    except ImportError as exc:
        raise RuntimeError("img2table is required for scanned table extraction") from exc

    pdf_doc = Img2TablePDF(str(pdf_path), detect_rotation=False, pdf_text_extraction=False)
    extracted = pdf_doc.extract_tables(ocr=TesseractOCR(), min_confidence=50, max_workers=1)

    markdown_tables: List[str] = []
    if isinstance(extracted, dict):
        pages: Dict[Any, List[Any]] = extracted
    else:
        pages = OrderedDict(extracted)

    for page_index, tables in pages.items():
        page_number = _normalize_page_number(page_index)
        for table in tables:
            df = getattr(table, "df", None)
            if df is not None:
                md = _markdown_from_dataframe(df)
                if md:
                    markdown_tables.append(_commented_table(page_number, md))
    return markdown_tables


def extract_tables(pdf_path: Path, pdf_type: str) -> List[str]:
    try:
        if pdf_type == "text":
            return _extract_camelot_tables(pdf_path)

        if pdf_type == "scanned" or pdf_type == "mixed":
            return _extract_scanned_tables(pdf_path)

        if pdf_type == "handwritten":
            return _extract_handwritten_tables(pdf_path)
    except Exception as exc:
        logger.warning("extract_tables_failed", error=str(exc), pdf_type=pdf_type)

    return []
