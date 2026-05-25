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
    validate_answer_key_csv,
    validate_students_csv,
    validate_grading_inputs,
    infer_exam_store,
    grade_all,
    compute_question_stats,
    export_results_csv,
    export_question_stats_csv,
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
from models import normalize_question_id
from ui.class_tab import build_class_tab
from ui.question_tab import build_question_tab
from ui.results_tab import build_results_tab
from ui.search_tab import build_search_tab

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
        self.class_summary = []
        self.result_rows = []
        self.display_rows = []
        self.score_index = []
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
        self.tab_class = self.tabview.add("Danh sách lớp HP")
        self.tab_question = self.tabview.add("Thống kê câu hỏi")
        self.tab_search = self.tabview.add("Tìm kiếm thí sinh")

        build_results_tab(self)
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
            validation_errors = (
                validate_answer_key_csv(answer_path)
                + validate_students_csv(student_path)
            )
            if validation_errors:
                messagebox.showerror("Dữ liệu không hợp lệ", "\n".join(validation_errors))
                return

            self.status_var.set("Đang xử lý...")
            self.update()

            # Đọc dữ liệu.
            self.answer_key = load_answer_key(answer_path)
            self.exam_store = load_exam_store(self._resolve_exam_metadata_path())
            self.students = load_students(student_path)
            validation_errors = validate_grading_inputs(self.answer_key, self.students)
            if validation_errors:
                messagebox.showerror("Dữ liệu không hợp lệ", "\n".join(validation_errors))
                self.status_var.set("Dữ liệu không hợp lệ.")
                return
            self.exam_store = infer_exam_store(self.answer_key, self.students, self.exam_store)

            # Chấm điểm.
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

            # Thống kê câu hỏi.
            self.question_stats = compute_question_stats(self.students, self.answer_key)
            self.class_summary = build_class_summary(self.results)

            # Cập nhật giao diện.
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

    def _update_search_suggestions(self, event=None):
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
        self.search_suggestion_box.grid_remove()

    def _select_search_suggestion(self, event=None):
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
        if self.results is None:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng chấm điểm trước.")
            return

        sid = self.var_search.get().strip()
        name_query = self.var_search_name.get().strip()
        if not sid and not name_query:
            return

        if sid:
            matches = search_students_indexed(self.student_search_index, sid, self.var_exam_filter.get())
            query_label = f"MSSV: {sid}"
        else:
            matches = search_students_by_name_prefix(
                self.student_search_index,
                name_query,
                self.var_exam_filter.get(),
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

# --- Điểm chạy chương trình ---

if __name__ == "__main__":
    app = App()
    app.mainloop()
