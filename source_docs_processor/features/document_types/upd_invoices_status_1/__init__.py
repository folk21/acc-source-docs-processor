"""Processor package for Russian UPD invoice-transfer documents with status 1.

This package contains all layout-specific logic for the currently supported
primary document type:

- fixed crop coordinates for the official UPD landscape form;
- targeted OCR for status, document number, document date, shipment row, and
  continuation-page markers;
- extraction and adjustment rules for noisy OCR text;
- orientation scoring tuned to UPD first pages and page-2 continuation scans.

Generic scanning, file copying, reporting, and CLI orchestration live one level
higher in `source_docs_processor`.
"""

from .processor import UpdInvoicesStatus1Processor

__all__ = ["UpdInvoicesStatus1Processor"]
