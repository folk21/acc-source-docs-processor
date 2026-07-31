PYTHON ?= python
PYTEST := $(PYTHON) -m pytest -q

.PHONY: help compile test check test-core test-public-api test-architecture \
	test-anonymization test-document-processing test-upd test-npd \
	test-incoming-purchase-documents

help:
	@printf '%s\n' \
		'make check                         Compile and run the complete test suite' \
		'make test                          Run the complete test suite' \
		'make test-core                     Run feature-neutral core tests' \
		'make test-public-api               Run public package and framework API contract tests' \
		'make test-architecture             Run CLI, public API, and package-boundary tests' \
		'make test-anonymization            Run anonymization unit/integration tests' \
		'make test-document-processing      Run the complete document-processing feature tests' \
		'make test-upd                      Run scanned UPD status 1 tests' \
		'make test-npd                      Run NPD receipt tests' \
		'make test-incoming-purchase-documents  Run incoming purchase-document tests'

compile:
	$(PYTHON) -m compileall -q main.py source_docs_processor tests

test:
	$(PYTEST)

check: compile test

test-core:
	$(PYTEST) tests/unit/core

test-public-api:
	$(PYTEST) \
		tests/unit/test_public_api.py \
		tests/unit/anonymization/test_api.py \
		tests/unit/document_processing/test_api.py \
		tests/unit/document_processing/test_framework_api.py

test-architecture:
	$(PYTEST) \
		tests/unit/test_cli.py \
		tests/unit/test_public_api.py \
		tests/unit/anonymization/test_api.py \
		tests/unit/document_processing/test_api.py \
		tests/unit/document_processing/test_framework_api.py \
		tests/unit/test_package_boundaries.py

test-anonymization:
	$(PYTEST) tests/unit/anonymization tests/integration/anonymization

test-document-processing:
	$(PYTEST) \
		tests/unit/document_processing \
		tests/unit/upd_invoices_status_1 \
		tests/unit/npd_receipts \
		tests/unit/incoming_purchase_documents \
		tests/unit/test_package_boundaries.py \
		tests/integration/upd_invoices_status_1 \
		tests/integration/npd_receipts \
		tests/integration/incoming_purchase_documents \
		tests/integration/test_pipeline_with_fake_processor.py

test-upd:
	$(PYTEST) tests/unit/upd_invoices_status_1 tests/integration/upd_invoices_status_1

test-npd:
	$(PYTEST) tests/unit/npd_receipts tests/integration/npd_receipts

test-incoming-purchase-documents:
	$(PYTEST) tests/unit/incoming_purchase_documents tests/integration/incoming_purchase_documents
