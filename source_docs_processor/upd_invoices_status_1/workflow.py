"""Folder workflow for UPD status 1 copy-and-register processing."""

from __future__ import annotations

from ..models import ExtractedDocument
from ..workflows.copy_and_register import CopyAndRegisterWorkflow


class UpdInvoicesStatus1Workflow(CopyAndRegisterWorkflow):
    """Preserve the established UPD copying, naming, and continuation behavior."""

    default_target_dir_name = "передаточные_документы"
    supports_continuation_pages = True

    def build_primary_filename_stem(self, document: ExtractedDocument) -> str:
        """Build the established UPD filename for a recognized first page."""
        number = document.document_number or "без_номера"
        if document.document_date:
            return f"УПД_{number}_от_{document.document_date}"
        return f"УПД_{number}"

    def build_output_filename_stem(self, document: ExtractedDocument) -> str:
        """Append the Russian page suffix for a continuation page."""
        stem = self.build_primary_filename_stem(document)
        if document.is_continuation_page:
            page_number = document.continuation_page_number or 2
            return f"{stem}_{page_number}_страница"
        return stem
