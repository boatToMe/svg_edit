import ctypes
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
    from tkwebview.core import webview_native_handle_kind_t
except Exception:  # pragma: no cover - runtime fallback
    TkWebview = None
    webview_native_handle_kind_t = None


WM_MOUSEWHEEL = 0x020A
GWL_WNDPROC = -4

if sys.platform == "win32":
    user32 = ctypes.windll.user32
    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p)
    SetWindowLongPtr = user32.SetWindowLongPtrW
    SetWindowLongPtr.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    SetWindowLongPtr.restype = ctypes.c_void_p
    CallWindowProc = user32.CallWindowProcW
    CallWindowProc.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
    CallWindowProc.restype = ctypes.c_longlong
else:  # pragma: no cover - platform fallback
    user32 = None
    WNDPROC = None
    SetWindowLongPtr = None
    CallWindowProc = None


class _WheelEvent:
    def __init__(self, delta: int):
        self.delta = delta
        self.num = None


class BrowserPreview:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="浏览器预览", padding=8)
        self.viewport = ttk.Frame(self.frame)
        self.viewport.pack(fill="both", expand=True)
        self.browser: TkWebview | None = None
        self.fallback_label: ttk.Label | None = None
        self._last_html = ""
        self._pending_set_html = False
        self._mousewheel_bound = False
        self._wheel_callback = None
        self._native_browser_hwnd = None
        self._original_wndproc = None
        self._wndproc_ref = None
        self._build()

    def _build(self):
        if TkWebview is None:
            self._show_fallback("浏览器预览组件不可用，无法显示标准 SVG 预览。")
            return
        try:
            self.browser = TkWebview(self.viewport, width=480, height=480)
            self.browser.pack(fill="both", expand=True)
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

    def bind_mousewheel(self, callback):
        self._wheel_callback = callback
        if self._mousewheel_bound:
            return
        targets = [self.frame, self.viewport]
        if self.fallback_label is not None:
            targets.append(self.fallback_label)
        for target in targets:
            target.bind("<MouseWheel>", callback, add="+")
            target.bind("<Button-4>", callback, add="+")
            target.bind("<Button-5>", callback, add="+")
            target.bind("<Enter>", lambda _event, widget=target: widget.focus_set(), add="+")
        self._install_native_mousewheel_hook()
        self._mousewheel_bound = True

    def _install_native_mousewheel_hook(self):
        if self.browser is None or self._wheel_callback is None:
            return
        if sys.platform != "win32" or webview_native_handle_kind_t is None or SetWindowLongPtr is None:
            return
        if self._native_browser_hwnd is not None:
            return
        try:
            hwnd = self.browser.webview.get_native_handle(
                webview_native_handle_kind_t.WEBVIEW_NATIVE_HANDLE_KIND_UI_WIDGET
            )
        except Exception:
            return
        if not hwnd:
            return
        self._native_browser_hwnd = int(hwnd)

        @WNDPROC
        def _wndproc(hwnd_value, msg, wparam, lparam):
            if msg == WM_MOUSEWHEEL and self._wheel_callback is not None:
                delta = ctypes.c_short((int(wparam) >> 16) & 0xFFFF).value
                self.frame.after_idle(lambda value=delta: self._dispatch_native_wheel(value))
                return 0
            return CallWindowProc(self._original_wndproc, hwnd_value, msg, wparam, lparam)

        self._wndproc_ref = _wndproc
        self._original_wndproc = SetWindowLongPtr(self._native_browser_hwnd, GWL_WNDPROC, self._wndproc_ref)

    def _dispatch_native_wheel(self, delta: int):
        if self._wheel_callback is None:
            return
        self._wheel_callback(_WheelEvent(delta))

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
            self._install_native_mousewheel_hook()
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
