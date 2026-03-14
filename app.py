import tkinter as tk
from tkinter import ttk

from svg_path_editor import SVGPathEditor


def main():
    root = tk.Tk()
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    SVGPathEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
