from .base import BaseController


class CodeController(BaseController):
    def bind_events(self):
        self.view.inspector_notebook.bind("<<NotebookTabChanged>>", self.app._guard(self.on_tab_changed, "切换检查器标签页"))

    def on_tab_changed(self, _event=None):
        if self.view.inspector_notebook.index("current") != 1:
            return
        self.refresh_code_view()

    def refresh_code_view(self):
        if self.session.document.root is None:
            self.view.set_code_text("请先打开一个 SVG 文件。")
            return
        self.view.set_code_text(self.session.document.to_svg_string())
