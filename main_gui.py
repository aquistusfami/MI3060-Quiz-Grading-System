# main_gui.py
# Giao diện người dùng với CustomTkinter.

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

import customtkinter as ctk

from app_logic import (
    load_answer_key,
    load_exam_store,
    load_students,
    infer_exam_store,
    grade_all,
    compute_question_stats,
    export_results_csv,
    export_question_stats_csv,
    search_students,
    search_students_by_name,
    build_student_search_index,
    search_students_indexed,
    get_student_id_suggestions,
    SORT_OPTIONS,
    SORT_CSV_ORDER,
    SORT_SCORE_DESC,
    build_result_rows_in_student_order,
    sort_results,
    build_score_index,
    get_students_in_score_range,
    get_hardest_questions,
    get_question_stats_items,
    get_answer_key_items,
    get_student_answer_items,
    get_top_k_results,
    get_exam_ids,
    get_results_by_exam,
    get_class_names,
    get_results_by_class,
    build_class_summary,
    build_class_roster_summary,
    build_exam_summary,
    build_exam_statistics,
)
from models import normalize_question_id

# Đường dẫn mặc định.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ANSWER_KEY = os.path.join(BASE_DIR, "data", "answer_key.csv")
DEFAULT_STUDENTS = os.path.join(BASE_DIR, "data", "students.csv")
DEFAULT_EXAMS = os.path.join(BASE_DIR, "data", "exams.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


# --- Ứng dụng chính ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hệ thống Chấm Điểm Trắc Nghiệm")
        self.geometry("1280x850")
        self.minsize(980, 680)
        self.resizable(True, True)

        # Trạng thái dữ liệu.
        self.answer_key = None
        self.exam_store = None
        self.students = None
        self.results = None
        self.question_stats = None
        self.exam_summary = []
        self.class_summary = []
        self.result_rows = []
        self.display_rows = []
        self.score_index = []
        self.student_id_trie = None
        self.student_search_index = None
        self.exam_ids = []
        self.class_names = []

        self._build_ui()
        self._load_initial_class_roster()

    # --- Xây dựng giao diện ---

    def _build_ui(self):
        self._configure_ttk_style()

        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="HỆ THỐNG CHẤM ĐIỂM TRẮC NGHIỆM",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(10, 6))

        toolbar = ctk.CTkFrame(header)
        toolbar.pack(fill="x", padx=10, pady=(0, 10))
        toolbar.grid_columnconfigure(1, weight=1)
        toolbar.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(toolbar, text="File đáp án:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.var_answer_path = tk.StringVar(value=DEFAULT_ANSWER_KEY)
        ctk.CTkEntry(toolbar, textvariable=self.var_answer_path).grid(
            row=0, column=1, sticky="ew", padx=5, pady=5
        )
        ctk.CTkButton(
            toolbar,
            text="Chọn",
            width=70,
            command=self._browse_answer,
        ).grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkLabel(toolbar, text="File thí sinh:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.var_student_path = tk.StringVar(value=DEFAULT_STUDENTS)
        ctk.CTkEntry(toolbar, textvariable=self.var_student_path).grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )
        ctk.CTkButton(
            toolbar,
            text="Chọn",
            width=70,
            command=self._browse_students,
        ).grid(row=1, column=2, padx=5, pady=5)

        ctk.CTkButton(
            toolbar,
            text="Chấm điểm",
            width=120,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._run_grading,
        ).grid(row=0, column=3, padx=(15, 5), pady=5, sticky="ew")

        ctk.CTkButton(
            toolbar,
            text="Xuất CSV",
            width=92,
            command=self._export,
        ).grid(row=1, column=3, padx=(15, 5), pady=5, sticky="ew")

        # Khu vực tab chính.
        self.tabview = ctk.CTkTabview(self, width=1330, height=760)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=5)

        self.tab_results = self.tabview.add("Kết quả & Xếp hạng")
        self.tab_stats = self.tabview.add("Thống kê tổng hợp")
        self.tab_exam = self.tabview.add("Thông tin kỳ thi")
        self.tab_class = self.tabview.add("Danh sách lớp HP")
        self.tab_question = self.tabview.add("Thống kê câu hỏi")
        self.tab_search = self.tabview.add("Tìm kiếm thí sinh")

        self._build_tab_results()
        self._build_tab_exam()
        self._build_tab_class()
        self._build_tab_stats()
        self._build_tab_question()
        self._build_tab_search()

        # Thanh trạng thái.
        self.status_var = tk.StringVar(value="Sẵn sàng. Chọn file và nhấn CHẤM ĐIỂM.")
        status = ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            anchor="w",
            height=30,
        )
        status.pack(fill="x", padx=10, pady=(0, 6))

    def _section_frame(self, parent, title: str):
        frame = ctk.CTkFrame(parent)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(8, 6))
        return frame

    def _configure_ttk_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            borderwidth=0,
            rowheight=27,
            font=("Arial", 10),
        )
        style.configure(
            "Treeview.Heading",
            relief="flat",
            font=("Arial", 10, "bold"),
            padding=(6, 6),
        )

    # --- TAB KẾT QUẢ VÀ XẾP HẠNG ---

    def _build_tab_results(self):
        main_frame = ctk.CTkFrame(self.tab_results, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(1, weight=1)

        controls_outer = self._section_frame(main_frame, "BỘ LỌC & TRA CỨU KẾT QUẢ")
        controls_outer.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 10))
        controls = ctk.CTkFrame(controls_outer)
        controls.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        controls.grid_columnconfigure(11, weight=1)

        ctk.CTkLabel(controls, text="Điểm từ").grid(row=0, column=0, padx=(8, 4), pady=5, sticky="w")
        self.var_score_low = tk.StringVar(value="0")
        ctk.CTkEntry(controls, textvariable=self.var_score_low, width=70).grid(row=0, column=1, padx=4, pady=5)

        ctk.CTkLabel(controls, text="đến").grid(row=0, column=2, padx=4, pady=5)
        self.var_score_high = tk.StringVar(value="10")
        ctk.CTkEntry(controls, textvariable=self.var_score_high, width=70).grid(row=0, column=3, padx=4, pady=5)

        ctk.CTkButton(
            controls,
            text="Lọc điểm",
            width=88,
            command=self._filter_score_range,
        ).grid(row=0, column=4, padx=5, pady=5)

        ctk.CTkButton(
            controls,
            text="Tất cả",
            width=76,
            command=self._show_all_results,
        ).grid(row=0, column=5, padx=5, pady=5)

        ctk.CTkLabel(controls, text="Top").grid(row=0, column=6, padx=(15, 4), pady=5)
        self.var_top_k = tk.StringVar(value="100")
        ctk.CTkEntry(controls, textvariable=self.var_top_k, width=72).grid(row=0, column=7, padx=4, pady=5)
        ctk.CTkButton(
            controls,
            text="Xem top",
            width=88,
            command=self._show_top_k,
        ).grid(row=0, column=8, padx=5, pady=5)

        ctk.CTkLabel(controls, text="ID lớp HP").grid(row=1, column=0, padx=(8, 4), pady=5, sticky="w")
        self.var_class_filter = tk.StringVar(value="Tất cả")
        self.class_filter = ctk.CTkComboBox(
            controls,
            variable=self.var_class_filter,
            values=["Tất cả"],
            width=170,
            command=lambda _: self._filter_class(),
        )
        self.class_filter.grid(row=1, column=1, columnspan=3, padx=4, pady=5, sticky="w")

        ctk.CTkLabel(controls, text="Kỳ thi").grid(row=1, column=4, padx=(15, 4), pady=5, sticky="w")
        self.var_exam_filter = tk.StringVar(value="Tất cả")
        self.exam_filter = ctk.CTkComboBox(
            controls,
            variable=self.var_exam_filter,
            values=["Tất cả"],
            width=170,
            command=lambda _: self._filter_exam_or_class(),
        )
        self.exam_filter.grid(row=1, column=5, columnspan=3, padx=4, pady=5, sticky="w")

        ctk.CTkLabel(controls, text="Sắp xếp").grid(row=1, column=8, padx=(15, 4), pady=5, sticky="w")
        self.var_result_sort = tk.StringVar(value=SORT_CSV_ORDER)
        self.result_sort = ctk.CTkComboBox(
            controls,
            variable=self.var_result_sort,
            values=list(SORT_OPTIONS),
            width=190,
            command=lambda _: self._refresh_results_tab(),
        )
        self.result_sort.grid(row=1, column=9, columnspan=2, padx=4, pady=5, sticky="w")

        cols = ("STT", "Kỳ thi", "MSSV", "Họ tên", "ID lớp HP", "Mã lớp SV", "Tên lớp SV", "Điểm", "Số câu đúng", "Tổng câu", "Tỷ lệ %")
        table_outer = self._section_frame(main_frame, "BẢNG KẾT QUẢ & XẾP HẠNG")
        table_outer.grid(row=1, column=0, sticky="nsew", padx=(5, 5), pady=(0, 5))
        table_outer.grid_columnconfigure(0, weight=1)
        table_outer.grid_rowconfigure(1, weight=1)
        self.tree_results = self._make_treeview(table_outer, cols, row=1, pady=(0, 8))
        self.tree_results.bind("<<TreeviewSelect>>", self._show_student_answers)

        answer_outer = self._section_frame(main_frame, "CHI TIẾT BÀI LÀM SINH VIÊN")
        answer_outer.grid(row=1, column=1, sticky="nsew", padx=(5, 5), pady=(0, 5))
        answer_outer.grid_columnconfigure(0, weight=1)
        answer_outer.grid_rowconfigure(1, weight=1)
        answer_cols = ("Câu", "Đáp án SV", "Đáp án đúng", "Kết quả")
        self.tree_student_answers = self._make_treeview(answer_outer, answer_cols, row=1, pady=(0, 8))

    # --- TAB THỐNG KÊ TỔNG HỢP ---

    def _build_tab_stats(self):
        main_frame = ctk.CTkFrame(self.tab_stats, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=5, pady=5)
        stats_outer = self._section_frame(main_frame, "THỐNG KÊ TỔNG HỢP")
        stats_outer.pack(expand=True, fill="both", padx=5, pady=5)
        stats_outer.grid_columnconfigure(0, weight=1)
        stats_outer.grid_rowconfigure(1, weight=1)
        self.stats_text = ctk.CTkTextbox(
            stats_outer,
            font=("Courier", 12),
            state=tk.DISABLED,
            border_width=1,
        )
        self.stats_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    # --- TAB THÔNG TIN KỲ THI ---

    def _build_tab_exam(self):
        main_frame = ctk.CTkFrame(self.tab_exam, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=5, pady=5)

        list_outer = self._section_frame(main_frame, "DANH SÁCH KỲ THI / ĐỀ THI")
        list_outer.pack(expand=True, fill="both", padx=5, pady=(5, 10))
        list_outer.grid_columnconfigure(0, weight=1)
        list_outer.grid_rowconfigure(1, weight=1)

        cols = ("Kỳ thi", "Học phần", "Học kỳ", "Số câu", "Số SV", "Số lớp HP")
        self.tree_exam = self._make_treeview(list_outer, cols, row=1, pady=(0, 8))
        self.tree_exam.bind("<<TreeviewSelect>>", self._show_exam_detail)

        detail_frame = self._section_frame(main_frame, "CHI TIẾT KỲ THI")
        detail_frame.pack(fill="x", padx=5, pady=(0, 5))
        detail_frame.grid_columnconfigure(0, weight=1)

        self.exam_detail_text = ctk.CTkTextbox(
            detail_frame,
            height=170,
            font=("Courier", 12),
            state=tk.DISABLED,
            border_width=1,
        )
        self.exam_detail_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    # --- TAB THỐNG KÊ CÂU HỎI ---

    def _build_tab_question(self):
        main_frame = ctk.CTkFrame(self.tab_question, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)

        question_outer = self._section_frame(main_frame, "THỐNG KÊ THEO CÂU HỎI")
        question_outer.grid(row=0, column=0, sticky="nsew", padx=(5, 5), pady=5)
        question_outer.grid_columnconfigure(0, weight=1)
        question_outer.grid_rowconfigure(2, weight=1)

        question_controls = ctk.CTkFrame(question_outer)
        question_controls.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        ctk.CTkLabel(question_controls, text="Chọn đề").pack(side=tk.LEFT)
        self.var_question_exam_filter = tk.StringVar(value="Chưa có dữ liệu")
        self.question_exam_filter = ctk.CTkComboBox(
            question_controls,
            variable=self.var_question_exam_filter,
            values=["Chưa có dữ liệu"],
            width=150,
            command=lambda _: self._refresh_question_tab(),
        )
        self.question_exam_filter.pack(side=tk.LEFT, padx=(6, 0))

        cols = ("Kỳ thi", "Câu hỏi", "Số người đúng", "Số người sai", "Tỷ lệ đúng %")
        self.tree_question = self._make_treeview(question_outer, cols, row=2, pady=(0, 6))

        side_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        side_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 5), pady=5)
        side_frame.grid_columnconfigure(0, weight=1)
        side_frame.grid_rowconfigure(1, weight=1)

        hardest_outer = self._section_frame(side_frame, "TOP CÂU HỎI KHÓ")
        hardest_outer.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 10))
        hardest_outer.grid_columnconfigure(0, weight=1)
        self.hardest_text = ctk.CTkTextbox(
            hardest_outer,
            height=110,
            font=("Courier", 12),
            state=tk.DISABLED,
            border_width=1,
        )
        self.hardest_text.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

        answer_key_outer = self._section_frame(side_frame, "CHỈNH SỬA ĐÁP ÁN BỘ ĐỀ")
        answer_key_outer.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        answer_key_outer.grid_columnconfigure(0, weight=1)
        answer_key_outer.grid_rowconfigure(2, weight=1)

        answer_controls = ctk.CTkFrame(answer_key_outer)
        answer_controls.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        ctk.CTkLabel(answer_controls, text="Đáp án mới").grid(row=0, column=0, padx=(8, 4), pady=5)
        self.var_new_answer = tk.StringVar()
        ctk.CTkEntry(answer_controls, textvariable=self.var_new_answer, width=90).grid(row=0, column=1, padx=4, pady=5)
        ctk.CTkButton(
            answer_controls,
            text="Cập nhật đáp án",
            width=130,
            command=self._update_selected_answer,
        ).grid(row=0, column=2, padx=5, pady=5)

        answer_cols = ("Kỳ thi", "Câu", "Đáp án đúng")
        self.tree_answer_key = self._make_treeview(answer_key_outer, answer_cols, row=2, pady=(0, 8))
        self.tree_answer_key.bind("<<TreeviewSelect>>", self._load_selected_answer)

    # --- TAB TÌM KIẾM THÍ SINH ---

    def _build_tab_search(self):
        main_frame = ctk.CTkFrame(self.tab_search, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=5, pady=5)

        search_outer = self._section_frame(main_frame, "TÌM KIẾM SINH VIÊN")
        search_outer.pack(fill="x", padx=5, pady=(5, 10))
        frame_top = ctk.CTkFrame(search_outer)
        frame_top.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        frame_top.grid_columnconfigure(1, weight=1)
        frame_top.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(frame_top, text="MSSV").grid(row=0, column=0, padx=(8, 4), pady=5, sticky="w")
        self.var_search = tk.StringVar()
        self.entry_search = ctk.CTkEntry(frame_top, textvariable=self.var_search)
        self.entry_search.grid(row=0, column=1, padx=4, pady=5, sticky="ew")
        self.entry_search.bind("<Return>", lambda e: self._do_search())
        self.entry_search.bind("<KeyRelease>", self._update_search_suggestions)
        self.entry_search.bind("<FocusOut>", lambda _event: self.after(150, self._hide_search_suggestions))

        ctk.CTkLabel(frame_top, text="Họ tên").grid(row=0, column=2, padx=(12, 4), pady=5, sticky="w")
        self.var_search_name = tk.StringVar()
        self.entry_search_name = ctk.CTkEntry(frame_top, textvariable=self.var_search_name)
        self.entry_search_name.grid(row=0, column=3, padx=4, pady=5, sticky="ew")
        self.entry_search_name.bind("<Return>", lambda e: self._do_search())

        ctk.CTkButton(
            frame_top,
            text="Tìm kiếm",
            width=96,
            command=self._do_search,
        ).grid(row=0, column=4, padx=8, pady=5)

        self.search_suggestion_box = tk.Listbox(
            search_outer,
            height=5,
            activestyle="dotbox",
            exportselection=False,
        )
        self.search_suggestion_box.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        self.search_suggestion_box.bind("<<ListboxSelect>>", self._select_search_suggestion)
        self.search_suggestion_box.bind("<Return>", self._select_search_suggestion)
        self.search_suggestion_box.grid_remove()

        self.search_result_text = ctk.CTkTextbox(
            main_frame,
            font=("Courier", 12),
            state=tk.DISABLED,
            border_width=1,
        )
        self.search_result_text.pack(expand=True, fill="both", padx=5, pady=(0, 5))

    # --- TAB DANH SÁCH LỚP HỌC PHẦN ---

    def _build_tab_class(self):
        main_frame = ctk.CTkFrame(self.tab_class, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=5, pady=5)

        class_outer = self._section_frame(main_frame, "DANH SÁCH LỚP HỌC PHẦN")
        class_outer.pack(expand=True, fill="both", padx=5, pady=(5, 10))
        class_outer.grid_columnconfigure(0, weight=1)
        class_outer.grid_rowconfigure(1, weight=1)

        class_cols = ("Kỳ thi", "Mã HP", "Tên học phần", "ID lớp HP", "Tên lớp SV", "Số SV", "Điểm TB", "Tỷ lệ đạt")
        self.tree_class = self._make_treeview(class_outer, class_cols, row=1, pady=(0, 8))
        self.tree_class.bind("<<TreeviewSelect>>", self._show_class_detail)

        student_outer = self._section_frame(main_frame, "SINH VIÊN TRONG LỚP")
        student_outer.pack(expand=True, fill="both", padx=5, pady=(0, 5))
        student_outer.grid_columnconfigure(0, weight=1)
        student_outer.grid_rowconfigure(1, weight=1)

        student_cols = ("Hạng", "MSSV", "Họ tên", "Mã lớp SV", "Tên lớp SV", "Điểm", "Đúng/Tổng", "Tỷ lệ")
        self.tree_class_students = self._make_treeview(student_outer, student_cols, row=1, pady=(0, 8))

    # --- Tạo bảng có thanh cuộn ---

    def _make_treeview(self, parent, columns, row: int = 0, pady=8) -> ttk.Treeview:
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

    def _load_initial_class_roster(self):
        student_path = self.var_student_path.get()
        try:
            self.exam_store = load_exam_store(self._resolve_exam_metadata_path())
            if os.path.exists(student_path):
                self.students = load_students(student_path)
        except Exception:
            self.students = None
            self.class_summary = []
            self._refresh_class_tab()
            return

        if self.students is None:
            self.class_summary = []
        else:
            self.class_summary = build_class_roster_summary(self.students)
        self._refresh_class_tab()

    # --- Xử lý thao tác ---

    def _browse_answer(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            self.var_answer_path.set(path)

    def _browse_students(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            self.var_student_path.set(path)
            self.results = None
            self.question_stats = None
            self.result_rows = []
            self.display_rows = []
            self.score_index = []
            self.student_id_trie = None
            self.student_search_index = None
            self.exam_ids = []
            self.class_names = []
            self._load_initial_class_roster()

    def _run_grading(self):
        answer_path = self.var_answer_path.get()
        student_path = self.var_student_path.get()

        if not os.path.exists(answer_path):
            messagebox.showerror("Lỗi", f"Không tìm thấy file:\n{answer_path}")
            return
        if not os.path.exists(student_path):
            messagebox.showerror("Lỗi", f"Không tìm thấy file:\n{student_path}")
            return

        try:
            self.status_var.set("Đang xử lý...")
            self.update()

            # Đọc dữ liệu.
            self.answer_key = load_answer_key(answer_path)
            self.exam_store = load_exam_store(self._resolve_exam_metadata_path())
            self.students = load_students(student_path)
            self.exam_store = infer_exam_store(self.answer_key, self.students, self.exam_store)

            # Chấm điểm.
            self.results = grade_all(self.students, self.answer_key)
            self.result_rows = build_result_rows_in_student_order(self.students, self.results)
            self.display_rows = []
            self.score_index = build_score_index(self.results)
            self.student_search_index = build_student_search_index(self.results)
            self.student_id_trie = self.student_search_index.student_id_trie
            self.exam_ids = get_exam_ids(self.results)
            self.class_names = get_class_names(self.results)
            self.var_exam_filter.set("Tất cả")
            self.var_class_filter.set("Tất cả")
            self.var_result_sort.set(SORT_CSV_ORDER)
            self.exam_filter.configure(values=["Tất cả"] + self.exam_ids)
            self.class_filter.configure(values=["Tất cả"] + self.class_names)
            first_exam = self.exam_ids[0] if self.exam_ids else "Chưa có dữ liệu"
            self.var_question_exam_filter.set(first_exam)
            self.question_exam_filter.configure(values=self.exam_ids or ["Chưa có dữ liệu"])

            # Thống kê câu hỏi.
            self.question_stats = compute_question_stats(self.students, self.answer_key)
            self.class_summary = build_class_summary(self.results)
            self.exam_summary = build_exam_summary(
                self.exam_store,
                self.answer_key,
                self.students,
                self.results,
            )

            # Cập nhật giao diện.
            self._refresh_results_tab()
            self._refresh_exam_tab()
            self._refresh_class_tab()
            self._refresh_stats_tab()
            self._refresh_question_tab()

            n = len(self.results)
            self.status_var.set(
                f"Hoàn thành! Đã chấm {n} thí sinh | {len(self.exam_ids)} kỳ thi | {len(self.answer_key)} đáp án."
            )

        except Exception as e:
            messagebox.showerror("Loi xu ly", str(e))
            self.status_var.set("Co loi xay ra.")

    def _resolve_exam_metadata_path(self):
        for data_path in (self.var_answer_path.get(), self.var_student_path.get()):
            candidate = os.path.join(os.path.dirname(data_path), "exams.csv")
            if os.path.exists(candidate):
                return candidate
        return DEFAULT_EXAMS

    def _export(self):
        if self.results is None:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng chấm điểm trước.")
            return
        try:
            export_results_csv(self.results, os.path.join(OUTPUT_DIR, "results.csv"))
            export_question_stats_csv(
                self.question_stats,
                os.path.join(OUTPUT_DIR, "question_stats.csv"),
            )
            messagebox.showinfo("Thanh cong", f"Da xuat file vao:\n{OUTPUT_DIR}")
        except Exception as e:
            messagebox.showerror("Loi xuat file", str(e))

    def _regrade_current_data(self):
        self.results = grade_all(self.students, self.answer_key)
        self.result_rows = build_result_rows_in_student_order(self.students, self.results)
        self.display_rows = []
        self.score_index = build_score_index(self.results)
        self.student_search_index = build_student_search_index(self.results)
        self.student_id_trie = self.student_search_index.student_id_trie
        self.question_stats = compute_question_stats(self.students, self.answer_key)
        self.class_summary = build_class_summary(self.results)
        self.exam_summary = build_exam_summary(
            self.exam_store,
            self.answer_key,
            self.students,
            self.results,
        )
        self._refresh_results_tab()
        self._refresh_exam_tab()
        self._refresh_class_tab()
        self._refresh_stats_tab()
        self._refresh_question_tab()
        self._clear_student_answer_detail()

    def _update_search_suggestions(self, event=None):
        if event is not None and event.keysym in ("Return", "Up", "Down", "Escape"):
            if event.keysym == "Escape":
                self._hide_search_suggestions()
            return

        prefix = self.var_search.get().strip()
        suggestions = get_student_id_suggestions(self.student_id_trie, prefix, limit=8)

        self.search_suggestion_box.delete(0, tk.END)
        if not suggestions:
            self._hide_search_suggestions()
            return

        for student_id in suggestions:
            self.search_suggestion_box.insert(tk.END, student_id)
        self.search_suggestion_box.grid()

    def _hide_search_suggestions(self):
        self.search_suggestion_box.grid_remove()

    def _select_search_suggestion(self, event=None):
        selection = self.search_suggestion_box.curselection()
        if not selection:
            return

        self.var_search.set(self.search_suggestion_box.get(selection[0]))
        self._hide_search_suggestions()
        self.entry_search.focus_set()
        if event is not None and getattr(event, "keysym", "") == "Return":
            self._do_search()

    def _do_search(self):
        if self.results is None:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng chấm điểm trước.")
            return

        sid = self.var_search.get().strip()
        name_query = self.var_search_name.get().strip()
        if not sid and not name_query:
            return

        if sid:
            if self.student_search_index is not None:
                matches = search_students_indexed(self.student_search_index, sid, self.var_exam_filter.get())
            else:
                matches = search_students(self.results, sid, self.var_exam_filter.get())
            query_label = f"MSSV: {sid}"
        else:
            matches = search_students_by_name(self.results, name_query, self.var_exam_filter.get())
            query_label = f"Họ tên: {name_query}"

        self.search_result_text.configure(state=tk.NORMAL)
        self.search_result_text.delete("1.0", tk.END)

        if not matches:
            self.search_result_text.insert(tk.END, f"Không tìm thấy thí sinh theo {query_label}")
        else:
            lines = [f"Kết quả tìm kiếm theo {query_label}: {len(matches)} kết quả"]
            for result in matches:
                lines.extend([
                    "=" * 45,
                    f"  Kỳ thi      : {result.exam_id}",
                    f"  MSSV        : {result.student_id}",
                    f"  Họ và tên   : {result.student_name}",
                    f"  ID lớp HP   : {result.class_id}",
                    f"  Mã lớp SV   : {result.admin_class_id}",
                    f"  Tên lớp SV  : {result.class_name}",
                    f"  Điểm số     : {result.score} / 10",
                    f"  Số câu đúng : {result.correct_count} / {result.total_questions}",
                    f"  Tỷ lệ đúng  : {result.accuracy_percent}%",
                    f"  Các câu sai : {self._format_wrong_questions(result.wrong_questions)}",
                ])
            lines.append("=" * 45)
            self.search_result_text.insert(tk.END, "\n".join(lines))

        self.search_result_text.configure(state=tk.DISABLED)

    def _format_wrong_questions(self, question_ids: list) -> str:
        if not question_ids:
            return "Không có"

        def sort_key(question_id):
            question_id = normalize_question_id(question_id)
            if str(question_id).isdigit():
                return (0, int(question_id))
            return (1, str(question_id))

        return ", ".join(f"Câu {qid}" for qid in sorted(question_ids, key=sort_key))

    def _apply_result_filters(self, rows: list) -> list:
        rows = get_results_by_exam(rows, self.var_exam_filter.get())
        rows = get_results_by_class(rows, self.var_class_filter.get())
        return rows

    def _sort_result_rows_for_display(self, rows: list) -> list:
        return sort_results(rows, self.var_result_sort.get())

    def _display_result_rows(self, rows: list, status_text: str | None = None):
        self.display_rows = rows
        self._fill_results_tree(rows)
        if status_text is not None:
            self.status_var.set(status_text)

    def _filter_class(self):
        self._filter_exam_or_class()

    def _filter_exam_or_class(self):
        if self.results is None:
            return

        rows = self._apply_result_filters(self.result_rows)
        rows = self._sort_result_rows_for_display(rows)
        self._display_result_rows(rows)
        self.status_var.set(f"Đang hiển thị {len(rows)} sinh viên.")

    def _filter_score_range(self):
        if self.results is None:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng chấm điểm trước.")
            return

        try:
            low = float(self.var_score_low.get())
            high = float(self.var_score_high.get())
        except ValueError:
            messagebox.showerror("Giá trị không hợp lệ", "Điểm lọc phải là số.")
            return

        filtered = get_students_in_score_range(self.score_index, low, high)
        filtered_keys = {
            (result.exam_id, result.student_id)
            for result in filtered
        }
        rows = [
            result
            for result in self.result_rows
            if (result.exam_id, result.student_id) in filtered_keys
        ]
        rows = self._apply_result_filters(rows)
        rows = self._sort_result_rows_for_display(rows)
        self._display_result_rows(rows)
        self.status_var.set(
            f"Đang hiển thị {len(rows)} thí sinh có điểm từ {min(low, high)} đến {max(low, high)}."
        )

    def _show_all_results(self):
        if self.results is None:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng chấm điểm trước.")
            return

        self.var_exam_filter.set("Tất cả")
        self.var_class_filter.set("Tất cả")
        rows = self._sort_result_rows_for_display(self.result_rows)
        self._display_result_rows(rows, f"Đang hiển thị tất cả {len(rows)} thí sinh.")

    def _show_top_k(self):
        if self.results is None:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng chấm điểm trước.")
            return

        try:
            k = int(self.var_top_k.get())
        except ValueError:
            messagebox.showerror("Giá trị không hợp lệ", "Top phải là số nguyên.")
            return

        class_name = self.var_class_filter.get()
        exam_id = self.var_exam_filter.get()
        if class_name == "Tất cả" and exam_id == "Tất cả":
            top_results = get_top_k_results(self.results, k)
        else:
            rows = self._apply_result_filters(self.result_rows)
            rows = sort_results(rows, SORT_SCORE_DESC)
            top_results = rows[:max(k, 0)]
        self._display_result_rows(top_results, f"Đang hiển thị top {len(top_results)} thí sinh.")

    def _show_student_answers(self, _event=None):
        if self.results is None:
            return

        selection = self.tree_results.selection()
        if not selection:
            return

        values = self.tree_results.item(selection[0], "values")
        if len(values) < 3:
            return

        exam_id = values[1]
        student_id = values[2]
        result = None
        for item in self.results.values():
            if item.exam_id == exam_id and item.student_id == student_id:
                result = item
                break
        if result is None:
            return

        for row in self.tree_student_answers.get_children():
            self.tree_student_answers.delete(row)

        for item in get_student_answer_items(result, self.answer_key):
            status = "Đúng" if item["is_correct"] else "Sai"
            self.tree_student_answers.insert("", tk.END, values=(
                f"Câu {item['question_id']}",
                item["selected_answer"],
                item["correct_answer"],
                status,
            ))

    def _clear_student_answer_detail(self):
        for row in self.tree_student_answers.get_children():
            self.tree_student_answers.delete(row)

    def _load_selected_answer(self, _event=None):
        selection = self.tree_answer_key.selection()
        if not selection:
            return
        values = self.tree_answer_key.item(selection[0], "values")
        if len(values) >= 3:
            self.var_new_answer.set(values[2])

    def _update_selected_answer(self):
        if self.answer_key is None:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng chấm điểm trước.")
            return

        selection = self.tree_answer_key.selection()
        if not selection:
            messagebox.showwarning("Chưa chọn câu", "Vui lòng chọn một câu trong bảng đáp án.")
            return

        new_answer = self.var_new_answer.get().strip().upper()
        if not new_answer:
            messagebox.showerror("Đáp án không hợp lệ", "Đáp án mới không được để trống.")
            return

        values = self.tree_answer_key.item(selection[0], "values")
        exam_id = values[0]
        question_id = normalize_question_id(values[1])

        try:
            self.answer_key.update_answer(exam_id, question_id, new_answer)
            self._regrade_current_data()
            self.status_var.set(f"Đã cập nhật đáp án {exam_id} - Câu {question_id}.")
        except Exception as exc:
            messagebox.showerror("Lỗi cập nhật đáp án", str(exc))

    # --- Cập nhật từng tab ---

    def _refresh_results_tab(self):
        if self.results is None:
            return
        rows = self._apply_result_filters(self.result_rows)
        rows = self._sort_result_rows_for_display(rows)
        self._display_result_rows(rows)

    def _fill_results_tree(self, rows: list):
        tree = self.tree_results
        for row in tree.get_children():
            tree.delete(row)

        for pos, r in enumerate(rows, start=1):
            tag = ""
            if pos == 1:
                tag = "gold"
            elif r.score < 5.0:
                tag = "fail"

            tree.insert("", tk.END, values=(
                pos,
                r.exam_id,
                r.student_id,
                r.student_name,
                r.class_id,
                r.admin_class_id,
                r.class_name,
                f"{r.score:.2f}",
                r.correct_count,
                r.total_questions,
                f"{r.accuracy_percent}%",
            ), tags=(tag,))

        tree.tag_configure("gold")
        tree.tag_configure("fail")

    def _refresh_stats_tab(self):
        stats = build_exam_statistics(self.results)
        lines = [
            "=" * 50,
            "         Thống kê tổng hợp kỳ thi",
            "=" * 50,
            f"  Tổng số thí sinh  : {len(stats.results)}",
            f"  Số kỳ thi/đề thi  : {len(self.exam_ids)}",
            f"  Tổng số đáp án    : {len(self.answer_key)}",
            f"  Số lớp học phần   : {len(self.class_names)}",
            "-" * 50,
            f"  Điểm trung bình   : {stats.average:.2f}",
            f"  Điểm cao nhất     : {stats.max_score:.2f}",
            f"  Điểm thấp nhất    : {stats.min_score:.2f}",
            f"  Độ lệch chuẩn     : {stats.std_dev:.2f}",
            "-" * 50,
            f"  Số thí sinh đạt   : {stats.passing_count()} ({stats.passing_rate()}%)",
            f"  Số thí sinh rớt   : {stats.failing_count()}",
        ]

        lines.extend([
            "-" * 50,
            "  Thống kê theo mã lớp học phần:",
        ])
        for item in build_class_summary(self.results):
            lines.append(
                f"    {item['exam_id']:<8} {item['class_id']:<12}: {item['count']:>3} SV | "
                f"DTB {item['average']:>5.2f} | Đạt {item['passing_rate']:>5.1f}%"
            )

        lines.append("=" * 50)

        self.stats_text.configure(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert(tk.END, "\n".join(lines))
        self.stats_text.configure(state=tk.DISABLED)

    def _refresh_exam_tab(self):
        tree = self.tree_exam
        for row in tree.get_children():
            tree.delete(row)

        for item in self.exam_summary:
            tree.insert("", tk.END, iid=item["exam_id"], values=(
                item["exam_id"],
                item["course_code"] or "-",
                item["semester"] or "-",
                item["question_count"],
                item["student_count"],
                item["class_count"],
            ))

        self._write_exam_detail([
            "Chọn một kỳ thi/đề thi trong bảng bên trái để xem thông tin.",
            "Màn hình này chỉ hiện metadata và thống kê tổng quan, không hiện danh sách câu hỏi.",
        ])

    def _show_exam_detail(self, _event=None):
        selection = self.tree_exam.selection()
        if not selection:
            return

        exam_id = selection[0]
        item = None
        for row in self.exam_summary:
            if row["exam_id"] == exam_id:
                item = row
                break
        if item is None:
            return

        lines = [
            "=" * 52,
            "  THÔNG TIN KỲ THI / ĐỀ THI",
            "=" * 52,
            f"  Mã kỳ thi       : {item['exam_id']}",
            f"  Tên kỳ thi      : {item['exam_name']}",
            f"  Mã học phần     : {item['course_code'] or '-'}",
            f"  Tên học phần    : {item['course_name'] or '-'}",
            f"  Học kỳ          : {item['semester'] or '-'}",
            f"  Ngày thi        : {item['exam_date'] or '-'}",
            f"  Thời lượng      : {item['duration_minutes'] or '-'} phút",
            "-" * 52,
            f"  Số câu hỏi      : {item['question_count']}",
            f"  Số sinh viên    : {item['student_count']}",
            f"  Số lớp học phần : {item['class_count']}",
            f"  Điểm trung bình : {item['average']:.2f}",
            f"  Tỷ lệ đạt       : {item['passing_rate']}%",
            "-" * 52,
            f"  Ghi chú         : {item['note'] or '-'}",
            "=" * 52,
        ]
        self._write_exam_detail(lines)

    def _write_exam_detail(self, lines: list[str]):
        self.exam_detail_text.configure(state=tk.NORMAL)
        self.exam_detail_text.delete("1.0", tk.END)
        self.exam_detail_text.insert(tk.END, "\n".join(lines))
        self.exam_detail_text.configure(state=tk.DISABLED)

    def _refresh_class_tab(self):
        for row in self.tree_class.get_children():
            self.tree_class.delete(row)

        for item in self.class_summary:
            exam = self.exam_store.get(item["exam_id"]) if self.exam_store is not None else None
            average = item.get("average")
            passing_rate = item.get("passing_rate")
            iid = f"{item['exam_id']}|{item['class_id']}"
            self.tree_class.insert("", tk.END, iid=iid, values=(
                item["exam_id"],
                exam.course_code if exam and exam.course_code else "-",
                exam.course_name if exam and exam.course_name else "-",
                item["class_id"],
                item["class_name"],
                item["count"],
                f"{average:.2f}" if average is not None else "-",
                f"{passing_rate}%" if passing_rate is not None else "-",
            ))

        for row in self.tree_class_students.get_children():
            self.tree_class_students.delete(row)

    def _show_class_detail(self, _event=None):
        selection = self.tree_class.selection()
        if not selection:
            return

        values = self.tree_class.item(selection[0], "values")
        if len(values) < 4:
            return

        exam_id = values[0]
        class_id = values[3]
        if self.results is None:
            self.status_var.set(
                f"Lớp học phần {class_id} ({exam_id}) đã có trong file thí sinh. Chấm điểm để xem danh sách điểm."
            )
            return

        rows = get_results_by_exam(self.result_rows, exam_id)
        rows = get_results_by_class(rows, class_id)
        rows = sort_results(rows, SORT_SCORE_DESC)

        for row in self.tree_class_students.get_children():
            self.tree_class_students.delete(row)

        for pos, result in enumerate(rows, start=1):
            self.tree_class_students.insert("", tk.END, values=(
                pos,
                result.student_id,
                result.student_name,
                result.admin_class_id,
                result.class_name,
                f"{result.score:.2f}",
                f"{result.correct_count}/{result.total_questions}",
                f"{result.accuracy_percent}%",
            ))

        self.status_var.set(
            f"Lớp học phần {class_id} ({exam_id}) có {len(rows)} sinh viên."
        )

    def _refresh_question_tab(self):
        tree = self.tree_question
        for row in tree.get_children():
            tree.delete(row)

        if self.question_stats is None or self.answer_key is None:
            self.hardest_text.configure(state=tk.NORMAL)
            self.hardest_text.delete("1.0", tk.END)
            self.hardest_text.insert(tk.END, "Chưa có dữ liệu câu hỏi.")
            self.hardest_text.configure(state=tk.DISABLED)
            for row in self.tree_answer_key.get_children():
                self.tree_answer_key.delete(row)
            return

        selected_exam = self.var_question_exam_filter.get()
        items = get_question_stats_items(self.question_stats)
        for data in items:
            if selected_exam and selected_exam != "Chưa có dữ liệu" and data["exam_id"] != selected_exam:
                continue

            total = data["total"]
            correct = data["correct"]
            wrong = total - correct
            rate = round(correct / total * 100, 1) if total > 0 else 0.0

            tag = "easy" if rate >= 80 else ("hard" if rate < 40 else "")
            tree.insert("", tk.END, values=(
                data["exam_id"], f"Câu {data['question_id']}", correct, wrong, f"{rate}%"
            ), tags=(tag,))

        tree.tag_configure("easy")
        tree.tag_configure("hard")

        hardest = [
            item for item in get_hardest_questions(self.question_stats, len(self.question_stats))
            if not selected_exam or selected_exam == "Chưa có dữ liệu" or item[0] == selected_exam
        ][:5]
        lines = [f"Top 5 câu hỏi khó nhất ({selected_exam}):"]
        for exam_id, qid, correct, total, rate in hardest:
            wrong = total - correct
            lines.append(
                f"  {exam_id:<8} Câu {qid:<3} | Đúng: {correct:>4}/{total:<4} | Sai: {wrong:>4} | Tỷ lệ đúng: {rate:>5.1f}%"
            )

        self.hardest_text.configure(state=tk.NORMAL)
        self.hardest_text.delete("1.0", tk.END)
        self.hardest_text.insert(tk.END, "\n".join(lines))
        self.hardest_text.configure(state=tk.DISABLED)

        for row in self.tree_answer_key.get_children():
            self.tree_answer_key.delete(row)

        for question in get_answer_key_items(self.answer_key, selected_exam):
            self.tree_answer_key.insert("", tk.END, values=(
                question.exam_id,
                f"Câu {question.question_id}",
                question.correct_answer,
            ))

# --- Điểm chạy chương trình ---

if __name__ == "__main__":
    app = App()
    app.mainloop()
