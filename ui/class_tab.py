"""Xây dựng tab danh sách lớp học phần và sinh viên."""

import customtkinter as ctk

from ui.widgets import make_treeview, section_frame


def build_class_tab(app):
    """Gắn hai bảng lớp học phần và sinh viên vào ``app``.

    Hàm nhận cửa sổ đã có ``tab_class``, không trả về giá trị và lưu các
    Treeview trên ``app`` để lớp điều phối nạp dữ liệu.
    """
    # Bảng trên tổng hợp từng lớp học phần.
    main_frame = ctk.CTkFrame(app.tab_class, fg_color="transparent")
    main_frame.pack(expand=True, fill="both", padx=5, pady=5)

    class_outer = section_frame(main_frame, "DANH SÁCH LỚP HỌC PHẦN")
    class_outer.pack(expand=True, fill="both", padx=5, pady=(5, 10))
    class_outer.grid_columnconfigure(0, weight=1)
    class_outer.grid_rowconfigure(1, weight=1)

    class_cols = ("Kỳ thi", "Mã HP", "Tên học phần", "ID lớp HP", "Tên lớp SV", "Số SV", "Điểm TB", "Tỷ lệ đạt")
    app.tree_class = make_treeview(class_outer, class_cols, row=1, pady=(0, 8))
    app.tree_class.bind("<<TreeviewSelect>>", app._show_class_detail)

    # Bảng dưới hiển thị sinh viên thuộc lớp đang được chọn.
    student_outer = section_frame(main_frame, "SINH VIÊN TRONG LỚP")
    student_outer.pack(expand=True, fill="both", padx=5, pady=(0, 5))
    student_outer.grid_columnconfigure(0, weight=1)
    student_outer.grid_rowconfigure(1, weight=1)

    student_cols = ("Hạng", "MSSV", "Họ tên", "Mã lớp SV", "Tên lớp SV", "Điểm", "Đúng/Tổng", "Tỷ lệ")
    app.tree_class_students = make_treeview(student_outer, student_cols, row=1, pady=(0, 8))
