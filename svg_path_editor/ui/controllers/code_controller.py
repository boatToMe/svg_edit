from tkinter import messagebox
from xml.dom import minidom

from .base import BaseController


class CodeController(BaseController):
    CODE_TAB_INDEX = 1

    def bind_events(self):
        self.view.inspector_notebook.add_tab_changed_handler(self.app._guard(self.on_tab_changed, "切换检查器标签页"))
        self.view.strip_css_button.configure(command=self.app._guard(self.strip_all_css, "去除所有 CSS"))
        self.view.preview_saved_code_button.configure(command=self.app._guard(self.preview_saved_code, "预览结果代码"))
        self.view.toggle_line_numbers_button.configure(command=self.app._guard(self.toggle_line_numbers, "切换行号显示"))

    def on_tab_changed(self, _event=None):
        if self.view.inspector_notebook.index("current") != self.CODE_TAB_INDEX:
            return
        self.refresh_code_view()

    def refresh_if_visible(self):
        if self.view.inspector_notebook.index("current") == self.CODE_TAB_INDEX:
            self.refresh_code_view()

    def refresh_code_view(self):
        if self.session.document.root is None:
            self.view.set_code_text("请先打开一个 SVG 文件。")
            return
        self.view.set_code_text(self.app.preview_controller.get_preview_svg_code())

    def preview_saved_code(self):
        if self.session.document.root is None:
            return
        self.app.preview_controller.show_saved_svg_code()

    def strip_all_css(self):
        if self.session.document.root is None:
            return
        if not messagebox.askyesno("去除所有 CSS", "这会移除当前 SVG 中的 <style>、class 和内联 style。是否继续？", parent=self.root):
            return
        self.session.document.strip_all_css()
        self.refresh_code_view()
        self.app.redraw()
        self.view.set_status("已去除当前 SVG 中的所有 CSS。")

    def format_code(self):
        if self.session.document.root is None:
            return
        current_code = self.view.code_text.get("1.0", "end").strip()
        if not current_code:
            return
        try:
            dom = minidom.parseString(current_code)
            formatted = dom.toprettyxml(indent="  ", encoding=None)
            lines = formatted.split("\n")
            if lines and lines[0].startswith("<?xml"):
                lines = lines[1:]
            formatted = "\n".join(lines).strip()
            self.view.set_code_text(formatted)
            self.view.set_status("已整理代码格式。")
        except Exception as exc:
            messagebox.showerror("格式化失败", str(exc), parent=self.root)

    def toggle_line_numbers(self):
        code_view = self.view.inspector.code_view
        current = code_view.get_show_line_numbers()
        code_view.set_show_line_numbers(not current)
        if current:
            self.view.toggle_line_numbers_button.configure(text="显示行号")
            self.view.set_status("已隐藏行号。")
        else:
            self.view.toggle_line_numbers_button.configure(text="隐藏行号")
            self.view.set_status("已显示行号。")
