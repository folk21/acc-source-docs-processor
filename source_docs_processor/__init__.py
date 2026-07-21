"""Core package for local processing of scanned accounting source documents.

The application is organized as a generic folder-processing pipeline plus
pluggable document processors:

1. The CLI walks through a source directory recursively and keeps the original
   subfolder structure in the generated target directory.
2. The CLI creates a document processor through `create_document_processor()`.
   The processor is selected by the `--document-type` parameter.
3. The generic pipeline loads every image and delegates document-specific OCR,
   rotation scoring, field extraction, and continuation-page detection to the
   selected processor.
4. The current released processor is `upd_invoices_status_1`. It recognizes
   Russian UPD documents with status `1`, meaning invoice plus transfer document.
5. Generic modules still handle reusable concerns: image loading, rotation,
   Tesseract wrappers, output copying, CSV registry writing, and run reporting.
6. Processor packages own template-specific details: crop coordinates, targeted
   OCR fields, extraction heuristics, and adjustment rules for bad scans.

This boundary is intended to make the project evolve from a single-purpose UPD
finder into a broader local accounting source-document processor. A new document
type should be added as a new processor package and registered in the factory,
rather than by mixing its rules into the CLI or generic helper modules.
"""

__version__ = "0.7.0"
