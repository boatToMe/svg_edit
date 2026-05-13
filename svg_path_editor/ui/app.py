import tkinter as tk

from ..application import DocumentContext
from .views import EditorView, PreviewWindow, SVGCodePreviewDialog
from .controllers import CanvasController, CodeController, FileController, GuideController, PreviewController, ShapeController, ShortcutController, TextController
from . import rendering


class SVGPathEditor:
    def __init__(self, root: tk.Tk, crash_handler=None):
        self.root = root
        self.crash_handler = crash_handler
        self.view = EditorView(root)
        self.preview_view = PreviewWindow(self.view.preview_host)
        self.code_preview_view = SVGCodePreviewDialog(root)
        self.documents: list[DocumentContext] = []
        self.active_document_index: int | None = None
        self._next_untitled_index = 1
        self._pan_origin = None

        self.file_controller = FileController(self)
        self.guide_controller = GuideController(self)
        self.shape_controller = ShapeController(self)
        self.text_controller = TextController(self)
        self.canvas_controller = CanvasController(self)
        self.preview_controller = PreviewController(self)
        self.code_controller = CodeController(self)
        self.shortcut_controller = ShortcutController(self)

        self._bind_events()
        self.file_controller.new_file(announce=False)
        self.preview_controller.open_preview()

    @property
    def current_document(self) -> DocumentContext:
        if self.active_document_index is None or self.active_document_index >= len(self.documents):
            raise RuntimeError("No active document.")
        return self.documents[self.active_document_index]

    @property
    def session(self):
        return self.current_document.session

    @property
    def state(self):
        return self.current_document.state

    def _guard(self, callback, source: str):
        if self.crash_handler is None:
            return callback
        return self.crash_handler.wrap(callback, source)

    def _bind_events(self):
        self.view.new_button.configure(command=self._guard(self.file_controller.new_file, "新建 SVG"))
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
        self.view.document_tabs.add_tab_changed_handler(self._guard(self.file_controller.on_document_tab_selected, "切换文档标签页"))

        for shape_key, button in self.view.shape_buttons.items():
            button.configure(command=self._guard(lambda key=shape_key: self.shape_controller.insert_basic_shape(key), f"插入基础图形 {shape_key}"))

        self.view.element_manager.on_select(self._guard(lambda index: self.file_controller.on_element_selected(index), "选择元素"))
        self.view.element_manager.on_delete(self._guard(lambda index: self.file_controller.delete_element(index), "删除元素"))
        self.view.strip_css_button.configure(command=self._guard(self.code_controller.strip_all_css, "去除所有 CSS"))
        self.view.preview_saved_code_button.configure(command=self._guard(self.code_controller.preview_saved_code, "预览结果代码"))
        self.view.format_code_button.configure(command=self._guard(self.code_controller.format_code, "整理代码格式"))
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

    def next_untitled_name(self) -> str:
        name = f"未命名 {self._next_untitled_index}"
        self._next_untitled_index += 1
        return name

    def rename_active_document(self, name: str):
        self.current_document.name = name
        self.refresh_document_tabs()

    def refresh_document_tabs(self):
        self.view.set_document_tabs([document.name for document in self.documents], self.active_document_index)
        self._update_window_title()

    def _update_window_title(self):
        if self.active_document_index is None or not self.documents:
            self.root.title("SVG 可视化编辑器")
            return
        self.root.title(f"{self.current_document.name} - SVG 可视化编辑器")

    def capture_active_geometry_draft(self):
        if self.active_document_index is None or not self.documents or self.session.current_index is None:
            return
        self.current_document.remember_draft(self.session.current_index, self.view.get_geometry_text())

    def register_document(self, context: DocumentContext, *, activate: bool = True, refit: bool = True, status_text: str | None = None, restore_draft: bool = False):
        self.documents.append(context)
        index = len(self.documents) - 1
        self.refresh_document_tabs()
        if activate:
            self.activate_document(index, refit=refit, status_text=status_text, restore_draft=restore_draft)
        return index

    def activate_document(self, index: int, *, refit: bool = False, status_text: str | None = None, restore_draft: bool = True):
        if index < 0 or index >= len(self.documents):
            return
        if self.active_document_index is not None and self.active_document_index < len(self.documents):
            self.capture_active_geometry_draft()
        self.active_document_index = index
        self.preview_controller.reset_document_state()
        self.refresh_document_tabs()
        self.refresh_active_document_view(refit=refit, restore_draft=restore_draft)
        if status_text is not None:
            self.view.set_status(status_text)

    def refresh_active_document_view(self, *, refit: bool = False, restore_draft: bool = False):
        if self.active_document_index is None:
            return
        loaded = self.session.document.root is not None
        self.view.set_document_loaded(loaded)
        self.preview_view.set_document_loaded(loaded)
        self.view.set_element_labels(self.session.get_element_labels())
        self.guide_controller.refresh_guide_listbox()
        if self.session.current_index is None and self.session.document.editable_elements:
            self.session.load_shape(0)
        if self.session.current_index is not None:
            current_index = self.session.current_index
            draft_index = self.current_document.draft_index
            draft_text = self.current_document.draft_text
            self.file_controller.load_path(current_index, show_toast=False, refit=refit)
            if restore_draft and draft_index == current_index:
                self.text_controller.set_geometry_text(draft_text)
                self.redraw()
            return

        self.state.focus_handle = None
        self.state.active_handle = None
        self.state.handle_text_spans = []
        self.state.text_selected_handle_indices = set()
        if refit:
            self.canvas_controller.fit_view()
        self.view.select_element(None)
        self.view.set_geometry_text("")
        self.text_controller.rebuild_text_mappings()
        self.text_controller.refresh_text_highlights()
        self.preview_controller.refresh_target_options()
        self.redraw()
        self.code_controller.refresh_code_view()
        if loaded:
            self.view.set_status("当前文档还没有图形，可在右侧“图形”页插入基础图形。")
