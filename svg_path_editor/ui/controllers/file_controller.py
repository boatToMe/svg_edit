from pathlib import Path
from tkinter import filedialog, messagebox

from .base import BaseController


class FileController(BaseController):
    def open_file(self):
        file_name = filedialog.askopenfilename(title="打开 SVG", filetypes=[("SVG 文件", "*.svg"), ("所有文件", "*.*")])
        if not file_name:
            return
        try:
            labels = self.session.open_file(Path(file_name))
        except Exception as exc:
            messagebox.showerror("打开失败", str(exc))
            return

        self.view.set_document_loaded(True)
        self.app.preview_view.set_document_loaded(True)
        self.view.set_element_labels(labels)
        self.state.custom_guides.clear()
        self.state.selected_guide_index = None
        self.state.active_guide_index = None
        self.state.drag_shape_before_text = None
        self.state.drag_guide_before_value = None
        self.state.text_selected_handle_indices = set()
        self.app.guide_controller.refresh_guide_listbox()
        self.app.preview_controller.refresh_target_options()

        if labels:
            self.view.select_element(0)
            self.load_path(0, show_toast=False)
            if self.session.document.view_box is not None:
                min_x, min_y, width, height = self.session.document.view_box
                self.view.set_status(f"已加载 {len(labels)} 个可编辑元素；viewBox 中心=({min_x + width / 2:g}, {min_y + height / 2:g})")
            else:
                self.view.set_status(f"已加载 {len(labels)} 个可编辑元素。")
        else:
            self.session.current_index = None
            self.session.current_shape = None
            self.state.focus_handle = None
            self.view.set_geometry_text("")
            self.view.canvas.delete("all")
            self.view.select_element(None)
            self.view.set_status("SVG 已加载，但没有找到支持编辑的元素。")

    def _preview_svg_before_save(self) -> bool:
        svg_code = self.session.document.to_svg_string()
        return self.app.code_preview_view.ask(svg_code)

    def save_file(self):
        try:
            self.app.text_controller.commit_text_if_needed(record_history=False)
            if not self._preview_svg_before_save():
                self.view.set_status("已取消保存。")
                return
            self.session.save()
            self.view.set_status(f"已保存到 {self.session.document.file_path}")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def save_file_as(self):
        if self.session.document.tree is None:
            messagebox.showinfo("无可保存内容", "请先打开一个 SVG 文件。")
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
            self.view.set_status(f"已保存到 {file_name}")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

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
