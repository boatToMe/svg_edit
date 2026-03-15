import copy
import html
from xml.etree import ElementTree as ET

from ...core import strip_ns


SVG_NS = "http://www.w3.org/2000/svg"
SUPPORTED_TAGS = {"path", "line", "polygon"}
FLASH_STROKE_WIDTH = "2.5"
STYLE_OVERRIDE_KEYS = {"fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin"}


class BrowserPreviewRenderer:
    def get_bounds(self, session):
        if session.document.view_box is not None:
            return session.document.view_box
        points = []
        for _idx, shape in session.get_display_shapes():
            for seg in shape.segments:
                points.append(seg.start)
                points.append(seg.end)
                points.extend(seg.controls)
        if not points:
            return (0.0, 0.0, 512.0, 512.0)
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        min_x = min(xs)
        min_y = min(ys)
        return (min_x, min_y, max(1.0, max(xs) - min_x), max(1.0, max(ys) - min_y))

    def build_document(self, session, target_width, theme_style, global_style_override, element_style_overrides, flash_color, is_flash_on):
        min_x, min_y, width, height = self.get_bounds(session)
        width_px = max(1, int(target_width))
        height_px = max(1, int(round(width_px * height / max(width, 1.0))))

        root_copy = copy.deepcopy(session.document.root)
        elements = [elem for elem in root_copy.iter() if strip_ns(elem.tag) in SUPPORTED_TAGS]
        for index, element in enumerate(elements):
            override = dict(global_style_override)
            override.update(element_style_overrides.get(index, {}))
            if is_flash_on(index):
                self._apply_flash_override(element, flash_color)
            self._apply_override(element, override)

        ET.register_namespace("", SVG_NS)
        svg_markup = ET.tostring(root_copy, encoding="unicode")
        title = html.escape(str(session.document.file_path) if session.document.file_path else "SVG 预览")
        html_text = self._wrap_html(svg_markup, title, width_px, theme_style)
        return html_text, width_px, height_px

    def _wrap_html(self, svg_markup: str, title: str, width_px: int, theme_style: dict[str, str]) -> str:
        return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{title}</title>
  <style>
    html, body {{
      margin: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
    }}
    body {{
      display: grid;
      place-items: center;
      background: {theme_style['background']};
      color: #111827;
      font-family: "Segoe UI", sans-serif;
    }}
    .stage {{
      width: 100%;
      height: 100%;
      display: grid;
      place-items: center;
      box-sizing: border-box;
      padding: 24px;
    }}
    .frame {{
      width: min(calc(100vw - 48px), {width_px}px);
      max-width: 100%;
      display: grid;
      place-items: center;
      box-sizing: border-box;
    }}
    svg {{
      display: block;
      width: 100%;
      height: auto;
      overflow: visible;
      shape-rendering: geometricPrecision;
      text-rendering: geometricPrecision;
    }}
  </style>
</head>
<body>
  <div class=\"stage\">
    <div class=\"frame\">{svg_markup}</div>
  </div>
</body>
</html>
"""

    def _parse_style_attr(self, style_text: str) -> dict[str, str]:
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

    def _write_style_attr(self, element, style_map: dict[str, str]):
        if style_map:
            element.set("style", "; ".join(f"{key}: {value}" for key, value in style_map.items()))
        elif "style" in element.attrib:
            del element.attrib["style"]

    def _set_override_property(self, element, key: str, value: str):
        if key in STYLE_OVERRIDE_KEYS:
            style_map = self._parse_style_attr(element.get("style", ""))
            if value == "":
                style_map.pop(key, None)
            else:
                style_map[key] = value
            self._write_style_attr(element, style_map)
            return
        if value == "":
            if key in element.attrib:
                del element.attrib[key]
            return
        element.set(key, value)

    def _apply_override(self, element, override: dict[str, str]):
        for key, value in override.items():
            if key == "_corner_radius":
                continue
            self._set_override_property(element, key, value)

    def _apply_flash_override(self, element, flash_color: str):
        tag = strip_ns(element.tag)
        if tag == "line":
            self._set_override_property(element, "stroke", flash_color)
            self._set_override_property(element, "stroke-width", element.get("stroke-width") or FLASH_STROKE_WIDTH)
            return
        fill_value = element.get("fill", "").strip().lower()
        if fill_value != "none":
            self._set_override_property(element, "fill", flash_color)
        self._set_override_property(element, "stroke", flash_color)
        self._set_override_property(element, "stroke-width", element.get("stroke-width") or FLASH_STROKE_WIDTH)
