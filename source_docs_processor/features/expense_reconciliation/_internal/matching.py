"""Exact-amount matching between expense documents and statement positions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .models import ExpenseDocument, ExpenseMatch, StatementEntry


@dataclass(frozen=True)
class _AmountPattern:
    """Represent one document match by statement amount denominations only."""

    document_index: int
    amount_indexes: tuple[int, ...]
    amount_cents: int


@dataclass(frozen=True)
class _AssignmentSlot:
    """Represent one selected document's need for a concrete statement row."""

    document_index: int
    pattern_position: int


def _money_cents(value: Decimal) -> int:
    """Convert a two-decimal Decimal amount to integer cents."""
    return int((value * 100).to_integral_exact())


def _normalized_person(value: str | None) -> str:
    """Normalize one optional person name for conservative exact comparison."""
    if not value:
        return ""
    return " ".join(value.casefold().replace("ё", "е").replace("/", " ").split())


def _row_preference(
    document: ExpenseDocument,
    entry: StatementEntry,
) -> tuple[int, int, int]:
    """Score a duplicate-amount statement row by optional person and date hints."""
    person_score = 0
    document_person = _normalized_person(document.person_name)
    if document_person and _normalized_person(entry.person_name) == document_person:
        person_score = 1

    date_score = 0
    if document.document_date is not None:
        difference = abs((entry.transaction_date - document.document_date).days)
        date_score = max(0, 31 - min(difference, 31))

    return date_score, person_score, -entry.source_row


def _build_amount_patterns(
    documents: list[ExpenseDocument],
    amount_values: tuple[int, ...],
    available_counts: tuple[int, ...],
) -> dict[int, tuple[_AmountPattern, ...]]:
    """Build unique one-position and two-position amount patterns per document."""
    index_by_amount = {amount: index for index, amount in enumerate(amount_values)}
    patterns_by_document: dict[int, tuple[_AmountPattern, ...]] = {}

    for document_index, document in enumerate(documents):
        if document.amount is None or document.amount <= 0:
            continue
        target = _money_cents(document.amount)
        patterns: list[_AmountPattern] = []

        single_index = index_by_amount.get(target)
        if single_index is not None and available_counts[single_index] > 0:
            patterns.append(
                _AmountPattern(
                    document_index=document_index,
                    amount_indexes=(single_index,),
                    amount_cents=target,
                )
            )

        for left_index, left_amount in enumerate(amount_values):
            right_amount = target - left_amount
            if right_amount < left_amount:
                continue
            right_index = index_by_amount.get(right_amount)
            if right_index is None:
                continue
            if left_index == right_index and available_counts[left_index] < 2:
                continue
            patterns.append(
                _AmountPattern(
                    document_index=document_index,
                    amount_indexes=(left_index, right_index),
                    amount_cents=target,
                )
            )

        if patterns:
            patterns_by_document[document_index] = tuple(
                sorted(
                    set(patterns),
                    key=lambda pattern: (
                        -len(pattern.amount_indexes),
                        pattern.amount_indexes,
                    ),
                )
            )
    return patterns_by_document


def _consume_pattern(
    counts: tuple[int, ...],
    pattern: _AmountPattern,
) -> tuple[int, ...] | None:
    """Return updated amount counts or None when the pattern is unavailable."""
    updated = list(counts)
    for amount_index in pattern.amount_indexes:
        if updated[amount_index] <= 0:
            return None
        updated[amount_index] -= 1
    return tuple(updated)


