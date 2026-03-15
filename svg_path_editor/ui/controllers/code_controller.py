from tkinter import messagebox

from .base import BaseController


class CodeController(BaseController):
    CODE_TAB_INDEX = 1

    def bind_events(self):
        self.view.inspector_notebook.add_tab_changed_handler(self.app._guard(self.on_tab_changed, "切换检查器标签页"))
        self.view.strip_css_button.configure(command=self.app._guard(self.strip_all_css, "去除所有 CSS"))
        self.view.preview_saved_code_button.configure(command=self.app._guard(self.preview_saved_code, "预览结果代码"))

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
