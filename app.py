import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from svg_path_editor import SVGPathEditor
from svg_path_editor.ui import CrashHandler, run_guarded_process
from svg_path_editor.ui.crash_handler import CHILD_ENV_KEY


def run_application():
    root = tk.Tk()
    crash_handler = CrashHandler(root)
    crash_handler.install()

    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")

        SVGPathEditor(root, crash_handler=crash_handler)
        root.mainloop()
    except Exception as exc:
        crash_handler.show_exception(exc, source="应用启动或主循环")


def main():
    if os.environ.get(CHILD_ENV_KEY) != "1":
        run_guarded_process(Path(__file__).resolve())
        return
    run_application()


if __name__ == "__main__":
    main()
