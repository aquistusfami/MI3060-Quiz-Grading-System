"""Xây dựng tab quản lý kho đáp án."""

import tkinter as tk

import customtkinter as ctk

from ui.widgets import make_treeview, section_frame


def build_answer_key_tab(app):
    """Gắn các widget quản lý đáp án vào trạng thái ``app``.

    Hàm đọc tab cha và callback từ ``app``; không trả về giá trị. Các biến nhập
    và bảng đáp án được lưu trên ``app`` để lớp cửa sổ cập nhật về sau.
    """
    # Khu điều khiển chứa dữ liệu đầu vào và các thao tác với kho đáp án.
    main_frame = ctk.CTkFrame(app.tab_answer_key, fg_color="transparent")
    main_frame.pack(expand=True, fill="both", padx=5, pady=5)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)

    controls_outer = section_frame(main_frame, "QUẢN LÝ ĐÁP ÁN")
    controls_outer.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 10))
    controls = ctk.CTkFrame(controls_outer)
    controls.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
    controls.grid_columnconfigure(7, weight=1)

    ctk.CTkLabel(controls, text="Mã đề").grid(row=0, column=0, padx=(8, 4), pady=5, sticky="w")
    app.var_key_exam_id = tk.StringVar()
    ctk.CTkEntry(controls, textvariable=app.var_key_exam_id, width=140).grid(
        row=0, column=1, padx=4, pady=5, sticky="w"
    )

    ctk.CTkLabel(controls, text="Câu").grid(row=0, column=2, padx=(12, 4), pady=5, sticky="w")
    app.var_key_question_id = tk.StringVar()
    ctk.CTkEntry(controls, textvariable=app.var_key_question_id, width=90).grid(
        row=0, column=3, padx=4, pady=5, sticky="w"
    )

    ctk.CTkLabel(controls, text="Đáp án").grid(row=0, column=4, padx=(12, 4), pady=5, sticky="w")
    app.var_key_answer = tk.StringVar()
    ctk.CTkEntry(controls, textvariable=app.var_key_answer, width=100).grid(
        row=0, column=5, padx=4, pady=5, sticky="w"
    )

    ctk.CTkButton(
        controls,
        text="Thêm/Sửa",
        width=96,
        command=app._save_answer_key_question,
    ).grid(row=0, column=6, padx=5, pady=5)

    ctk.CTkButton(
        controls,
        text="Xóa câu",
        width=86,
        command=app._delete_answer_key_question,
    ).grid(row=1, column=1, padx=4, pady=5, sticky="w")

    ctk.CTkButton(
        controls,
        text="Xóa đề",
        width=86,
        command=app._delete_answer_key_exam,
    ).grid(row=1, column=2, padx=4, pady=5, sticky="w")

    ctk.CTkButton(
        controls,
        text="Nạp CSV",
        width=86,
        command=app._load_answer_key_for_management,
    ).grid(row=1, column=3, padx=4, pady=5, sticky="w")

    ctk.CTkButton(
        controls,
        text="Lưu CSV",
        width=86,
        command=app._save_answer_key_csv,
    ).grid(row=1, column=4, padx=4, pady=5, sticky="w")

    # Bảng bên dưới hiển thị toàn bộ đáp án và phát sự kiện chọn dòng.
    table_outer = section_frame(main_frame, "DANH SÁCH ĐÁP ÁN")
    table_outer.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
    table_outer.grid_columnconfigure(0, weight=1)
    table_outer.grid_rowconfigure(1, weight=1)

    cols = ("Mã đề", "Câu hỏi", "Đáp án đúng")
    app.tree_answer_key = make_treeview(table_outer, cols, row=1, pady=(0, 8))
    app.tree_answer_key.bind("<<TreeviewSelect>>", app._select_answer_key_row)
