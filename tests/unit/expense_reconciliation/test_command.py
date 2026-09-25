"""CLI regression tests for expense reconciliation."""

from source_docs_processor.cli import build_parser


def test_reconcile_expenses_subcommand_owns_two_input_sources() -> None:
    """Verify reconciliation exposes source documents and statement separately.

    Protected risk: adding statement options to `process` would violate the
    document-type contract and make unrelated workflows understand reconciliation.
    """
    args = build_parser().parse_args(
        [
            "reconcile-expenses",
            "--source",
            "/tmp/documents",
            "--statement",
            "/tmp/payments.xlsx",
            "--output",
            "/tmp/output",
        ]
    )

    assert args.command == "reconcile-expenses"
    assert args.source == "/tmp/documents"
    assert args.statement == "/tmp/payments.xlsx"
    assert args.output == "/tmp/output"
    assert args.lang == "rus+eng"
    assert not hasattr(args, "document_type")
