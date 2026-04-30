from pathlib import Path
from tkinter import filedialog, messagebox

from ...application import DocumentContext, EditorSession, InteractionState
from .base import BaseController


class FileController(BaseController):
    def new_file(self, announce: bool = True):
        document_name = self.app.next_untitled_name()
        session = EditorSession()
        session.create_new_document()
        context = DocumentContext(name=document_name, session=session, state=InteractionState())
        status_text = f"已创建 {document_name}，可在右侧“图形”页插入基础图形。"
        self.app.register_document(context, activate=True, refit=True, status_text=status_text, restore_draft=False)
        if not announce:
            self.view.set_status(status_text)

    def open_file(self):
        file_name = filedialog.askopenfilename(title="打开 SVG", filetypes=[("SVG 文件", "*.svg"), ("所有文件", "*.*")])
        if not file_name:
            return
        try:
            session = EditorSession()
            labels = session.open_file(Path(file_name))
        except Exception as exc:
            messagebox.showerror("打开失败", str(exc))
            return
        if labels:
            session.load_shape(0)
            if session.document.view_box is not None:
                min_x, min_y, width, height = session.document.view_box
                status_text = f"已加载 {len(labels)} 个可编辑元素；viewBox 中心=({min_x + width / 2:g}, {min_y + height / 2:g})"
            else:
                status_text = f"已加载 {len(labels)} 个可编辑元素。"
        else:
            status_text = "SVG 已加载，但没有找到支持编辑的图形。"
        context = DocumentContext(name=Path(file_name).name, session=session, state=InteractionState())
        self.app.register_document(context, activate=True, refit=True, status_text=status_text, restore_draft=False)

    def _preview_svg_before_save(self) -> bool:
        svg_code = self.session.document.to_svg_string()
        return self.app.code_preview_view.ask(svg_code)

    def save_file(self):
        try:
            if self.session.document.file_path is None:
                self.save_file_as()
                return
            self.app.text_controller.commit_text_if_needed(record_history=False)
            if not self._preview_svg_before_save():
                self.view.set_status("已取消保存。")
                return
            self.session.save()
            self.app.rename_active_document(Path(self.session.document.file_path).name)
            self.app.code_controller.refresh_if_visible()
            self.view.set_status(f"已保存到 {self.session.document.file_path}")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def save_file_as(self):
        if self.session.document.tree is None:
            messagebox.showinfo("无可保存内容", "请先打开或新建一个 SVG 文件。")
            return
        file_name = filedialog.asksaveasfilename(title="另存为", defaultextension=".svg", filetypes=[("SVG 文件", "*.svg"), ("所有文件", "*.*")])
        if not file_name:
            return
        try:
            self.app.text_controller.commit_text_if_needed(record_history=False)
            if not self._preview_svg_before_save():
                self.view.set_status("已取消另存为。")
                return
            self.session.save(Path(file_name))
            self.app.rename_active_document(Path(file_name).name)
            self.app.code_controller.refresh_if_visible()
            self.view.set_status(f"已保存到 {file_name}")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def on_document_tab_selected(self, _event=None):
        index = self.view.get_selected_document_index()
        if index is not None:
            self.app.activate_document(index, refit=False, restore_draft=True)

    def on_element_selected(self, _event=None):
        index = self.view.get_selected_element_index()
        if index is not None:
            self.load_path(index, show_toast=True)

    def reload_selected_path(self):
        if self.session.current_index is not None:
            self.load_path(self.session.current_index, show_toast=False)

    def load_path(self, index: int, show_toast: bool = True, refit: bool = True):
        try:
            shape = self.session.load_shape(index)
        except Exception as exc:
            messagebox.showerror("不支持的元素", str(exc))
            return
        self.app.current_document.clear_draft()
        self.view.select_element(index)
        self.state.focus_handle = self.session.handles[0] if self.session.handles else None
        self.state.text_selected_handle_indices = {0} if self.session.handles else set()
        self.app.text_controller.set_geometry_text(shape.raw_text)
        self.app.preview_controller.refresh_target_options()
        if refit:
            self.app.canvas_controller.fit_view()
        self.app.redraw()
        element_name = self.session.get_element_name(index)
        self.view.set_status(f"正在编辑 {element_name}")
        if show_toast:
            self.app.canvas_controller.show_toast(f"已选中 {element_name}")
