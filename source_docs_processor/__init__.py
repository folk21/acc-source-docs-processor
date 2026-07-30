"""Local processing and anonymization of accounting source documents.

The package is organized around independent features:

- ``features.anonymization`` owns privacy-safe document redaction;
- ``features.document_types`` owns document recognition, workflows, registries,
  and concrete document-type implementations;
- ``core`` contains only utilities shared by more than one feature;
- ``commands`` adapts CLI arguments to the selected feature.

The public CLI and registered document type identifiers remain stable while the
internal feature packages evolve independently.
"""

__version__ = "0.14.0"
