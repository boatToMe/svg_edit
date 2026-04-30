import re
from tkinter import messagebox, simpledialog

from ...core import shape_to_text
from ...application import UpdateShapeCommand
from .base import BaseController


NUMBER_PATTERN = re.compile(r"[-+]?(?:\d+\.\d+|\d+\.|\.\d+|\d+)(?:[eE][-+]?\d+)?")


class TextController(BaseController):
    def apply_text(self):
        if self.session.current_index is None or self.session.current_shape is None:
            messagebox.showinfo("未选中图形", "请先在右侧列表中选择一个图形，或先插入基础图形。")
            return
        try:
            self.commit_text_if_needed(record_history=True)
            self.app.file_controller.load_path(self.session.current_index, show_toast=False, refit=False)
            self.view.set_status("已应用右侧几何文本。")
        except Exception as exc:
            messagebox.showerror("几何解析失败", str(exc))

    def commit_text_if_needed(self, record_history: bool):
        if self.session.current_index is None or self.session.current_shape is None:
            return
        raw_text = self.view.get_geometry_text()
        before_text = self.session.get_shape_text(self.session.current_index)
        if record_history and raw_text == before_text:
            return
        if record_history:
            shape = self._execute_shape_update(raw_text)
        else:
            shape = self.session.commit_text(raw_text)
        self.state.focus_handle = self.session.handles[0] if self.session.handles else None
        if self.session.handles and not self.state.text_selected_handle_indices:
            self.state.text_selected_handle_indices = {0}
        self.set_geometry_text(shape.raw_text)

    def _execute_shape_update(self, raw_text: str):
        if self.session.current_index is None:
            raise RuntimeError("No active shape.")
        before_text = self.session.get_shape_text(self.session.current_index)
        if raw_text == before_text:
            return self.session.current_shape
        command = UpdateShapeCommand(self.session, self.session.current_index, before_text, raw_text)
        self.session.history.execute(command)
        return self.session.current_shape

    def set_geometry_text(self, text: str):
        self.view.set_geometry_text(text)
        self.rebuild_text_mappings()
        self.refresh_text_highlights()

    def rebuild_text_mappings(self):
        text = self.view.text.get("1.0", "end-1c")
        number_matches = list(NUMBER_PATTERN.finditer(text))
        self.state.handle_text_spans = []
        pair_count = min(len(self.session.handles), len(number_matches) // 2)
        for handle_index in range(pair_count):
            x_match = number_matches[handle_index * 2]
            y_match = number_matches[handle_index * 2 + 1]
            self.state.handle_text_spans.append({
                "handle_index": handle_index,
                "x": (x_match.start(), x_match.end()),
                "y": (y_match.start(), y_match.end()),
                "x_text": x_match.group(0),
                "y_text": y_match.group(0),
            })

    def refresh_text_highlights(self):
        for tag in ("number_default", "number_focus", "number_selected"):
            self.view.text.tag_remove(tag, "1.0", "end")
        focus_index = self.get_focus_handle_index()
        for span in self.state.handle_text_spans:
            handle_index = span["handle_index"]
            color_tag = "number_default"
            if handle_index in self.state.text_selected_handle_indices:
                color_tag = "number_selected"
            elif focus_index is not None and handle_index == focus_index:
                color_tag = "number_focus"
            for key in ("x", "y"):
                start_offset, end_offset = span[key]
                self.view.text.tag_add(color_tag, f"1.0 + {start_offset} chars", f"1.0 + {end_offset} chars")

    def get_focus_handle_index(self) -> int | None:
        if self.state.focus_handle is None:
            return None
        for index, handle in enumerate(self.session.handles):
            if handle is self.state.focus_handle:
                return index
        return None

    def on_text_key_release(self, _event=None):
        self.root.after_idle(self.on_text_selection_changed)

    def on_text_selection_changed(self, _event=None):
        self.root.after_idle(self.sync_selection_from_text)

    def sync_selection_from_text(self):
        self.state.text_selected_handle_indices = set()
        try:
            sel_start = self.view.text.index("sel.first")
            sel_end = self.view.text.index("sel.last")
        except Exception:
            self.refresh_text_highlights()
            self.app.redraw()
            return
        for span in self.state.handle_text_spans:
            if self.selection_overlaps_range(sel_start, sel_end, span["x"]) or self.selection_overlaps_range(sel_start, sel_end, span["y"]):
                self.state.text_selected_handle_indices.add(span["handle_index"])
        if self.state.text_selected_handle_indices:
            first_index = min(self.state.text_selected_handle_indices)
            if first_index < len(self.session.handles):
                self.state.focus_handle = self.session.handles[first_index]
        self.refresh_text_highlights()
        self.app.redraw()

    def selection_overlaps_range(self, sel_start: str, sel_end: str, value_range: tuple[int, int]) -> bool:
        start_offset, end_offset = value_range
        range_start = f"1.0 + {start_offset} chars"
        range_end = f"1.0 + {end_offset} chars"
        return self.view.text.compare(sel_start, "<", range_end) and self.view.text.compare(sel_end, ">", range_start)

    def _index_to_offset(self, index: str) -> int:
        return len(self.view.text.get("1.0", index))

    def _get_selected_number_text(self) -> str | None:
        text = self.view.text.get("1.0", "end-1c")
        try:
            sel_start = self.view.text.index("sel.first")
            sel_end = self.view.text.index("sel.last")
            selected_text = self.view.text.get(sel_start, sel_end).strip()
            if NUMBER_PATTERN.fullmatch(selected_text):
                return selected_text
            start_offset = self._index_to_offset(sel_start)
            end_offset = self._index_to_offset(sel_end)
            matches = [match for match in NUMBER_PATTERN.finditer(text) if match.start() < end_offset and match.end() > start_offset]
            unique_numbers = list(dict.fromkeys(match.group(0) for match in matches))
            if len(unique_numbers) == 1:
                return unique_numbers[0]
        except Exception:
            pass

        insert_offset = self._index_to_offset(self.view.text.index("insert"))
        for match in NUMBER_PATTERN.finditer(text):
            if match.start() <= insert_offset <= match.end():
                return match.group(0)
        return None

    def batch_replace_selected_value(self):
        old_value = self._get_selected_number_text()
        if not old_value:
            messagebox.showinfo("未选中数字", "请先在几何数据区选中一个数字，或把光标放到数字上。")
            return
        new_value = simpledialog.askstring("批量修改同值", f"把所有 {old_value} 改为：", parent=self.root)
        if new_value is None:
            return
        new_value = new_value.strip()
        if not new_value:
            return
        text = self.view.text.get("1.0", "end-1c")
        number_pattern = re.compile(rf"(?<![A-Za-z0-9_.+-]){re.escape(old_value)}(?![A-Za-z0-9_.+-])")
        replaced = number_pattern.sub(new_value, text)
        if replaced == text:
            return
        self.view.set_geometry_text(replaced)
        self.commit_text_if_needed(record_history=True)
        self.app.file_controller.load_path(self.session.current_index, show_toast=False, refit=False)
        self.view.set_status(f"已将所有 {old_value} 批量修改为 {new_value}")

    def handles_to_tokens(self):
        if self.session.current_shape is None:
            return
        self.session.current_shape.segments = self.session.current_segments
        shape_text = shape_to_text(self.session.current_shape.shape_type, self.session.current_segments)
        self.session.sync_shape_from_segments(shape_text)
        self.set_geometry_text(shape_text)
