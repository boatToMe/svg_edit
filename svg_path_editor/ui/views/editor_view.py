import tkinter as tk
from tkinter import ttk


class EditorView:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SVG 可视化编辑器")

        self.path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="请先打开一个 SVG 文件。")
        self.guide_axis_var = tk.StringVar(value="x")
        self.guide_value_var = tk.StringVar()
        self.drag_step_var = tk.StringVar(value="1")

        self._build_ui()

    def _build_ui(self):
        self.root.geometry("1360x880")
        self.root.minsize(1080, 760)
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        self.open_button = ttk.Button(top, text="打开 SVG")
        self.open_button.pack(side="left")
        self.save_button = ttk.Button(top, text="保存")
        self.save_button.pack(side="left", padx=(8, 0))
        self.save_as_button = ttk.Button(top, text="另存为")
        self.save_as_button.pack(side="left", padx=(8, 0))
        self.preview_button = ttk.Button(top, text="预览")
        self.preview_button.pack(side="left", padx=(8, 0))
        ttk.Label(top, text="元素：").pack(side="left", padx=(18, 6))
        self.path_combo = ttk.Combobox(top, textvariable=self.path_var, state="readonly", width=42, values=[])
        self.path_combo.pack(side="left", fill="x", expand=True)

        self.main = ttk.PanedWindow(self.root, orient="horizontal")
        self.main.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        left = ttk.Frame(self.main, padding=(0, 0, 8, 0))
        right = ttk.Frame(self.main)
        self.main.add(left, weight=4)
        self.main.add(right, weight=2)

        self.canvas = tk.Canvas(left, background="#f8fafc", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        inspector = ttk.LabelFrame(right, text="几何数据", padding=8)
        inspector.pack(fill="x")
        self.text = tk.Text(inspector, wrap="word", font=("Consolas", 11), height=7)
        self.text.pack(fill="x", expand=False)
        self.text.tag_configure("number_default", foreground="#0f172a")
        self.text.tag_configure("number_focus", foreground="#2563eb")
        self.text.tag_configure("number_selected", foreground="#dc2626")
        text_buttons = ttk.Frame(inspector)
        text_buttons.pack(fill="x", pady=(8, 0))
        self.apply_text_button = ttk.Button(text_buttons, text="应用文本")
        self.apply_text_button.pack(side="left")
        self.reload_button = ttk.Button(text_buttons, text="重新载入")
        self.reload_button.pack(side="left", padx=(8, 0))
        self.batch_replace_button = ttk.Button(text_buttons, text="批量修改同值")
        self.batch_replace_button.pack(side="left", padx=(8, 0))

        editor_box = ttk.LabelFrame(right, text="编辑设置", padding=8)
        editor_box.pack(fill="x", pady=(8, 0))
        step_row = ttk.Frame(editor_box)
        step_row.pack(fill="x")
        ttk.Label(step_row, text="拖动步长").pack(side="left")
        self.drag_step_entry = ttk.Entry(step_row, textvariable=self.drag_step_var, width=10)
        self.drag_step_entry.pack(side="left", padx=(8, 6))
        ttk.Label(step_row, text="px").pack(side="left")
        ttk.Label(editor_box, text="端点和辅助线拖动都会按这个步长吸附。", justify="left").pack(anchor="w", pady=(8, 0))

        guide_box = ttk.LabelFrame(right, text="辅助线", padding=8)
        guide_box.pack(fill="x", pady=(8, 0))
        guide_input = ttk.Frame(guide_box)
        guide_input.pack(fill="x")
        ttk.Label(guide_input, text="方向").pack(side="left")
        self.guide_axis_combo = ttk.Combobox(guide_input, textvariable=self.guide_axis_var, values=["x", "y"], width=4, state="readonly")
        self.guide_axis_combo.pack(side="left", padx=(6, 8))
        ttk.Label(guide_input, text="位置").pack(side="left")
        self.guide_value_entry = ttk.Entry(guide_input, textvariable=self.guide_value_var, width=10)
        self.guide_value_entry.pack(side="left", padx=(6, 8))
        self.add_guide_button = ttk.Button(guide_input, text="添加辅助线")
        self.add_guide_button.pack(side="left")
        guide_actions = ttk.Frame(guide_box)
        guide_actions.pack(fill="x", pady=(8, 0))
        self.add_focus_x_button = ttk.Button(guide_actions, text="添加焦点 X")
        self.add_focus_x_button.pack(side="left")
        self.add_focus_y_button = ttk.Button(guide_actions, text="添加焦点 Y")
        self.add_focus_y_button.pack(side="left", padx=(8, 0))
        self.delete_guide_button = ttk.Button(guide_actions, text="删除选中辅助线")
        self.delete_guide_button.pack(side="left", padx=(8, 0))
        self.clear_guides_button = ttk.Button(guide_actions, text="清空辅助线")
        self.clear_guides_button.pack(side="left", padx=(8, 0))
        list_frame = ttk.Frame(guide_box)
        list_frame.pack(fill="x", pady=(8, 0))
        self.guide_listbox = tk.Listbox(list_frame, height=6, exportselection=False)
        self.guide_listbox.pack(side="left", fill="x", expand=True)
        guide_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.guide_listbox.yview)
        guide_scrollbar.pack(side="right", fill="y")
        self.guide_listbox.configure(yscrollcommand=guide_scrollbar.set)

        help_box = ttk.LabelFrame(right, text="提示", padding=8)
        help_box.pack(fill="x", pady=(8, 0))
        ttk.Label(help_box, text=(
            "画布会同时显示全部可编辑元素\n"
            "当前元素高亮，节点可拖动\n"
            "拖动会按编辑设置里的步长吸附\n"
            "按住空格并左键拖动可移动画布\n"
            "节点拖动后可用 Ctrl+Z 撤销、Ctrl+Y 重做\n"
            "选中几何数据区数字时会高亮对应端点\n"
            "可对选中的同值数字做批量替换\n"
            "点击预览可按像素宽度查看渲染结果"
        ), justify="left").pack(anchor="w")
        ttk.Label(self.root, textvariable=self.status_var, anchor="w", padding=(10, 6)).pack(fill="x")

    def set_element_labels(self, labels: list[str]):
        self.path_combo["values"] = labels

    def set_geometry_text(self, text: str):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)

    def get_geometry_text(self) -> str:
        return self.text.get("1.0", "end").strip()

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
