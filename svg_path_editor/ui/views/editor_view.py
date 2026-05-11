import tkinter as tk
from tkinter import ttk

from .components import DocumentTabBar, EditorToolbar, EditorWorkspace


class EditorView:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SVG 可视化编辑器")

        self.status_var = tk.StringVar(value="请先打开或新建一个 SVG 文件。")
        self.guide_axis_var = tk.StringVar(value="x")
        self.guide_value_var = tk.StringVar()
        self.drag_step_var = tk.StringVar(value="1")

        self._build_ui()

    def _build_ui(self):
        self.root.geometry("1680x920")
        self.root.minsize(1480, 820)

        self.toolbar = EditorToolbar(self.root)
        self.document_tabs = DocumentTabBar(self.root)
        self.document_tabs.pack(fill="x")
        self.workspace = EditorWorkspace(
            self.root,
            self.guide_axis_var,
            self.guide_value_var,
            self.drag_step_var,
        )

        self.new_button = self.toolbar.new_button
        self.open_button = self.toolbar.open_button
        self.save_button = self.toolbar.save_button
        self.save_as_button = self.toolbar.save_as_button
        self.preview_button = self.toolbar.preview_button

        self.preview_host = self.workspace.preview_pane.host
        self.canvas = self.workspace.canvas_pane.canvas
        self.inspector = self.workspace.inspector

        self.element_manager = self.inspector.element_manager
        self.text = self.inspector.text
        self.code_text = self.inspector.code_text
        self.strip_css_button = self.inspector.strip_css_button
        self.preview_saved_code_button = self.inspector.preview_saved_code_button
        self.inspector_notebook = self.inspector.notebook
        self.apply_text_button = self.inspector.apply_text_button
        self.reload_button = self.inspector.reload_button
        self.batch_replace_button = self.inspector.batch_replace_button
        self.shape_buttons = self.inspector.shape_buttons
        self.drag_step_entry = self.inspector.drag_step_entry
        self.guide_axis_combo = self.inspector.guide_axis_combo
        self.guide_value_entry = self.inspector.guide_value_entry
        self.add_guide_button = self.inspector.add_guide_button
        self.add_focus_x_button = self.inspector.add_focus_x_button
        self.add_focus_y_button = self.inspector.add_focus_y_button
        self.delete_guide_button = self.inspector.delete_guide_button
        self.clear_guides_button = self.inspector.clear_guides_button
        self.guide_listbox = self.inspector.guide_listbox

        ttk.Label(self.root, textvariable=self.status_var, anchor="w", padding=(10, 6)).pack(fill="x")
        self.set_document_loaded(False)
        self.set_code_text("请先打开或新建一个 SVG 文件。")

    def set_document_loaded(self, loaded: bool):
        button_state = "normal" if loaded else "disabled"
        entry_state = "normal" if loaded else "disabled"
        combo_state = "readonly" if loaded else "disabled"

        self.save_button.configure(state=button_state)
        self.save_as_button.configure(state=button_state)
        self.preview_button.configure(state=button_state)
        self.text.configure(state=entry_state)
        self.apply_text_button.configure(state=button_state)
        self.reload_button.configure(state=button_state)
        self.batch_replace_button.configure(state=button_state)
        self.drag_step_entry.configure(state=entry_state)
        self.guide_axis_combo.configure(state=combo_state)
        self.guide_value_entry.configure(state=entry_state)
        self.add_guide_button.configure(state=button_state)
        self.add_focus_x_button.configure(state=button_state)
        self.add_focus_y_button.configure(state=button_state)
        self.delete_guide_button.configure(state=button_state)
        self.clear_guides_button.configure(state=button_state)
        self.guide_listbox.configure(state="normal" if loaded else "disabled")
        self.strip_css_button.configure(state=button_state)
        self.preview_saved_code_button.configure(state=button_state)
        for button in self.shape_buttons.values():
            button.configure(state=button_state)

    def set_element_labels(self, labels: list[str]):
        self.element_manager.set_labels(labels)

    def set_document_tabs(self, labels: list[str], active_index: int | None):
        self.document_tabs.set_tabs(labels, active_index)

    def get_selected_document_index(self) -> int | None:
        return self.document_tabs.get_selected_index()

    def select_element(self, index: int | None):
        self.element_manager.select(index)

    def get_selected_element_index(self) -> int | None:
        return self.element_manager.get_selected_index()

    def set_geometry_text(self, text: str):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)

    def get_geometry_text(self) -> str:
        return self.text.get("1.0", "end").strip()

    def set_code_text(self, text: str):
        self.code_text.configure(state="normal")
        self.code_text.delete("1.0", "end")
        self.code_text.insert("1.0", text)
        self.code_text.configure(state="disabled")

    def get_drag_step(self) -> float:
        try:
            value = float(self.drag_step_var.get().strip())
        except ValueError:
            return 1.0
        return value if value > 0 else 1.0

    def set_status(self, text: str):
        self.status_var.set(text)

    def refresh_guide_list(self, guides: list[tuple[str, float]], selected_index: int | None):
        self.guide_listbox.delete(0, "end")
        for idx, (axis, value) in enumerate(guides, start=1):
            self.guide_listbox.insert("end", f"辅助线{idx}: {axis} = {value:g}")
        if selected_index is not None and selected_index < len(guides):
            self.guide_listbox.selection_set(selected_index)
            self.guide_listbox.activate(selected_index)

    def get_selected_guide_index(self) -> int | None:
        selection = self.guide_listbox.curselection()
        return selection[0] if selection else None
