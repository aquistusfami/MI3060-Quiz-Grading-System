import tkinter as tk

import customtkinter as ctk

from ui.widgets import make_treeview, section_frame


def build_question_tab(app):
    main_frame = ctk.CTkFrame(app.tab_question, fg_color="transparent")
    main_frame.pack(expand=True, fill="both", padx=5, pady=5)
    main_frame.grid_columnconfigure(0, weight=3)
    main_frame.grid_columnconfigure(1, weight=2)
    main_frame.grid_rowconfigure(0, weight=1)

    question_outer = section_frame(main_frame, "THỐNG KÊ THEO CÂU HỎI")
    question_outer.grid(row=0, column=0, sticky="nsew", padx=(5, 5), pady=5)
    question_outer.grid_columnconfigure(0, weight=1)
    question_outer.grid_rowconfigure(2, weight=1)

    question_controls = ctk.CTkFrame(question_outer)
    question_controls.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
    ctk.CTkLabel(question_controls, text="Chọn đề").pack(side=tk.LEFT)
    app.var_question_exam_filter = tk.StringVar(value="Chưa có dữ liệu")
    app.question_exam_filter = ctk.CTkComboBox(
        question_controls,
        variable=app.var_question_exam_filter,
        values=["Chưa có dữ liệu"],
        width=150,
        command=lambda _: app._refresh_question_tab(),
    )
    app.question_exam_filter.pack(side=tk.LEFT, padx=(6, 0))

    cols = ("Kỳ thi", "Câu hỏi", "Số người đúng", "Số người sai", "Tỷ lệ đúng %")
    app.tree_question = make_treeview(question_outer, cols, row=2, pady=(0, 6))

    side_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    side_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 5), pady=5)
    side_frame.grid_columnconfigure(0, weight=1)
    side_frame.grid_rowconfigure(0, weight=1)

    hardest_outer = section_frame(side_frame, "TOP CÂU HỎI KHÓ")
    hardest_outer.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    hardest_outer.grid_columnconfigure(0, weight=1)
    hardest_outer.grid_rowconfigure(1, weight=1)
    app.hardest_text = ctk.CTkTextbox(
        hardest_outer,
        font=("Courier", 12),
        state=tk.DISABLED,
        border_width=1,
    )
    app.hardest_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
