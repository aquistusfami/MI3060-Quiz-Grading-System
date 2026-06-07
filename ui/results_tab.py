import tkinter as tk

import customtkinter as ctk

from app_logic import SORT_CSV_ORDER, SORT_OPTIONS
from ui.widgets import make_treeview, section_frame


def build_results_tab(app):
    main_frame = ctk.CTkFrame(app.tab_results, fg_color="transparent")
    main_frame.pack(expand=True, fill="both", padx=5, pady=5)
    main_frame.grid_columnconfigure(0, weight=3)
    main_frame.grid_columnconfigure(1, weight=2)
    main_frame.grid_rowconfigure(1, weight=1)

    controls_outer = section_frame(main_frame, "BỘ LỌC & TRA CỨU KẾT QUẢ")
    controls_outer.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 10))
    controls = ctk.CTkFrame(controls_outer)
    controls.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
    controls.grid_columnconfigure(11, weight=1)

    ctk.CTkLabel(controls, text="Điểm từ").grid(row=0, column=0, padx=(8, 4), pady=5, sticky="w")
    app.var_score_low = tk.StringVar(value="0")
    ctk.CTkEntry(controls, textvariable=app.var_score_low, width=70).grid(row=0, column=1, padx=4, pady=5)

    ctk.CTkLabel(controls, text="đến").grid(row=0, column=2, padx=4, pady=5)
    app.var_score_high = tk.StringVar(value="10")
    ctk.CTkEntry(controls, textvariable=app.var_score_high, width=70).grid(row=0, column=3, padx=4, pady=5)

    ctk.CTkButton(
        controls,
        text="Lọc điểm",
        width=88,
        command=app._filter_score_range,
    ).grid(row=0, column=4, padx=5, pady=5)

    ctk.CTkButton(
        controls,
        text="Tất cả",
        width=76,
        command=app._show_all_results,
    ).grid(row=0, column=5, padx=5, pady=5)

    ctk.CTkLabel(controls, text="ID lớp HP").grid(row=1, column=0, padx=(8, 4), pady=5, sticky="w")
    app.var_class_filter = tk.StringVar(value="Tất cả")
    app.class_filter = ctk.CTkComboBox(
        controls,
        variable=app.var_class_filter,
        values=["Tất cả"],
        width=170,
        command=lambda _: app._filter_exam_or_class(),
    )
    app.class_filter.grid(row=1, column=1, columnspan=3, padx=4, pady=5, sticky="w")

    ctk.CTkLabel(controls, text="Kỳ thi").grid(row=1, column=4, padx=(15, 4), pady=5, sticky="w")
    app.var_exam_filter = tk.StringVar(value="Tất cả")
    app.exam_filter = ctk.CTkComboBox(
        controls,
        variable=app.var_exam_filter,
        values=["Tất cả"],
        width=170,
        command=lambda _: app._filter_exam_or_class(),
    )
    app.exam_filter.grid(row=1, column=5, columnspan=3, padx=4, pady=5, sticky="w")

    ctk.CTkLabel(controls, text="Sắp xếp").grid(row=1, column=8, padx=(15, 4), pady=5, sticky="w")
    app.var_result_sort = tk.StringVar(value=SORT_CSV_ORDER)
    app.result_sort = ctk.CTkComboBox(
        controls,
        variable=app.var_result_sort,
        values=list(SORT_OPTIONS),
        width=190,
        command=lambda _: app._refresh_results_tab(),
    )
    app.result_sort.grid(row=1, column=9, columnspan=2, padx=4, pady=5, sticky="w")

    cols = ("STT", "Kỳ thi", "MSSV", "Họ tên", "ID lớp HP", "Mã lớp SV", "Tên lớp SV", "Điểm", "Số câu đúng", "Tổng câu", "Tỷ lệ %")
    table_outer = section_frame(main_frame, "BẢNG KẾT QUẢ & XẾP HẠNG")
    table_outer.grid(row=1, column=0, sticky="nsew", padx=(5, 5), pady=(0, 5))
    table_outer.grid_columnconfigure(0, weight=1)
    table_outer.grid_rowconfigure(1, weight=1)
    app.tree_results = make_treeview(table_outer, cols, row=1, pady=(0, 8))
    app.tree_results.bind("<<TreeviewSelect>>", app._show_student_answers)

    answer_outer = section_frame(main_frame, "CHI TIẾT BÀI LÀM SINH VIÊN")
    answer_outer.grid(row=1, column=1, sticky="nsew", padx=(5, 5), pady=(0, 5))
    answer_outer.grid_columnconfigure(0, weight=1)
    answer_outer.grid_rowconfigure(1, weight=1)
    answer_cols = ("Câu", "Đáp án SV", "Đáp án đúng", "Kết quả")
    app.tree_student_answers = make_treeview(answer_outer, answer_cols, row=1, pady=(0, 8))
