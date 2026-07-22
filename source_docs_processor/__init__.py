"""Local processing of scanned accounting source documents.

The package separates three independently selected responsibilities:

1. a document processor recognizes and extracts one image;
2. a processing workflow decides how a source folder and its files are handled;
3. a registry definition controls the tabular output schema and row mapping.

A complete document type definition binds these parts together for CLI use. The
current released definition is ``upd_invoices_status_1``. Future receipt, act,
or other definitions can select different folder actions and CSV schemas without
adding conditional business logic to the OCR processor or CLI.
"""

__version__ = "0.9.0"
