"""Source-file processor for electronic UPD status 1 documents."""

from __future__ import annotations

from pathlib import Path

from ..document_processor import BaseSourceFileProcessor
from ..file_ops import safe_filename
from ..models import ExtractedDocument
from .extractor import DOCUMENT_TYPE, extract_document
from .readers import read_docx, read_pdf


class IncomingPurchaseDocumentsProcessor(BaseSourceFileProcessor):
    """Read PDF and DOCX UPD files using native content before OCR fallback."""

    document_type = DOCUMENT_TYPE
    display_name = "Electronic UPD invoice-transfer document, status 1"
    supported_extensions = frozenset({".pdf", ".docx"})

    def analyze_source_file(
        self,
        source_path: Path,
        lang: str,
        deep_ocr: bool,
        debug_root: Path | None = None,
    ) -> ExtractedDocument:
        """Extract one PDF or DOCX source file."""
        suffix = source_path.suffix.lower()
        debug_dir = (
            debug_root / safe_filename(source_path.stem)
            if debug_root is not None
            else None
        )
        if suffix == ".pdf":
            content = read_pdf(
                source_path,
                lang=lang,
                deep_ocr=deep_ocr,
                debug_dir=debug_dir,
            )
        elif suffix == ".docx":
            content = read_docx(source_path, debug_dir=debug_dir)
        else:
            raise ValueError(f"Unsupported electronic UPD file format: {suffix}")
        return extract_document(source_path, content)