def _select_amount_patterns(
    documents: list[ExpenseDocument],
    entries: list[StatementEntry],
) -> tuple[_AmountPattern, ...]:
    """Select a globally optimal non-overlapping set by amount denominations.

    The exact objective is lexicographic: covered statement amount, covered
    statement positions, and matched supporting documents. Row identities inside
    duplicate amounts are assigned afterwards using optional person/date hints.
    """
    statement_amounts = [_money_cents(entry.amount) for entry in entries]
    amount_values = tuple(sorted(set(statement_amounts)))
    amount_index = {amount: index for index, amount in enumerate(amount_values)}
    counts = [0] * len(amount_values)
    for amount in statement_amounts:
        counts[amount_index[amount]] += 1
    available_counts = tuple(counts)

    patterns_by_document = _build_amount_patterns(
        documents,
        amount_values,
        available_counts,
    )
    document_order = sorted(
        patterns_by_document,
        key=lambda index: (
            len(patterns_by_document[index]),
            -_money_cents(documents[index].amount or Decimal("0")),
            index,
        ),
    )
    remaining_amount_upper = [0] * (len(document_order) + 1)
    for position in range(len(document_order) - 1, -1, -1):
        document = documents[document_order[position]]
        remaining_amount_upper[position] = (
            remaining_amount_upper[position + 1]
            + _money_cents(document.amount or Decimal("0"))
        )

    best_score = (-1, -1, -1)
    best_patterns: tuple[_AmountPattern, ...] = ()
    memo: dict[tuple[int, tuple[int, ...]], int] = {}

    def search(
        position: int,
        remaining_counts: tuple[int, ...],
        covered_amount: int,
        covered_rows: int,
        matched_documents: int,
        selected: tuple[_AmountPattern, ...],
    ) -> None:
        nonlocal best_score, best_patterns

        if covered_amount + remaining_amount_upper[position] < best_score[0]:
            return

        state_key = (position, remaining_counts)
        previous_matched_documents = memo.get(state_key)
        if (
            previous_matched_documents is not None
            and previous_matched_documents >= matched_documents
        ):
            return
        memo[state_key] = matched_documents

        if position == len(document_order):
            score = (covered_amount, covered_rows, matched_documents)
            if score > best_score:
                best_score = score
                best_patterns = selected
            return

        document_index = document_order[position]
        for pattern in patterns_by_document[document_index]:
            updated_counts = _consume_pattern(remaining_counts, pattern)
            if updated_counts is None:
                continue
            search(
                position + 1,
                updated_counts,
                covered_amount + pattern.amount_cents,
                covered_rows + len(pattern.amount_indexes),
                matched_documents + 1,
                selected + (pattern,),
            )

        search(
            position + 1,
            remaining_counts,
            covered_amount,
            covered_rows,
            matched_documents,
            selected,
        )

    search(0, available_counts, 0, 0, 0, ())
    return best_patterns


def _assign_statement_rows(
    selected: tuple[_AmountPattern, ...],
    documents: list[ExpenseDocument],
    entries: list[StatementEntry],
) -> list[ExpenseMatch]:
    """Assign concrete duplicate-amount rows using optional person/date hints."""
    rows_by_amount: dict[int, list[int]] = {}
    for statement_index, entry in enumerate(entries):
        rows_by_amount.setdefault(_money_cents(entry.amount), []).append(statement_index)

    slots_by_amount: dict[int, list[_AssignmentSlot]] = {}
    amount_values = tuple(sorted(rows_by_amount))
    for pattern in selected:
        for pattern_position, amount_index in enumerate(pattern.amount_indexes):
            amount = amount_values[amount_index]
            slots_by_amount.setdefault(amount, []).append(
                _AssignmentSlot(
                    document_index=pattern.document_index,
                    pattern_position=pattern_position,
                )
            )

    assigned_by_document: dict[int, list[int]] = {
        pattern.document_index: [] for pattern in selected
    }
    for amount, slots in slots_by_amount.items():
        available_rows = set(rows_by_amount[amount])
        ordered_slots = sorted(
            slots,
            key=lambda slot: (
                documents[slot.document_index].document_date is not None,
                documents[slot.document_index].person_name is not None,
                -slot.document_index,
            ),
            reverse=True,
        )
        for slot in ordered_slots:
            document = documents[slot.document_index]
            statement_index = max(
                available_rows,
                key=lambda index: _row_preference(document, entries[index]),
            )
            available_rows.remove(statement_index)
            assigned_by_document[slot.document_index].append(statement_index)

    return sorted(
        (
            ExpenseMatch(
                document_index=document_index,
                statement_indexes=tuple(sorted(statement_indexes)),
            )
            for document_index, statement_indexes in assigned_by_document.items()
        ),
        key=lambda match: (min(match.statement_indexes), match.document_index),
    )


def match_expenses(
    documents: list[ExpenseDocument],
    entries: list[StatementEntry],
) -> list[ExpenseMatch]:
    """Choose global exact amount matches and then resolve duplicate rows."""
    selected = _select_amount_patterns(documents, entries)
    return _assign_statement_rows(selected, documents, entries)
