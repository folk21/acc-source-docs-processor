from pathlib import Path

from source_docs_processor.features.document_processing.processor_base import BaseDocumentProcessor
from source_docs_processor.features.document_processing.models import ExtractedDocument


def test_base_processor_rejects_other_document_types():
    """Verify document-type isolation remains a recognition responsibility.

    Protected risk: a result produced by one processor must not be accepted by
    another processor even though folder actions are now selected separately.
    """
    document = ExtractedDocument(
        source_path=Path("document.png"),
        document_type="another_type",
        is_recognized=True,
    )

    assert BaseDocumentProcessor().is_supported_document(document) is False


def test_base_processor_does_not_define_output_policy():
    """Verify OCR processors do not own copying, naming, or registry concerns.

    Protected risk: putting workflow methods back on processors would make a
    registry-only document type inherit irrelevant file-output behavior.
    """
    processor = BaseDocumentProcessor()

    assert not hasattr(processor, "default_target_dir_name")
    assert not hasattr(processor, "build_output_filename_stem")
    assert not hasattr(processor, "registry_extra_columns")
