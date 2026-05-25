import tkinter as tk

import customtkinter as ctk

from ui.widgets import section_frame


def build_search_tab(app):
    main_frame = ctk.CTkFrame(app.tab_search, fg_color="transparent")
    main_frame.pack(expand=True, fill="both", padx=5, pady=5)

    search_outer = section_frame(main_frame, "TÌM KIẾM SINH VIÊN")
    search_outer.pack(fill="x", padx=5, pady=(5, 10))
    frame_top = ctk.CTkFrame(search_outer)
    frame_top.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
    frame_top.grid_columnconfigure(1, weight=1)
    frame_top.grid_columnconfigure(3, weight=1)

    ctk.CTkLabel(frame_top, text="MSSV").grid(row=0, column=0, padx=(8, 4), pady=5, sticky="w")
    app.var_search = tk.StringVar()
    app.entry_search = ctk.CTkEntry(frame_top, textvariable=app.var_search)
    app.entry_search.grid(row=0, column=1, padx=4, pady=5, sticky="ew")
    app.entry_search.bind("<Return>", lambda e: app._do_search())
    app.entry_search.bind("<KeyRelease>", app._update_search_suggestions)
    app.entry_search.bind("<FocusOut>", lambda _event: app.after(150, app._hide_search_suggestions))

    ctk.CTkLabel(frame_top, text="Họ tên").grid(row=0, column=2, padx=(12, 4), pady=5, sticky="w")
    app.var_search_name = tk.StringVar()
    app.entry_search_name = ctk.CTkEntry(frame_top, textvariable=app.var_search_name)
    app.entry_search_name.grid(row=0, column=3, padx=4, pady=5, sticky="ew")
    app.entry_search_name.bind("<Return>", lambda e: app._do_search())
    app.entry_search_name.bind("<KeyRelease>", app._update_search_name_suggestions)
    app.entry_search_name.bind("<FocusOut>", lambda _event: app.after(150, app._hide_search_suggestions))

    ctk.CTkButton(
        frame_top,
        text="Tìm kiếm",
        width=96,
        command=app._do_search,
    ).grid(row=0, column=4, padx=8, pady=5)

    app.search_suggestion_box = tk.Listbox(
        search_outer,
        height=5,
        activestyle="dotbox",
        exportselection=False,
    )
    app.search_suggestion_box.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
    app.search_suggestion_box.bind("<<ListboxSelect>>", app._select_search_suggestion)
    app.search_suggestion_box.bind("<Return>", app._select_search_suggestion)
    app.search_suggestion_box.grid_remove()
    app.search_suggestion_target = "mssv"

    app.search_result_text = ctk.CTkTextbox(
        main_frame,
        font=("Courier", 12),
        state=tk.DISABLED,
        border_width=1,
    )
    app.search_result_text.pack(expand=True, fill="both", padx=5, pady=(0, 5))
