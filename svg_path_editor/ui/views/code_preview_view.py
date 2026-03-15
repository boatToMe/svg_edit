import tkinter as tk
from tkinter import ttk


class SVGCodePreviewDialog:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.window: tk.Toplevel | None = None
        self.text: tk.Text | None = None
        self.confirm_button = None
        self.cancel_button = None
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

        text_frame = ttk.Frame(body)
        text_frame.pack(fill="both", expand=True)
        self.text = tk.Text(text_frame, wrap="none", font=("Consolas", 10))
        self.text.pack(side="left", fill="both", expand=True)
        y_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(body, orient="horizontal", command=self.text.xview)
        x_scroll.pack(fill="x")
        self.text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(8, 0))
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
        self.cancel_button.configure(text="取消" if not view_only else "关闭")
        if self.text is not None:
            self.text.configure(state="normal")
            self.text.delete("1.0", "end")
            self.text.insert("1.0", svg_code)
            self.text.configure(state="disabled")
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

    def _close(self):
        if self.window is None or not self.window.winfo_exists():
            return
        self.window.grab_release()
        self.window.destroy()
        self.window = None
