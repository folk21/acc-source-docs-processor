"""Fail-closed DOCX package sanitization and visible-content anonymization."""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path, PurePosixPath

from lxml import etree

from .image import SUPPORTED_IMAGE_EXTENSIONS, anonymize_image_bytes
from .models import TextEntityAnalyzer
from .text import mask_text


_RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
_SENSITIVE_BINARY_PREFIXES = (
    "word/embeddings/",
    "word/activeX/",
)
_SENSITIVE_BINARY_NAMES = {
    "word/vbaProject.bin",
    "word/vbaData.xml",
}
_TEXT_LOCAL_NAMES = {"t"}
_PARAGRAPH_LOCAL_NAMES = {"p"}
_SENSITIVE_ATTRIBUTE_NAMES = {
    "author",
    "initials",
    "lastModifiedBy",
    "email",
    "userId",
    "descr",
    "title",
    "tooltip",
}


def _safe_member_name(info: zipfile.ZipInfo) -> str:
    """Validate a DOCX member path and reject links or traversal attempts."""
    name = info.filename.replace("\\", "/")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe DOCX package member: {info.filename}")
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise ValueError(f"DOCX package symlinks are not supported: {info.filename}")
    return name


def _local_name(tag: object) -> str:
    """Return the local part of one expanded XML name."""
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def _xml_parser() -> etree.XMLParser:
    """Create an XML parser that disables network and entity expansion."""
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        remove_blank_text=False,
        recover=False,
        huge_tree=False,
    )


def _sanitize_relationships(root: etree._Element) -> None:
    """Remove external and stripped custom-data relationships."""
    for relationship in list(root):
        target = relationship.get("Target", "")
        relationship_type = relationship.get("Type", "")
        if (
            relationship.get("TargetMode") == "External"
            or "customXml" in target
            or "customXml" in relationship_type
            or "custom-properties" in relationship_type
        ):
            root.remove(relationship)


def _sanitize_content_types(root: etree._Element) -> None:
    """Remove package declarations for stripped custom data."""
    for element in list(root):
        part_name = element.get("PartName", "")
        content_type = element.get("ContentType", "")
        if "customXml" in part_name or "custom-properties" in content_type:
            root.remove(element)


def _mask_text_nodes(
    root: etree._Element,
    analyzer: TextEntityAnalyzer,
) -> int:
    """Mask text across paragraph runs and then sanitize remaining text nodes."""
    detected = 0
    processed: set[int] = set()

    for paragraph in root.iter():
        if _local_name(paragraph.tag) not in _PARAGRAPH_LOCAL_NAMES:
            continue
        nodes = [
            node
            for node in paragraph.iter()
            if _local_name(node.tag) in _TEXT_LOCAL_NAMES and node.text
        ]
        if not nodes:
            continue
        combined = "".join(node.text or "" for node in nodes)
        masked, entities = mask_text(combined, analyzer)
        detected += len(entities)
        offset = 0
        for node in nodes:
            length = len(node.text or "")
            node.text = masked[offset : offset + length]
            offset += length
            processed.add(id(node))

    for node in root.iter():
        if id(node) in processed or _local_name(node.tag) not in _TEXT_LOCAL_NAMES:
            continue
        if not node.text:
            continue
        node.text, entities = mask_text(node.text, analyzer)
        detected += len(entities)

    for element in root.iter():
        for attribute_name in tuple(element.attrib):
            if _local_name(attribute_name) in _SENSITIVE_ATTRIBUTE_NAMES:
                element.set(attribute_name, "ANONYMIZED")
    return detected


def _sanitize_xml(
    name: str,
    content: bytes,
    analyzer: TextEntityAnalyzer,
) -> tuple[bytes, int]:
    """Sanitize one XML part and return serialized safe content."""
    root = etree.fromstring(content, parser=_xml_parser())
    detected = 0
    if name.endswith(".rels") and root.tag == f"{{{_RELATIONSHIPS_NS}}}Relationships":
        _sanitize_relationships(root)
    elif name == "[Content_Types].xml" and root.tag == f"{{{_CONTENT_TYPES_NS}}}Types":
        _sanitize_content_types(root)
    else:
        detected = _mask_text_nodes(root, analyzer)

    if name in {"docProps/core.xml", "docProps/app.xml"}:
        for element in root.iter():
            if element is not root and element.text:
                element.text = ""

    return (
        etree.tostring(
            root,
            encoding="UTF-8",
            xml_declaration=True,
            standalone=None,
        ),
        detected,
    )


def _validate_package_members(members: list[tuple[zipfile.ZipInfo, str]]) -> None:
    """Reject package content that cannot be sanitized reliably."""
    names = [name for _info, name in members]
    if len(names) != len(set(names)):
        raise ValueError("DOCX contains duplicate package member names")
    name_set = set(names)
    forbidden = sorted(
        name
        for name in name_set
        if name in _SENSITIVE_BINARY_NAMES
        or any(name.startswith(prefix) for prefix in _SENSITIVE_BINARY_PREFIXES)
    )
    if forbidden:
        raise ValueError(
            "DOCX contains embedded or active content which cannot be safely anonymized: "
            + ", ".join(forbidden)
        )

    for name in name_set:
        if not (
            name.startswith("word/media/")
            or name.startswith("docProps/thumbnail")
        ):
            continue
        suffix = Path(name).suffix.lower()
        if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError(
                "DOCX contains an unsupported embedded image format which "
                "cannot be safely anonymized: "
                + name
            )


def anonymize_docx_file(
    source: Path,
    destination: Path,
    analyzer: TextEntityAnalyzer,
    lang: str = "rus+eng",
) -> int:
    """Anonymize text and raster media while stripping hidden custom data."""
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
                if name.startswith("customXml/") or name == "docProps/custom.xml":
                    continue

                content = archive.read(info)
                suffix = Path(name).suffix.lower()
                if (
                    name.endswith(".xml")
                    or name.endswith(".rels")
                    or name == "[Content_Types].xml"
                ):
                    content, count = _sanitize_xml(name, content, analyzer)
                    detected += count
                elif (
                    name.startswith("word/media/")
                    or name.startswith("docProps/thumbnail")
                ):
                    content, count = anonymize_image_bytes(
                        content,
                        suffix=suffix,
                        analyzer=analyzer,
                        lang=lang,
                    )
                    detected += count

                output.writestr(name, content)
    return detected
