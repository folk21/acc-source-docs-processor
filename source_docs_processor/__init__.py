"""Core package for local processing of scanned accounting source documents.

The application is organized as a small OCR pipeline:

1. The CLI walks through a source directory recursively and keeps the original
   subfolder structure in the generated target directory.
2. Each image is tested in several orientations so sideways scans can be saved
   back in the orientation that produced the best recognition result.
3. The OCR layer combines lightweight header OCR with targeted crops for fields
   that matter most: status, document number, document date, shipment row, and
   continuation-page markers.
4. The extractor layer converts noisy OCR text into structured metadata and
   applies domain-specific corrections for Russian UPD status 1 documents.
5. The file operations layer copies recognized documents, continuation pages,
   and unrecognized files, then writes a semicolon-separated registry and a text
   report for manual review.

The current implementation is intentionally focused on UPD status 1 documents,
but the package boundaries are kept broad enough to support additional primary
document extractors later.
"""

__version__ = "0.6.0"
