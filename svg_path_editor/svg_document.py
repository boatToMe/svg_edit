import re
from pathlib import Path
from xml.etree import ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
SUPPORTED_TAGS = {"path", "line", "polygon"}
CSS_BACKGROUND_FILL = "var(--background)"
CSS_STROKE_COLOR = "currentColor"
COLOR_STYLE_KEYS = {"fill", "stroke"}


def strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def parse_viewbox(value: str | None):
    if not value:
        return None
    parts = [float(item) for item in re.split(r"[\s,]+", value.strip()) if item]
    if len(parts) != 4:
        return None
    return tuple(parts)


def parse_style_attr(style_text: str) -> dict[str, str]:
    style_map: dict[str, str] = {}
    for part in style_text.split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key:
            style_map[key] = value
    return style_map


def serialize_style_attr(style_map: dict[str, str]) -> str:
    return "; ".join(f"{key}: {value}" for key, value in style_map.items())


def color_value_of(element: ET.Element, style_map: dict[str, str], key: str) -> str:
    value = element.get(key)
    if value is None:
        value = style_map.get(key, "")
    return value.strip().lower()


def normalize_element_colors_for_css(element: ET.Element):
    tag = strip_ns(element.tag)
    style_map = parse_style_attr(element.get("style", ""))
    fill_value = color_value_of(element, style_map, "fill")
    stroke_value = color_value_of(element, style_map, "stroke")

    for key in COLOR_STYLE_KEYS:
        style_map.pop(key, None)
        if key in element.attrib:
            del element.attrib[key]

    if style_map:
        element.set("style", serialize_style_attr(style_map))
    elif "style" in element.attrib:
        del element.attrib["style"]

    if tag == "line":
        element.set("fill", "none")
        element.set("stroke", CSS_STROKE_COLOR)
        return

    if fill_value != "none":
        element.set("fill", CSS_BACKGROUND_FILL)
    else:
        element.set("fill", "none")

    if stroke_value and stroke_value != "none":
        element.set("stroke", CSS_STROKE_COLOR)


class SVGPathDocument:
    def __init__(self):
        self.tree: ET.ElementTree | None = None
        self.root: ET.Element | None = None
        self.editable_elements: list[ET.Element] = []
        self.file_path: Path | None = None
        self.view_box: tuple[float, float, float, float] | None = None

    def load(self, file_path: Path):
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()
        self.file_path = file_path
        self.view_box = parse_viewbox(self.root.get("viewBox")) if self.root is not None else None
        self.editable_elements = [
            elem for elem in self.root.iter() if strip_ns(elem.tag) in SUPPORTED_TAGS
        ]

    def save(self, file_path: Path | None = None):
        if self.tree is None:
            raise RuntimeError("No SVG loaded.")
        target = file_path or self.file_path
        if target is None:
            raise RuntimeError("No save location available.")
        for element in self.editable_elements:
            normalize_element_colors_for_css(element)
        ET.register_namespace("", SVG_NS)
        self.tree.write(target, encoding="utf-8", xml_declaration=True)
        self.file_path = target
