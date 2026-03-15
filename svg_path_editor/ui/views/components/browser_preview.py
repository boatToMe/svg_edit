import sys
from pathlib import Path
from tkinter import ttk


def _vendor_root() -> Path:
    return Path(__file__).resolve().parents[4] / "vendor"


vendor_root = _vendor_root()
if vendor_root.exists():
    vendor_text = str(vendor_root)
    if vendor_text not in sys.path:
        sys.path.insert(0, vendor_text)

try:
    from tkwebview import TkWebview
except Exception:  # pragma: no cover - runtime fallback
    TkWebview = None


class BrowserPreview:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.browser: TkWebview | None = None
        self.fallback_label: ttk.Label | None = None
        self._last_html = ""
        self._sync_handler = None
        self._pending_set_html = False
        self._build()

    def _build(self):
        if TkWebview is None:
            self._show_fallback("浏览器预览组件不可用，无法显示标准 SVG 预览。")
            return
        try:
            self.browser = TkWebview(self.frame, width=480, height=480)
            self.browser.pack(fill="both", expand=True)
        except Exception:
            self.browser = None
            self._show_fallback("浏览器预览组件初始化失败，无法显示标准 SVG 预览。")

    def _show_fallback(self, text: str):
        if self.fallback_label is None:
            self.fallback_label = ttk.Label(
                self.frame,
                text=text,
                justify="center",
                anchor="center",
            )
            self.fallback_label.pack(fill="both", expand=True, padx=16, pady=16)
        else:
            self.fallback_label.configure(text=text)

    def _handle_preview_sync(self, payload):
        if self._sync_handler is None:
            return None
        self.frame.after(0, lambda: self._sync_handler(payload))
        return "ok"

    def set_sync_handler(self, handler):
        self._sync_handler = handler

    def is_available(self) -> bool:
        return self.browser is not None

    def get_viewport_size(self) -> tuple[int, int]:
        self.frame.update_idletasks()
        return max(1, self.frame.winfo_width()), max(1, self.frame.winfo_height())

    def _apply_pending_html(self):
        self._pending_set_html = False
        if self.browser is None:
            self._show_fallback("浏览器预览组件不可用，无法显示标准 SVG 预览。")
            return
        try:
            self.browser.set_html(self._last_html)
        except Exception:
            self.browser = None
            self._show_fallback("浏览器预览组件加载 HTML 失败，无法显示标准 SVG 预览。")

    def set_html(self, html_text: str):
        self._last_html = html_text
        if self.browser is None:
            self._show_fallback("浏览器预览组件不可用，无法显示标准 SVG 预览。")
            return
        if self._pending_set_html:
            return
        self._pending_set_html = True
        self.frame.after_idle(self._apply_pending_html)

    def reload(self):
        if self.browser is None or not self._last_html:
            return
        self.set_html(self._last_html)
