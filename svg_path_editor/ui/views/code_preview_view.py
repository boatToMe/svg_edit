import tkinter as tk
from tkinter import ttk
from xml.dom import minidom

from .components.line_number_text import LineNumberText


class SVGCodePreviewDialog:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.window: tk.Toplevel | None = None
        self.text: tk.Text | None = None
        self.confirm_button = None
        self.cancel_button = None
        self.format_button = None
        self._code_view = None
        self._confirmed = False
        self._view_only = False

    def ensure_window(self):
        if self.window is not None and self.window.winfo_exists():
            return self.window
        self.window = tk.Toplevel(self.root)
        self.window.title("保存前预览 SVG 代码")
        self.window.geometry("820x680")
        self.window.minsize(560, 420)
        self.window.transient(self.root)
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)

        body = ttk.Frame(self.window, padding=8)
        body.pack(fill="both", expand=True)
        self.message_label = ttk.Label(body, text="下面是即将保存的 SVG 代码。确认无误后再保存。", justify="left")
        self.message_label.pack(anchor="w", pady=(0, 8))

        self._code_view = LineNumberText(body, wrap="char")
        self._code_view.frame.pack(fill="both", expand=True)
        self.text = self._code_view.text

        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(8, 0))
        self.format_button = ttk.Button(buttons, text="整理代码格式", command=self._on_format)
        self.format_button.pack(side="left")
        self.confirm_button = ttk.Button(buttons, text="确认保存", command=self._on_confirm)
        self.confirm_button.pack(side="right")
        self.cancel_button = ttk.Button(buttons, text="取消", command=self._on_cancel)
        self.cancel_button.pack(side="right", padx=(0, 8))
        return self.window

    def ask(self, svg_code: str) -> bool:
        self._show(svg_code, title="保存前预览 SVG 代码", message="下面是即将保存的 SVG 代码。确认无误后再保存。", confirm_text="确认保存", view_only=False)
        return self._confirmed

    def show(self, svg_code: str):
        self._show(svg_code, title="当前 SVG 代码", message="下面是当前 SVG 代码。", confirm_text="关闭", view_only=True)

    def _show(self, svg_code: str, title: str, message: str, confirm_text: str, view_only: bool):
        window = self.ensure_window()
        self._confirmed = False
        self._view_only = view_only
        window.title(title)
        self.message_label.configure(text=message)
        self.confirm_button.configure(text=confirm_text)
        if view_only:
            self.cancel_button.pack_forget()
        else:
            self.cancel_button.pack(side="right", padx=(0, 8))
        self._code_view.set_text(svg_code, state="disabled")
        window.deiconify()
        window.lift()
        window.focus_force()
        window.grab_set()
        self.root.wait_window(window)

    def _on_confirm(self):
        self._confirmed = True
        self._close()

    def _on_cancel(self):
        self._confirmed = False
        self._close()

    def _on_format(self):
        if self._code_view is None:
            return
        current_code = self._code_view.get_text()
        if not current_code:
            return
        try:
            dom = minidom.parseString(current_code)
            formatted = dom.toprettyxml(indent="  ", encoding=None)
            lines = formatted.split("\n")
            if lines and lines[0].startswith("<?xml"):
                lines = lines[1:]
            formatted = "\n".join(lines).strip()
            self._code_view.set_text(formatted, state="disabled")
        except Exception:
            pass

    def _close(self):
        if self.window is None or not self.window.winfo_exists():
            return
        self.window.grab_release()
        self.window.destroy()
        self.window = None
