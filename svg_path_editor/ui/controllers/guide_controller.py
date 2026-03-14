from tkinter import messagebox

from ...application import AddGuideCommand, ClearGuidesCommand, DeleteGuideCommand, MoveGuideCommand
from ..helpers import canvas_to_point, point_to_canvas
from .base import BaseController


class GuideController(BaseController):
    def refresh_guide_listbox(self):
        self.view.refresh_guide_list(self.state.custom_guides, self.state.selected_guide_index)

    def sync_view_after_guide_change(self):
        self.refresh_guide_listbox()
        self.app.redraw()

    def on_guide_selected(self, _event=None):
        self.state.selected_guide_index = self.view.get_selected_guide_index()
        self.app.redraw()

    def add_guide_from_input(self):
        try:
            value = float(self.view.guide_value_var.get().strip())
        except ValueError:
            messagebox.showerror("辅助线无效", "辅助线位置必须是数字。")
            return
        axis = self.view.guide_axis_var.get()
        self.session.history.execute(AddGuideCommand(self.state, axis, value))
        self.sync_view_after_guide_change()
        self.view.set_status(f"已添加 {axis} 方向辅助线，位置 {value:g}")

    def add_focus_guides(self, axis: str):
        if self.state.focus_handle is None:
            messagebox.showinfo("没有焦点点", "请先选中或拖动一个点。")
            return
        value = self.state.focus_handle.point[0] if axis == "x" else self.state.focus_handle.point[1]
        self.session.history.execute(AddGuideCommand(self.state, axis, value))
        self.sync_view_after_guide_change()
        self.view.set_status(f"已从焦点点添加 {axis} 方向辅助线，位置 {value:g}")

    def delete_selected_guide(self):
        if self.state.selected_guide_index is None:
            messagebox.showinfo("未选中辅助线", "请先在辅助线列表中选择一条辅助线。")
            return
        axis, value = self.state.custom_guides[self.state.selected_guide_index]
        self.session.history.execute(DeleteGuideCommand(self.state, self.state.selected_guide_index))
        self.sync_view_after_guide_change()
        self.view.set_status(f"已删除辅助线 {axis} = {value:g}")

    def clear_guides(self):
        if not self.state.custom_guides:
            return
        self.session.history.execute(ClearGuidesCommand(self.state))
        self.sync_view_after_guide_change()
        self.view.set_status("已清空自定义辅助线。")

    def finalize_guide_move(self):
        if self.state.active_guide_index is None or self.state.drag_guide_before_value is None:
            return False
        axis, after_value = self.state.custom_guides[self.state.active_guide_index]
        before_value = self.state.drag_guide_before_value
        self.state.drag_guide_before_value = None
        if abs(before_value - after_value) < 1e-9:
            return False
        self.session.history.push_executed(MoveGuideCommand(self.state, self.state.active_guide_index, before_value, after_value))
        self.view.set_status(f"已按 {self.app.canvas_controller.get_drag_step():g} 步长移动辅助线 {axis} = {after_value:g}")
        return True

    def find_selected_guide_hit(self, canvas_x: float, canvas_y: float):
        if self.state.selected_guide_index is None or self.session.document.view_box is None or self.state.selected_guide_index >= len(self.state.custom_guides):
            return None
        axis, value = self.state.custom_guides[self.state.selected_guide_index]
        if axis == "x":
            guide_x, _ = point_to_canvas((value, 0), self.state.scale, self.state.offset_x, self.state.offset_y)
            return self.state.selected_guide_index if abs(canvas_x - guide_x) <= 8 else None
        _x, guide_y = point_to_canvas((0, value), self.state.scale, self.state.offset_x, self.state.offset_y)
        return self.state.selected_guide_index if abs(canvas_y - guide_y) <= 8 else None

    def drag_active_guide(self, event):
        if self.state.active_guide_index is None:
            return False
        axis, _old_value = self.state.custom_guides[self.state.active_guide_index]
        new_point = canvas_to_point(event.x, event.y, self.state.scale, self.state.offset_x, self.state.offset_y)
        raw_value = new_point[0] if axis == "x" else new_point[1]
        new_value = self.app.canvas_controller.snap_value(raw_value)
        self.state.custom_guides[self.state.active_guide_index] = (axis, new_value)
        self.state.selected_guide_index = self.state.active_guide_index
        self.refresh_guide_listbox()
        self.view.set_status(f"正在按 {self.app.canvas_controller.get_drag_step():g} 步长拖动辅助线：{axis} = {new_value:g}")
        self.app.redraw()
        return True
