"""Cửa sổ CustomTkinter điều phối thao tác của hệ thống chấm điểm.

Lớp ``App`` sở hữu trạng thái phiên làm việc của giao diện. Mọi tính toán dữ
liệu được chuyển cho ``app_logic``; module này chỉ đọc giá trị widget, cập nhật
widget và hiển thị thông báo cho người dùng.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

import customtkinter as ctk

from app_logic import (
    AnswerKeyBook,
    load_answer_key,
    load_exam_store,
    load_students,
    validate_answer_key_csv,
    validate_students_csv,
    validate_grading_inputs,
    infer_exam_store,
    grade_all,
    compute_question_stats,
    export_results_csv,
    export_question_stats_csv,
    export_answer_key_csv,
    build_student_search_index,
    search_students_indexed,
    get_student_id_suggestions,
    get_student_name_suggestions,
    search_students_by_name_prefix,
    SORT_CSV_ORDER,
    SORT_SCORE_DESC,
    build_result_rows_in_student_order,
    sort_results,
    build_score_index,
    parse_score_range,
    get_students_in_score_range,
    get_hardest_questions,
    get_question_stats_items,
    get_student_answer_items,
    get_exam_ids,
    get_results_by_exam,
    get_class_names,
    get_results_by_class,
    build_class_summary,
    build_class_roster_summary,
)
from models import Question
from ui.answer_key_tab import build_answer_key_tab
from ui.class_tab import build_class_tab
from ui.question_tab import build_question_tab
from ui.results_tab import build_results_tab
from ui.search_tab import build_search_tab

# Các đường dẫn mặc định được tính từ thư mục mã nguồn để không phụ thuộc cwd.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ANSWER_KEY = os.path.join(BASE_DIR, "data", "answer_key.csv")
DEFAULT_STUDENTS = os.path.join(BASE_DIR, "data", "students.csv")
DEFAULT_EXAMS = os.path.join(BASE_DIR, "data", "exams.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """Cửa sổ chính và trạng thái hiện tại của phiên chấm điểm."""

    def __init__(self):
        """Khởi tạo trạng thái ứng dụng, widget và dữ liệu mặc định."""
        super().__init__()
        self.title("Hệ thống Chấm Điểm Trắc Nghiệm")
        self.geometry("1280x850")
        self.minsize(980, 680)
        self.resizable(True, True)

        # Trạng thái dữ liệu.
        self.answer_key = None
        self.answer_key_dirty = False
        self.answer_key_source_path = None
        self.exam_store = None
        self.students = None
        self.results = None
        self.question_stats = None
        self.class_summary = []
        self.result_rows = []
        self.display_rows = []
        self.score_index = []
        self.student_search_index = None
        self.exam_ids = []
        self.class_names = []

        self._build_ui()
        self._load_initial_answer_key()
        self._load_initial_class_roster()

    # Xây dựng giao diện

    def _build_ui(self):
        """Tạo thanh công cụ, các tab và biến trạng thái hiển thị."""
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
        self.tab_answer_key = self.tabview.add("Quản lý đáp án")
        self.tab_class = self.tabview.add("Danh sách lớp HP")
        self.tab_question = self.tabview.add("Thống kê câu hỏi")
        self.tab_search = self.tabview.add("Tìm kiếm thí sinh")

        build_results_tab(self)
        build_answer_key_tab(self)
        build_class_tab(self)
        build_question_tab(self)
        build_search_tab(self)

        # Thanh trạng thái.
        self.status_var = tk.StringVar(value="Sẵn sàng. Chọn file và nhấn CHẤM ĐIỂM.")
        status = ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            anchor="w",
            height=30,
        )
        status.pack(fill="x", padx=10, pady=(0, 6))

    def _configure_ttk_style(self):
        """Áp dụng kiểu hiển thị chung cho mọi Treeview trong ứng dụng."""
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

    def _load_initial_class_roster(self):
        """Đọc file sinh viên hiện tại và cập nhật danh sách lớp ban đầu."""
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

    def _load_initial_answer_key(self):
        """Nạp kho đáp án mặc định nếu file tồn tại và hợp lệ."""
        answer_path = self.var_answer_path.get()
        if not os.path.exists(answer_path):
            self._refresh_answer_key_tab()
            return

        try:
            if validate_answer_key_csv(answer_path):
                self._refresh_answer_key_tab()
                return
            self.answer_key = load_answer_key(answer_path)
            self.answer_key_dirty = False
            self.answer_key_source_path = answer_path
        except Exception:
            self.answer_key = None
            self.answer_key_dirty = False
            self.answer_key_source_path = None
        self._refresh_answer_key_tab()

    # Xử lý thao tác

    def _browse_answer(self):
        """Chọn file đáp án và nạp file đó vào tab quản lý."""
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            self.var_answer_path.set(path)
            self.answer_key_dirty = False
            self.answer_key_source_path = None
            self._load_answer_key_for_management()

    def _browse_students(self):
        """Chọn file sinh viên, xóa kết quả cũ và cập nhật danh sách lớp."""
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            self.var_student_path.set(path)
            self.results = None
            self.question_stats = None
            self.result_rows = []
            self.display_rows = []
            self.score_index = []
            self.student_search_index = None
            self.exam_ids = []
            self.class_names = []
            self._load_initial_class_roster()

    def _run_grading(self):
        """Validate file đầu vào, chấm toàn bộ bài và làm mới các tab.

        Hàm đọc đường dẫn từ widget, có thể đọc ba file CSV và cập nhật toàn bộ
        trạng thái kết quả của cửa sổ. Lỗi dữ liệu được hiển thị qua messagebox.
        """
        answer_path = self.var_answer_path.get()
        student_path = self.var_student_path.get()

        if not os.path.exists(answer_path):
            messagebox.showerror("Lỗi", f"Không tìm thấy file:\n{answer_path}")
            return
        if not os.path.exists(student_path):
            messagebox.showerror("Lỗi", f"Không tìm thấy file:\n{student_path}")
            return

        try:
            validation_errors = (
                validate_answer_key_csv(answer_path)
                + validate_students_csv(student_path)
            )
            if validation_errors:
                messagebox.showerror("Dữ liệu không hợp lệ", "\n".join(validation_errors))
                return

            self.status_var.set("Đang xử lý...")
            self.update()

            # Dùng đáp án đang sửa nếu chưa lưu ra file.
            if self.answer_key_dirty and self.answer_key is not None:
                if len(self.answer_key) == 0:
                    messagebox.showerror("Dữ liệu không hợp lệ", "Kho đáp án đang trống.")
                    self.status_var.set("Dữ liệu không hợp lệ.")
                    return
            else:
                self.answer_key = load_answer_key(answer_path)
                self.answer_key_dirty = False
                self.answer_key_source_path = answer_path
                self._refresh_answer_key_tab()
            self.exam_store = load_exam_store(self._resolve_exam_metadata_path())
            self.students = load_students(student_path)
            validation_errors = validate_grading_inputs(self.answer_key, self.students)
            if validation_errors:
                messagebox.showerror("Dữ liệu không hợp lệ", "\n".join(validation_errors))
                self.status_var.set("Dữ liệu không hợp lệ.")
                return
            self.exam_store = infer_exam_store(self.answer_key, self.students, self.exam_store)

            self.results = grade_all(self.students, self.answer_key)
            self.result_rows = build_result_rows_in_student_order(self.students, self.results)
            self.display_rows = []
            self.score_index = build_score_index(self.results)
            self.student_search_index = build_student_search_index(self.results)
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

            self.question_stats = compute_question_stats(self.students, self.answer_key)
            self.class_summary = build_class_summary(self.results)

            self._refresh_results_tab()
            self._refresh_class_tab()
            self._refresh_question_tab()

            n = len(self.results)
            self.status_var.set(
                f"Hoàn thành! Đã chấm {n} thí sinh | {len(self.exam_ids)} kỳ thi | {len(self.answer_key)} đáp án."
            )

        except Exception as e:
            messagebox.showerror("Loi xu ly", str(e))
            self.status_var.set("Co loi xay ra.")

    def _resolve_exam_metadata_path(self):
        """Trả về file ``exams.csv`` gần dữ liệu đang chọn hoặc file mặc định."""
        for data_path in (self.var_answer_path.get(), self.var_student_path.get()):
            candidate = os.path.join(os.path.dirname(data_path), "exams.csv")
            if os.path.exists(candidate):
                return candidate
        return DEFAULT_EXAMS

    def _export(self):
        """Ghi kết quả và thống kê hiện tại vào thư mục ``output``."""
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

    def _load_answer_key_for_management(self):
        """Validate và nạp file đáp án đang chọn vào trạng thái chỉnh sửa."""
        answer_path = self.var_answer_path.get()
        if not os.path.exists(answer_path):
            messagebox.showerror("Lỗi", f"Không tìm thấy file:\n{answer_path}")
            return

        try:
            validation_errors = validate_answer_key_csv(answer_path)
            if validation_errors:
                messagebox.showerror("Dữ liệu không hợp lệ", "\n".join(validation_errors))
                return

            self.answer_key = load_answer_key(answer_path)
            self.answer_key_dirty = False
            self.answer_key_source_path = answer_path
            self._invalidate_grading_outputs()
            self._refresh_answer_key_tab()
            self.status_var.set(f"Đã nạp {len(self.answer_key)} đáp án từ CSV.")
        except Exception as e:
            messagebox.showerror("Lỗi nạp đáp án", str(e))

    def _save_answer_key_question(self):
        """Thêm hoặc cập nhật một đáp án từ ba ô nhập trên giao diện."""
        exam_id = self.var_key_exam_id.get().strip()
        question_id = self.var_key_question_id.get().strip()
        correct_answer = self.var_key_answer.get()

        if not exam_id or not question_id or not correct_answer.strip():
            messagebox.showerror("Dữ liệu không hợp lệ", "Mã đề, câu hỏi và đáp án không được để trống.")
            return
        if (
            not question_id.isdigit()
            or int(question_id) < 1
            or question_id != str(int(question_id))
        ):
            messagebox.showerror("Dữ liệu không hợp lệ", "Câu hỏi phải có dạng 1, 2, 3, ...")
            return
        if self.answer_key is None:
            self.answer_key = AnswerKeyBook()

        question = Question(question_id=question_id, correct_answer=correct_answer, exam_id=exam_id)
        self.answer_key.put(question.exam_id, question)
        self.answer_key_dirty = True
        self._invalidate_grading_outputs()
        self._refresh_answer_key_tab()
        self._select_answer_key_iid(question.exam_id, question.question_id)
        self.status_var.set(
            f"Đã lưu đáp án: {question.exam_id} - Câu {question.question_id} = {question.correct_answer}. Chấm điểm lại để cập nhật kết quả."
        )

    def _delete_answer_key_question(self):
        """Xóa câu hỏi đang chọn sau khi người dùng xác nhận."""
        if self.answer_key is None:
            messagebox.showwarning("Chưa có dữ liệu", "Chưa có kho đáp án để xóa.")
            return

        exam_id = self.var_key_exam_id.get().strip()
        question_id = self.var_key_question_id.get().strip()
        if not exam_id or not question_id:
            messagebox.showerror("Dữ liệu không hợp lệ", "Chọn hoặc nhập mã đề và câu hỏi cần xóa.")
            return

        if not messagebox.askyesno("Xác nhận xóa", f"Xóa đáp án câu {question_id} của đề {exam_id}?"):
            return

        removed = self.answer_key.remove_question(exam_id, question_id)
        if not removed:
            messagebox.showwarning("Không tìm thấy", "Không tìm thấy đáp án cần xóa.")
            return

        self.answer_key_dirty = True
        self._invalidate_grading_outputs()
        self._refresh_answer_key_tab()
        self.status_var.set(f"Đã xóa câu {question_id} của đề {exam_id}.")

    def _delete_answer_key_exam(self):
        """Xóa toàn bộ đáp án của kỳ thi đang chọn sau khi xác nhận."""
        if self.answer_key is None:
            messagebox.showwarning("Chưa có dữ liệu", "Chưa có kho đáp án để xóa.")
            return

        exam_id = self.var_key_exam_id.get().strip()
        if not exam_id:
            messagebox.showerror("Dữ liệu không hợp lệ", "Nhập mã đề cần xóa.")
            return

        if not messagebox.askyesno("Xác nhận xóa", f"Xóa toàn bộ đáp án của đề {exam_id}?"):
            return

        removed_count = self.answer_key.remove_exam(exam_id)
        if removed_count == 0:
            messagebox.showwarning("Không tìm thấy", "Không tìm thấy đề cần xóa.")
            return

        self.answer_key_dirty = True
        self._invalidate_grading_outputs()
        self._refresh_answer_key_tab()
        self.status_var.set(f"Đã xóa đề {exam_id} với {removed_count} câu hỏi.")

    def _save_answer_key_csv(self):
        """Ghi kho đáp án đang chỉnh sửa tới file CSV do người dùng chọn."""
        if self.answer_key is None or len(self.answer_key) == 0:
            messagebox.showwarning("Chưa có dữ liệu", "Chưa có đáp án để lưu.")
            return

        initial_path = self.answer_key_source_path or self.var_answer_path.get() or DEFAULT_ANSWER_KEY
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialdir=os.path.dirname(initial_path),
            initialfile=os.path.basename(initial_path),
        )
        if not path:
            return

        try:
            export_answer_key_csv(self.answer_key, path)
            self.var_answer_path.set(path)
            self.answer_key_dirty = False
            self.answer_key_source_path = path
            messagebox.showinfo("Thành công", f"Đã lưu đáp án vào:\n{path}")
            self.status_var.set(f"Đã lưu {len(self.answer_key)} đáp án.")
        except Exception as e:
            messagebox.showerror("Lỗi lưu đáp án", str(e))

    def _select_answer_key_row(self, _event=None):
        """Đưa dữ liệu dòng đáp án được chọn trở lại các ô nhập."""
        selection = self.tree_answer_key.selection()
        if not selection:
            return

        values = self.tree_answer_key.item(selection[0], "values")
        if len(values) < 3:
            return

        self.var_key_exam_id.set(values[0])
        self.var_key_question_id.set(values[1])
        self.var_key_answer.set(values[2])

    def _refresh_answer_key_tab(self):
        """Vẽ lại bảng đáp án từ ``self.answer_key`` hiện tại."""
        tree = self.tree_answer_key
        for row in tree.get_children():
            tree.delete(row)

        if self.answer_key is None:
            return

        for exam_id in self.answer_key.exam_ids():
            exam_key = self.answer_key.get_exam_key(exam_id)
            if exam_key is None:
                continue
            question_ids = sorted(exam_key.keys(), key=self._answer_key_question_sort_value)
            for question_id in question_ids:
                question = exam_key.get(question_id)
                iid = self._answer_key_iid(exam_id, question.question_id)
                tree.insert("", tk.END, iid=iid, values=(
                    exam_id,
                    question.question_id,
                    question.correct_answer,
                ))

    def _select_answer_key_iid(self, exam_id: str, question_id: str):
        """Chọn và cuộn đến một dòng đáp án theo kỳ thi và câu hỏi."""
        iid = self._answer_key_iid(exam_id, question_id)
        if self.tree_answer_key.exists(iid):
            self.tree_answer_key.selection_set(iid)
            self.tree_answer_key.see(iid)

    def _answer_key_iid(self, exam_id: str, question_id: str) -> str:
        """Tạo định danh Treeview ổn định cho một câu hỏi."""
        return f"{exam_id}|{question_id}"

    def _answer_key_question_sort_value(self, question_id: str):
        """Chuyển mã câu hỏi đã validate thành khóa sắp xếp số nguyên."""
        return int(question_id)

    def _invalidate_grading_outputs(self):
        """Xóa mọi kết quả phụ thuộc vào kho đáp án vừa thay đổi."""
        self.results = None
        self.question_stats = None
        self.result_rows = []
        self.display_rows = []
        self.score_index = []
        self.student_search_index = None
        self.exam_ids = []
        self.class_names = []

        if hasattr(self, "tree_results"):
            for row in self.tree_results.get_children():
                self.tree_results.delete(row)
        if hasattr(self, "tree_student_answers"):
            self._clear_student_answer_detail()
        if hasattr(self, "exam_filter"):
            self.var_exam_filter.set("Tất cả")
            self.exam_filter.configure(values=["Tất cả"])
        if hasattr(self, "class_filter"):
            self.var_class_filter.set("Tất cả")
            self.class_filter.configure(values=["Tất cả"])
        if hasattr(self, "question_exam_filter"):
            self.var_question_exam_filter.set("Chưa có dữ liệu")
            self.question_exam_filter.configure(values=["Chưa có dữ liệu"])

        if self.students is not None:
            self.class_summary = build_class_roster_summary(self.students)
        else:
            self.class_summary = []
        if hasattr(self, "tree_class"):
            self._refresh_class_tab()
        if hasattr(self, "tree_question"):
            self._refresh_question_tab()

    def _update_search_suggestions(self, event=None):
        """Cập nhật gợi ý MSSV theo nội dung ô tìm kiếm hiện tại."""
        if event is not None and event.keysym in ("Return", "Up", "Down", "Escape"):
            if event.keysym == "Escape":
                self._hide_search_suggestions()
            return

        prefix = self.var_search.get().strip()
        student_id_trie = (
            self.student_search_index.student_id_trie
            if self.student_search_index is not None
            else None
        )
        suggestions = get_student_id_suggestions(student_id_trie, prefix, limit=8)
        self.search_suggestion_target = "mssv"

        self.search_suggestion_box.delete(0, tk.END)
        if not suggestions:
            self._hide_search_suggestions()
            return

        for student_id in suggestions:
            self.search_suggestion_box.insert(tk.END, student_id)
        self.search_suggestion_box.grid()

    def _update_search_name_suggestions(self, event=None):
        """Cập nhật gợi ý họ tên theo nội dung ô tìm kiếm hiện tại."""
        if event is not None and event.keysym in ("Return", "Up", "Down", "Escape"):
            if event.keysym == "Escape":
                self._hide_search_suggestions()
            return

        prefix = self.var_search_name.get().strip()
        suggestions = get_student_name_suggestions(self.student_search_index, prefix, limit=8)
        self.search_suggestion_target = "name"

        self.search_suggestion_box.delete(0, tk.END)
        if not suggestions:
            self._hide_search_suggestions()
            return

        for student_name in suggestions:
            self.search_suggestion_box.insert(tk.END, student_name)
        self.search_suggestion_box.grid()

    def _hide_search_suggestions(self):
        """Ẩn danh sách gợi ý tìm kiếm dùng chung."""
        self.search_suggestion_box.grid_remove()

    def _select_search_suggestion(self, event=None):
        """Chép gợi ý được chọn vào đúng ô tìm kiếm và thực hiện tra cứu."""
        selection = self.search_suggestion_box.curselection()
        if not selection:
            return

        selected_value = self.search_suggestion_box.get(selection[0])
        if self.search_suggestion_target == "name":
            self.var_search_name.set(selected_value)
            target_entry = self.entry_search_name
        else:
            self.var_search.set(selected_value)
            target_entry = self.entry_search
        self._hide_search_suggestions()
        target_entry.focus_set()
        if event is not None and getattr(event, "keysym", "") == "Return":
            self._do_search()

    def _do_search(self):
        """Tra cứu theo MSSV hoặc tiền tố họ tên và hiển thị kết quả."""
        if self.results is None:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng chấm điểm trước.")
            return

        sid = self.var_search.get().strip()
        name_query = self.var_search_name.get().strip()
        if not sid and not name_query:
            return

        if sid:
            matches = search_students_indexed(self.student_search_index, sid)
            query_label = f"MSSV: {sid}"
        else:
            matches = search_students_by_name_prefix(
                self.student_search_index,
                name_query,
                limit=len(self.student_search_index.all_rows),
            )
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
        """Trả về chuỗi mã câu sai đã sắp xếp để hiển thị."""
        if not question_ids:
            return "Không có"

        def sort_key(question_id):
            """Chuyển mã câu hỏi thành khóa số để sắp xếp."""
            return int(question_id)

        return ", ".join(f"Câu {qid}" for qid in sorted(question_ids, key=sort_key))

    def _apply_result_filters(self, rows: list) -> list:
        """Lọc ``rows`` theo kỳ thi và lớp đang chọn, không đổi danh sách gốc."""
        rows = get_results_by_exam(rows, self.var_exam_filter.get())
        rows = get_results_by_class(rows, self.var_class_filter.get())
        return rows

    def _sort_result_rows_for_display(self, rows: list) -> list:
        """Trả về bản sao ``rows`` theo tùy chọn sắp xếp của giao diện."""
        return sort_results(rows, self.var_result_sort.get())

    def _display_result_rows(self, rows: list, status_text: str | None = None):
        """Nạp các dòng kết quả vào bảng và tùy chọn cập nhật trạng thái."""
        self.display_rows = rows
        self._fill_results_tree(rows)
        if status_text is not None:
            self.status_var.set(status_text)

    def _filter_exam_or_class(self):
        """Áp dụng bộ lọc kỳ thi/lớp và vẽ lại bảng kết quả."""
        if self.results is None:
            return

        rows = self._apply_result_filters(self.result_rows)
        rows = self._sort_result_rows_for_display(rows)
        self._display_result_rows(rows)
        self.status_var.set(f"Đang hiển thị {len(rows)} sinh viên.")

    def _filter_score_range(self):
        """Validate khoảng điểm, kết hợp các bộ lọc và vẽ lại kết quả."""
        if self.results is None:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng chấm điểm trước.")
            return

        try:
            low, high = parse_score_range(
                self.var_score_low.get(),
                self.var_score_high.get(),
            )
        except ValueError as exc:
            messagebox.showerror("Giá trị không hợp lệ", str(exc))
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
        """Đặt lại bộ lọc kỳ thi/lớp và hiển thị toàn bộ kết quả."""
        if self.results is None:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng chấm điểm trước.")
            return

        self.var_exam_filter.set("Tất cả")
        self.var_class_filter.set("Tất cả")
        rows = self._sort_result_rows_for_display(self.result_rows)
        self._display_result_rows(rows, f"Đang hiển thị tất cả {len(rows)} thí sinh.")

    def _show_student_answers(self, _event=None):
        """Hiển thị đáp án chi tiết của dòng kết quả đang chọn."""
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
        """Xóa toàn bộ dòng khỏi bảng chi tiết bài làm."""
        for row in self.tree_student_answers.get_children():
            self.tree_student_answers.delete(row)

    # Cập nhật từng tab

    def _refresh_results_tab(self):
        """Áp dụng bộ lọc/sắp xếp hiện tại và làm mới tab kết quả."""
        if self.results is None:
            return
        rows = self._apply_result_filters(self.result_rows)
        rows = self._sort_result_rows_for_display(rows)
        self._display_result_rows(rows)

    def _fill_results_tree(self, rows: list):
        """Thay nội dung bảng kết quả bằng ``rows`` theo đúng thứ tự."""
        tree = self.tree_results
        for row in tree.get_children():
            tree.delete(row)

        for pos, r in enumerate(rows, start=1):
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
            ))

    def _refresh_class_tab(self):
        """Làm mới bảng tổng hợp lớp từ dữ liệu đã nạp hoặc đã chấm."""
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
        """Hiển thị sinh viên thuộc lớp học phần đang chọn."""
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
        """Làm mới thống kê câu hỏi và danh sách câu khó của kỳ thi chọn."""
        tree = self.tree_question
        for row in tree.get_children():
            tree.delete(row)

        if self.question_stats is None or self.answer_key is None:
            self.hardest_text.configure(state=tk.NORMAL)
            self.hardest_text.delete("1.0", tk.END)
            self.hardest_text.insert(tk.END, "Chưa có dữ liệu câu hỏi.")
            self.hardest_text.configure(state=tk.DISABLED)
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

            tree.insert("", tk.END, values=(
                data["exam_id"], f"Câu {data['question_id']}", correct, wrong, f"{rate}%"
            ))

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

# Chạy chương trình

if __name__ == "__main__":
    app = App()
    app.mainloop()
