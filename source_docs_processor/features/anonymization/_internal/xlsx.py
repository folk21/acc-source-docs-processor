"""Fail-closed XLSX package sanitization while preserving workbook structure."""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path, PurePosixPath

from lxml import etree

from .config import AnonymizationConfig, EMPTY_ANONYMIZATION_CONFIG
from .image import SUPPORTED_IMAGE_EXTENSIONS, anonymize_image_bytes
from .models import TextEntityAnalyzer
from .text import merge_entities, transform_text, transform_text_parts


_OPAQUE_PREFIXES = (
    "xl/activeX/",
    "xl/embeddings/",
    "xl/externalLinks/",
    "xl/pivotCache/",
    "xl/queryTables/",
    "xl/threadedComments/",
    "xl/persons/",
    "xl/model/",
    "xl/richData/",
    "customXml/",
)
_OPAQUE_NAMES = {
    "xl/vbaProject.bin",
    "xl/connections.xml",
    "docProps/custom.xml",
}
_VISIBLE_TEXT_PART_PREFIXES = (
    "xl/drawings/",
    "xl/charts/",
)
_SENSITIVE_TEXT_ATTRIBUTES = {"descr", "title", "tooltip"}
_FORMULA_LOCAL_NAMES = {"f", "formula1", "formula2", "definedName"}
_HEADER_FOOTER_LOCAL_NAMES = {
    "oddHeader",
    "oddFooter",
    "evenHeader",
    "evenFooter",
    "firstHeader",
    "firstFooter",
}


def _safe_member_name(info: zipfile.ZipInfo) -> str:
    """Validate one XLSX package member path and reject links or traversal."""
    name = info.filename.replace("\\", "/")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe XLSX package member: {info.filename}")
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise ValueError(f"XLSX package symlinks are not supported: {info.filename}")
    if info.flag_bits & 0x1:
        raise ValueError(f"Encrypted XLSX package members are not supported: {info.filename}")
    return name


def _xml_parser() -> etree.XMLParser:
    """Create a parser that disables network access and entity expansion."""
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        remove_blank_text=False,
        recover=False,
        huge_tree=False,
    )


def _local_name(tag: object) -> str:
    """Return the local part of one expanded XML name."""
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def _validate_package_members(members: list[tuple[zipfile.ZipInfo, str]]) -> None:
    """Reject workbook content that cannot be anonymized reliably."""
    names = [name for _info, name in members]
    if len(names) != len(set(names)):
        raise ValueError("XLSX contains duplicate package member names")

    forbidden = sorted(
        name
        for name in names
        if name in _OPAQUE_NAMES or any(name.startswith(prefix) for prefix in _OPAQUE_PREFIXES)
    )
    if forbidden:
        raise ValueError(
            "XLSX contains external, embedded, cached, or active content which "
            "cannot be safely anonymized: " + ", ".join(forbidden)
        )

    for name in names:
        if not name.startswith("xl/media/"):
            continue
        suffix = Path(name).suffix.lower()
        if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError(
                "XLSX contains an unsupported embedded image format which "
                "cannot be safely anonymized: " + name
            )


def _contains_sensitive_text(value: str, analyzer: TextEntityAnalyzer) -> bool:
    """Return True when one structural string contains detected PII."""
    return bool(merge_entities(analyzer.analyze(value), len(value)))


def _transform_nodes(
    nodes: list[etree._Element],
    analyzer: TextEntityAnalyzer,
) -> int:
    """Transform visible text split across one OOXML rich-text container."""
    active = [node for node in nodes if node.text]
    if not active:
        return 0
    parts = [node.text or "" for node in active]
    transformed, entities = transform_text_parts(parts, analyzer)
    for node, value in zip(active, transformed, strict=True):
        node.text = value
    return len(entities)


def _sanitize_shared_strings(root: etree._Element, analyzer: TextEntityAnalyzer) -> int:
    """Sanitize shared-string items while preserving rich-text run structure."""
    detected = 0
    for item in root.iter():
        if _local_name(item.tag) != "si":
            continue
        nodes = [node for node in item.iter() if _local_name(node.tag) == "t"]
        detected += _transform_nodes(nodes, analyzer)
    return detected


def _sanitize_comments(root: etree._Element, analyzer: TextEntityAnalyzer) -> int:
    """Sanitize comment text and remove stored comment-author identities."""
    detected = 0
    for element in root.iter():
        local = _local_name(element.tag)
        if local == "author":
            element.text = "ANONYMIZED"
        elif local == "text":
            nodes = [node for node in element.iter() if _local_name(node.tag) == "t"]
            detected += _transform_nodes(nodes, analyzer)
    return detected


def _sanitize_worksheet(root: etree._Element, analyzer: TextEntityAnalyzer) -> int:
    """Sanitize visible worksheet strings and reject PII embedded in formulas."""
    detected = 0
    for element in root.iter():
        local = _local_name(element.tag)
        if local in _FORMULA_LOCAL_NAMES and element.text:
            if _contains_sensitive_text(element.text, analyzer):
                raise ValueError(
                    "XLSX contains detected PII inside a formula or defined expression; "
                    "rewriting formulas is not supported safely"
                )
        if local in _HEADER_FOOTER_LOCAL_NAMES and element.text:
            element.text, entities = transform_text(element.text, analyzer)
            detected += len(entities)
        if local == "is":
            nodes = [node for node in element.iter() if _local_name(node.tag) == "t"]
            detected += _transform_nodes(nodes, analyzer)

    for cell in root.iter():
        if _local_name(cell.tag) != "c" or cell.get("t") != "str":
            continue
        value = next(
            (child for child in cell if _local_name(child.tag) == "v" and child.text),
            None,
        )
        if value is not None:
            value.text, entities = transform_text(value.text or "", analyzer)
            detected += len(entities)
    return detected


