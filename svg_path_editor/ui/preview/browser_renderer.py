import copy
import html
from xml.etree import ElementTree as ET

from ...core import strip_ns


SVG_NS = "http://www.w3.org/2000/svg"
SUPPORTED_TAGS = {"path", "line", "polygon"}
FLASH_STROKE_WIDTH = "2.5"
STYLE_OVERRIDE_KEYS = {"fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin"}
PREVIEW_WHEEL_BRIDGE_NAME = "previewWheel"


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

    def build_svg_markup(
        self,
        session,
        global_style_override,
        element_style_overrides,
        flash_color,
        is_flash_on,
    ):
        root_copy = copy.deepcopy(session.document.root)
        elements = [elem for elem in root_copy.iter() if strip_ns(elem.tag) in SUPPORTED_TAGS]
        for index, element in enumerate(elements):
            override = dict(global_style_override)
            override.update(element_style_overrides.get(index, {}))
            if is_flash_on(index):
                self._apply_flash_override(element, flash_color)
            self._apply_override(element, override)

        ET.register_namespace("", SVG_NS)
        return ET.tostring(root_copy, encoding="unicode")

    def build_document(
        self,
        session,
        target_width,
        theme_style,
        global_style_override,
        element_style_overrides,
        flash_color,
        is_flash_on,
        zoom_multiplier=1.0,
    ):
        _min_x, _min_y, width, height = self.get_bounds(session)
        width_px = max(1, int(target_width))
        height_px = max(1, int(round(width_px * height / max(width, 1.0))))
        initial_scale = max(0.05, zoom_multiplier)
        rendered_width = max(1, int(round(width_px * initial_scale)))
        rendered_height = max(1, int(round(height_px * initial_scale)))
        zoom_percent = max(1, int(round(initial_scale * 100)))

        svg_markup = self.build_svg_markup(
            session=session,
            global_style_override=global_style_override,
            element_style_overrides=element_style_overrides,
            flash_color=flash_color,
            is_flash_on=is_flash_on,
        )
        title = html.escape(str(session.document.file_path) if session.document.file_path else "SVG 预览")
        html_text = self._wrap_html(svg_markup, title, width_px, height_px, initial_scale, theme_style)
        return html_text, rendered_width, rendered_height, zoom_percent

    def build_svg_code(
        self,
        session,
        global_style_override,
        element_style_overrides,
        flash_color,
        is_flash_on,
    ):
        svg_markup = self.build_svg_markup(
            session=session,
            global_style_override=global_style_override,
            element_style_overrides=element_style_overrides,
            flash_color=flash_color,
            is_flash_on=is_flash_on,
        )
        return '<?xml version="1.0" encoding="utf-8"?>\n' + svg_markup

    def _wrap_html(self, svg_markup: str, title: str, width_px: int, height_px: int, initial_scale: float, theme_style: dict[str, str]) -> str:
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    html, body {{
      margin: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
    }}
    body {{
      background: {theme_style['background']};
      color: #111827;
      font-family: "Segoe UI", sans-serif;
      user-select: none;
      cursor: default;
    }}
    #viewport {{
      position: relative;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      touch-action: none;
    }}
    #content {{
      position: absolute;
      left: 0;
      top: 0;
      transform-origin: 0 0;
      will-change: transform;
    }}
    svg {{
      display: block;
      width: {width_px}px;
      height: {height_px}px;
      overflow: visible;
      shape-rendering: geometricPrecision;
      text-rendering: geometricPrecision;
      pointer-events: none;
    }}
  </style>
</head>
<body>
  <div id="viewport"><div id="content">{svg_markup}</div></div>
  <script>
    (() => {{
      const viewport = document.getElementById('viewport');
      const content = document.getElementById('content');
      const baseWidth = {width_px};
      const baseHeight = {height_px};
      const initialScale = {initial_scale:.6f};
      let scale = initialScale;
      let translateX = 0;
      let translateY = 0;
      let dragging = false;
      let panMode = false;
      let dragStartX = 0;
      let dragStartY = 0;
      let dragOriginX = 0;
      let dragOriginY = 0;

      function applyTransform() {{
        content.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{scale}})`;
      }}

      function centerContent() {{
        const viewWidth = viewport.clientWidth;
        const viewHeight = viewport.clientHeight;
        translateX = Math.round((viewWidth - baseWidth * scale) / 2);
        translateY = Math.round((viewHeight - baseHeight * scale) / 2);
        applyTransform();
      }}

      async function notifyWheel(deltaY) {{
        if (deltaY === 0 || typeof window.{PREVIEW_WHEEL_BRIDGE_NAME} !== 'function') {{
          return;
        }}
        try {{
          await window.{PREVIEW_WHEEL_BRIDGE_NAME}(deltaY);
        }} catch (_error) {{
        }}
      }}

      window.addEventListener('keydown', event => {{
        if (event.code === 'Space') {{
          panMode = true;
          document.body.style.cursor = 'grab';
          event.preventDefault();
        }}
      }});

      window.addEventListener('keyup', event => {{
        if (event.code === 'Space') {{
          panMode = false;
          if (!dragging) {{
            document.body.style.cursor = 'default';
          }}
          event.preventDefault();
        }}
      }});

      viewport.addEventListener('mousedown', event => {{
        if (event.button !== 0 || !panMode) return;
        dragging = true;
        dragStartX = event.clientX;
        dragStartY = event.clientY;
        dragOriginX = translateX;
        dragOriginY = translateY;
        document.body.style.cursor = 'grabbing';
        event.preventDefault();
      }});

      viewport.addEventListener('wheel', event => {{
        if (event.deltaY === 0) return;
        event.preventDefault();
        notifyWheel(event.deltaY);
      }}, {{ passive: false }});

      window.addEventListener('mousemove', event => {{
        if (!dragging) return;
        translateX = dragOriginX + (event.clientX - dragStartX);
        translateY = dragOriginY + (event.clientY - dragStartY);
        applyTransform();
      }});

      window.addEventListener('mouseup', () => {{
        if (!dragging) return;
        dragging = false;
        document.body.style.cursor = panMode ? 'grab' : 'default';
      }});

      window.addEventListener('resize', centerContent);
      centerContent();
    }})();
  </script>
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
