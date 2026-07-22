"""Local processing of scanned accounting source documents.

The package consists of a document-type-neutral folder pipeline and explicit
processor packages. Shared code owns file discovery, image loading, output,
registry generation, and reporting. Each processor owns OCR, extraction,
recognition decisions, filename policy, continuation behavior, and optional
registry columns for one document type.

The current released processor is ``upd_invoices_status_1``. Future processors,
including NPD receipts, can reuse the generic ``ExtractedDocument`` model and
``BaseDocumentProcessor`` without introducing invoice-specific fields into the
shared pipeline.
"""

__version__ = "0.8.0"
