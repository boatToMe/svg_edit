import ctypes
from queue import Empty, Queue
import sys
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk

from ...preview.browser_renderer import PREVIEW_WHEEL_BRIDGE_NAME


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


if sys.platform == "win32":
    user32 = ctypes.windll.user32
    SetFocus = user32.SetFocus
    SetFocus.argtypes = [ctypes.c_void_p]
    SetFocus.restype = ctypes.c_void_p
else:  # pragma: no cover - platform fallback
    user32 = None
    SetFocus = None


class BrowserPreview:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="浏览器预览", padding=8)
        self.viewport = ttk.Frame(self.frame, takefocus=True)
        self.viewport.pack(fill="both", expand=True)
        self.browser: TkWebview | None = None
        self.fallback_label: ttk.Label | None = None
        self._last_html = ""
        self._pending_set_html = False
        self._wheel_delta_callback: Callable[[float], None] | None = None
        self._wheel_bridge_bound = False
        self._wheel_delta_queue: Queue[float] = Queue()
        self._wheel_pump_after_id = None
        self._wheel_pump_interval_ms = 16
        self._build()
        self._schedule_wheel_pump()

    def _build(self):
        if TkWebview is None:
            self._show_fallback("浏览器预览组件不可用，无法显示标准 SVG 预览。")
            return
        try:
            self.browser = TkWebview(self.viewport, width=480, height=480)
            self.browser.pack(fill="both", expand=True)
            self._register_wheel_bridge()
        except Exception:
            self.browser = None
            self._show_fallback("浏览器预览组件初始化失败，无法显示标准 SVG 预览。")

    def _show_fallback(self, text: str):
        if self.fallback_label is None:
            self.fallback_label = ttk.Label(
                self.viewport,
                text=text,
                justify="center",
                anchor="center",
            )
            self.fallback_label.pack(fill="both", expand=True, padx=16, pady=16)
        else:
            self.fallback_label.configure(text=text)

    def _register_wheel_bridge(self):
        if self.browser is None or self._wheel_bridge_bound:
            return
        try:
            self.browser.bindjs(PREVIEW_WHEEL_BRIDGE_NAME, self._handle_wheel_delta)
        except Exception:
            return
        self._wheel_bridge_bound = True

    def bind_wheel_delta(self, callback):
        self._wheel_delta_callback = callback

    def _handle_wheel_delta(self, delta_y):
        try:
            wheel_delta = float(delta_y)
        except (TypeError, ValueError):
            return None
        self._wheel_delta_queue.put(wheel_delta)
        return None

    def _schedule_wheel_pump(self):
        if self._wheel_pump_after_id is not None or not self.frame.winfo_exists():
            return
        self._wheel_pump_after_id = self.frame.after(self._wheel_pump_interval_ms, self._drain_wheel_deltas)

    def _drain_wheel_deltas(self):
        self._wheel_pump_after_id = None
        if not self.frame.winfo_exists():
            return
        while True:
            try:
                delta_y = self._wheel_delta_queue.get_nowait()
            except Empty:
                break
            self._dispatch_wheel_delta(delta_y)
        self._schedule_wheel_pump()

    def _dispatch_wheel_delta(self, delta_y: float):
        if self._wheel_delta_callback is None or not self.frame.winfo_exists():
            return
        self._wheel_delta_callback(delta_y)

    def _focus_preview_host(self):
        host = self.browser if self.browser is not None else self.viewport
        if not host.winfo_exists():
            return
        try:
            host.focus_set()
        except Exception:
            pass
        if sys.platform != "win32" or SetFocus is None:
            return
        try:
            SetFocus(ctypes.c_void_p(host.winfo_id()))
        except Exception:
            return

    def is_available(self) -> bool:
        return self.browser is not None

    def get_viewport_size(self) -> tuple[int, int]:
        self.viewport.update_idletasks()
        return max(1, self.viewport.winfo_width()), max(1, self.viewport.winfo_height())

    def _apply_pending_html(self):
        self._pending_set_html = False
        if self.browser is None:
            self._show_fallback("浏览器预览组件不可用，无法显示标准 SVG 预览。")
            return
        try:
            self.browser.set_html(self._last_html)
            self._focus_preview_host()
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
