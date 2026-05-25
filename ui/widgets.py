import tkinter as tk
from tkinter import ttk

import customtkinter as ctk


def section_frame(parent, title: str):
    frame = ctk.CTkFrame(parent)
    frame.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        frame,
        text=title,
        font=ctk.CTkFont(size=14, weight="bold"),
    ).grid(row=0, column=0, padx=10, pady=(8, 6))
    return frame


def make_treeview(parent, columns, row: int = 0, pady=8) -> ttk.Treeview:
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(row, weight=1)

    frame = ctk.CTkFrame(parent, corner_radius=6)
    frame.grid(row=row, column=0, sticky="nsew", padx=8, pady=pady)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)

    tree = ttk.Treeview(frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=110, anchor=tk.CENTER)

    vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    return tree
