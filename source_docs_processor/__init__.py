"""Local processing of scanned and electronic accounting source documents.

The package separates three independently selected responsibilities:

1. a processor recognizes and extracts one image or source file;
2. a processing workflow decides how a source folder and its files are handled;
3. a registry definition controls tabular output schemas and row mapping.

A complete document type definition binds these parts together for CLI use.
Existing scan and receipt workflows remain independent from the incoming purchase
document workflow, whose current scope is PDF/DOCX UPD status 1 files.
"""

__version__ = "0.11.2"
