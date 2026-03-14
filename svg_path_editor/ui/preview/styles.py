import re


STYLE_RULE_RE = re.compile(r"\.([A-Za-z0-9_-]+)\s*\{([^}]*)\}", re.S)
HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
SCOPE_ALL = "整体图形"
INHERIT = "继承"
LIGHT_THEME = "亮色"
DARK_THEME = "暗色"
PREVIEW_THEME_STYLES = {
    LIGHT_THEME: {"background": "#ffffff", "border": "#cbd5e1"},
    DARK_THEME: {"background": "#111827", "border": "#334155"},
}


def parse_style_rules(root, strip_ns):
    rules: dict[str, dict[str, str]] = {}
    if root is None:
        return rules
    for elem in root.iter():
        if strip_ns(elem.tag) != "style" or elem.text is None:
            continue
        for class_name, body in STYLE_RULE_RE.findall(elem.text):
            declarations = {}
            for part in body.split(";"):
                if ":" not in part:
                    continue
                key, value = part.split(":", 1)
                declarations[key.strip()] = value.strip()
            if declarations:
                rules[class_name] = declarations
    return rules


def resolve_style(element, style_rules):
    style: dict[str, str] = {}
    class_names = element.get("class", "").split()
    for class_name in class_names:
        style.update(style_rules.get(class_name, {}))
    inline_style = element.get("style", "")
    for part in inline_style.split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        style[key.strip()] = value.strip()
    for key in (
        "fill",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "opacity",
        "fill-opacity",
        "stroke-opacity",
        "color",
    ):
        value = element.get(key)
        if value is not None:
            style[key] = value
    return style


def merge_style_overrides(style: dict[str, str], global_override: dict[str, str], element_override: dict[str, str] | None):
    merged = dict(style)
    merged.update(global_override)
    if element_override:
        merged.update(element_override)
    return merged


def get_theme_style(theme_name: str):
    return PREVIEW_THEME_STYLES.get(theme_name, PREVIEW_THEME_STYLES[LIGHT_THEME])


def normalize_color(value: str | None, fallback: str | None = None):
    if value is None:
        return fallback
    text = value.strip()
    if not text or text.lower() == "none":
        return ""
    lowered = text.lower()
    if lowered == "currentcolor" or lowered.startswith("var("):
        return fallback
    return text


def stroke_width(style: dict[str, str], scale: float):
    raw = style.get("stroke-width", "1").strip().replace("px", "")
    try:
        width = float(raw)
    except ValueError:
        width = 1.0
    return max(1.0, width * scale)


def corner_radius(style: dict[str, str], scale: float):
    raw = style.get("_corner_radius", "0").strip()
    try:
        value = float(raw)
    except ValueError:
        value = 0.0
    return max(0.0, value * scale)