def _sanitize_visible_xml(root: etree._Element, analyzer: TextEntityAnalyzer) -> int:
    """Sanitize drawing/chart text and privacy-relevant descriptive attributes."""
    detected = 0
    for element in root.iter():
        local = _local_name(element.tag)
        if local in {"t", "v"} and element.text:
            element.text, entities = transform_text(element.text, analyzer)
            detected += len(entities)
        for attribute_name in tuple(element.attrib):
            if _local_name(attribute_name) not in _SENSITIVE_TEXT_ATTRIBUTES:
                continue
            value = element.get(attribute_name, "")
            transformed, entities = transform_text(value, analyzer)
            element.set(attribute_name, transformed)
            detected += len(entities)
    return detected


def _sanitize_workbook(root: etree._Element, analyzer: TextEntityAnalyzer) -> None:
    """Reject PII in structural workbook names which cannot be rewritten safely."""
    for element in root.iter():
        local = _local_name(element.tag)
        if local == "sheet":
            value = element.get("name", "")
            if value and _contains_sensitive_text(value, analyzer):
                raise ValueError(
                    "XLSX contains detected PII in a worksheet name; automatic "
                    "sheet renaming is not supported safely"
                )
        elif local == "definedName" and element.text:
            if _contains_sensitive_text(element.text, analyzer):
                raise ValueError(
                    "XLSX contains detected PII in a defined name expression"
                )


def _sanitize_table(root: etree._Element, analyzer: TextEntityAnalyzer) -> None:
    """Reject PII duplicated in structural table names or column definitions."""
    for element in root.iter():
        for attribute in ("name", "displayName"):
            value = element.get(attribute, "")
            if value and _contains_sensitive_text(value, analyzer):
                raise ValueError(
                    "XLSX contains detected PII in a structural table name or "
                    "column definition which cannot be rewritten safely"
                )


def _clear_properties(root: etree._Element) -> None:
    """Remove workbook document-property values that may identify an author."""
    for element in root.iter():
        if element is root:
            continue
        if element.text:
            element.text = ""


def _reject_external_relationships(name: str, root: etree._Element) -> None:
    """Reject external package relationships so hidden targets cannot leak data."""
    if not name.endswith(".rels"):
        return
    for relationship in root:
        if relationship.get("TargetMode") == "External":
            raise ValueError(
                "XLSX contains external relationships which cannot be copied into "
                "a privacy-safe anonymized workbook"
            )


def _sanitize_xml(
    name: str,
    content: bytes,
    analyzer: TextEntityAnalyzer,
) -> tuple[bytes, int]:
    """Sanitize one XLSX XML part while preserving unrelated workbook markup."""
    root = etree.fromstring(content, parser=_xml_parser())
    detected = 0
    _reject_external_relationships(name, root)

    if name == "xl/sharedStrings.xml":
        detected += _sanitize_shared_strings(root, analyzer)
    elif name.startswith("xl/comments") and name.endswith(".xml"):
        detected += _sanitize_comments(root, analyzer)
    elif name.startswith("xl/worksheets/") and name.endswith(".xml"):
        detected += _sanitize_worksheet(root, analyzer)
    elif name == "xl/workbook.xml":
        _sanitize_workbook(root, analyzer)
    elif name.startswith("xl/tables/") and name.endswith(".xml"):
        _sanitize_table(root, analyzer)
    elif name.startswith(_VISIBLE_TEXT_PART_PREFIXES) and name.endswith(".xml"):
        detected += _sanitize_visible_xml(root, analyzer)
    elif name in {"docProps/core.xml", "docProps/app.xml"}:
        _clear_properties(root)

    return (
        etree.tostring(
            root,
            encoding="UTF-8",
            xml_declaration=True,
            standalone=None,
        ),
        detected,
    )


def anonymize_xlsx_file(
    source: Path,
    destination: Path,
    analyzer: TextEntityAnalyzer,
    lang: str = "rus+eng",
    config: AnonymizationConfig = EMPTY_ANONYMIZATION_CONFIG,
) -> int:
    """Anonymize visible XLSX content and embedded raster images safely."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    detected = 0
    with zipfile.ZipFile(source, "r") as archive:
        members = [(info, _safe_member_name(info)) for info in archive.infolist()]
        _validate_package_members(members)

        with zipfile.ZipFile(
            destination,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as output:
            for info, name in members:
                if info.is_dir():
                    continue
                content = archive.read(info)
                if name.startswith("xl/media/"):
                    content, count = anonymize_image_bytes(
                        content,
                        suffix=Path(name).suffix.lower(),
                        analyzer=analyzer,
                        lang=lang,
                        config=config,
                    )
                    detected += count
                elif (
                    name.endswith(".xml")
                    or name.endswith(".rels")
                    or name == "[Content_Types].xml"
                ):
                    content, count = _sanitize_xml(name, content, analyzer)
                    detected += count
                output.writestr(info, content)
    return detected
