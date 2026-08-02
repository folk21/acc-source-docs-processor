"""Local processing and anonymization of accounting source documents.

The package is organized around independent features:

- ``features.anonymization`` owns privacy-safe redaction and its CLI adapter;
- ``features.document_processing`` owns processing contracts, infrastructure,
  registered document types, its programmatic API, and its CLI adapter;
- ``core`` contains feature-neutral filesystem, image, text, and path primitives;
- ``cli`` composes feature entry points without importing their internals.

The public CLI and registered document type identifiers remain stable while each
feature and document implementation can evolve independently.
"""

__version__ = "0.26.0"

__all__ = ["__version__"]
