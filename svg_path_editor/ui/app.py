import tkinter as tk

from ..application import EditorSession, InteractionState
from .views import EditorView, PreviewWindow, SVGCodePreviewDialog
from .controllers import CanvasController, CodeController, FileController, GuideController, PreviewController, ShortcutController, TextController
from . import rendering


class SVGPathEditor:
    def __init__(self, root: tk.Tk, crash_handler=None):
        self.root = root
        self.crash_handler = crash_handler
        self.view = EditorView(root)
        self.preview_view = PreviewWindow(self.view.preview_host)
        self.code_preview_view = SVGCodePreviewDialog(root)
        self.session = EditorSession()
        self.state = InteractionState()
        self._pan_origin = None

        self.file_controller = FileController(self)
        self.guide_controller = GuideController(self)
        self.text_controller = TextController(self)
        self.canvas_controller = CanvasController(self)
        self.preview_controller = PreviewController(self)
        self.code_controller = CodeController(self)
        self.shortcut_controller = ShortcutController(self)

        self._bind_events()
        self.preview_controller.open_preview()

    def _guard(self, callback, source: str):
        if self.crash_handler is None:
            return callback
        return self.crash_handler.wrap(callback, source)

    def _bind_events(self):
        self.view.open_button.configure(command=self._guard(self.file_controller.open_file, "打开文件"))
        self.view.save_button.configure(command=self._guard(self.file_controller.save_file, "保存文件"))
        self.view.save_as_button.configure(command=self._guard(self.file_controller.save_file_as, "另存为"))
        self.view.preview_button.configure(command=self._guard(self.preview_controller.open_preview, "打开预览"))
        self.view.apply_text_button.configure(command=self._guard(self.text_controller.apply_text, "应用几何文本"))
        self.view.reload_button.configure(command=self._guard(self.file_controller.reload_selected_path, "重新载入元素"))
        self.view.batch_replace_button.configure(command=self._guard(self.text_controller.batch_replace_selected_value, "批量修改同值"))
        self.view.add_guide_button.configure(command=self._guard(self.guide_controller.add_guide_from_input, "添加辅助线"))
        self.view.add_focus_x_button.configure(command=self._guard(lambda: self.guide_controller.add_focus_guides("x"), "添加焦点 X 辅助线"))
        self.view.add_focus_y_button.configure(command=self._guard(lambda: self.guide_controller.add_focus_guides("y"), "添加焦点 Y 辅助线"))
        self.view.delete_guide_button.configure(command=self._guard(self.guide_controller.delete_selected_guide, "删除选中辅助线"))
        self.view.clear_guides_button.configure(command=self._guard(self.guide_controller.clear_guides, "清空辅助线"))

        self.view.element_listbox.bind("<<ListboxSelect>>", self._guard(self.file_controller.on_element_selected, "选择元素"))
        self.view.guide_listbox.bind("<<ListboxSelect>>", self._guard(self.guide_controller.on_guide_selected, "选择辅助线"))
        self.view.canvas.bind("<Configure>", self._guard(lambda event: self.redraw(), "重绘画布"))
        self.view.canvas.bind("<ButtonPress-1>", self._guard(self.canvas_controller.on_left_down, "画布按下"))
        self.view.canvas.bind("<B1-Motion>", self._guard(self.canvas_controller.on_left_drag, "画布拖动"))
        self.view.canvas.bind("<ButtonRelease-1>", self._guard(self.canvas_controller.on_left_up, "画布释放"))
        self.view.canvas.bind("<MouseWheel>", self._guard(self.canvas_controller.on_mousewheel, "画布缩放"))
        self.view.text.bind("<ButtonRelease-1>", self._guard(self.text_controller.on_text_selection_changed, "几何文本选择"))
        self.view.text.bind("<KeyRelease>", self._guard(self.text_controller.on_text_key_release, "几何文本输入"))
        self.code_controller.bind_events()
        self.shortcut_controller.bind_shortcuts()

    def redraw(self):
        rendering.redraw(self)
        self.preview_controller.redraw_if_open()
        self.code_controller.refresh_if_visible()

    def get_focus_handle_index(self) -> int | None:
        return self.text_controller.get_focus_handle_index()
