import customtkinter as ctk
from tkinter import ttk, messagebox, simpledialog, filedialog
import csv
from sys_logics import GradingSystem, Exam, StudentSubmission
import data_manager
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

class QuizAppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Hệ thống Chấm điểm Trắc nghiệm Tự động")
        self.geometry("1100x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Khởi tạo Backend
        self.system = GradingSystem()
        
        # Nạp Dữ liệu
        data_manager.load_exams(self.system.exams_db)
        data_manager.load_submissions(self.system.submissions_db)
        
        # Thiết lập Giao diện
        self.tab_view = ctk.CTkTabview(self, width=1060, height=660)
        self.tab_view.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.dashboard_tab = self.tab_view.add("Thống kê & Phân tích")
        self.exams_tab = self.tab_view.add("Quản lý Đề thi")
        self.submissions_tab = self.tab_view.add("Bài làm Sinh viên")
        self.grading_tab = self.tab_view.add("Chấm điểm & Xuất")
        
        self._setup_dashboard_tab()
        self._setup_exams_tab()
        self._setup_submissions_tab()
        self._setup_grading_tab()
        
        # Cập nhật ban đầu
        self._refresh_exams_list()
        self._refresh_submissions_list()
        self._refresh_dashboard()

    def _show_msg(self, msg, level="INFO"):
        if level == "INFO":
            messagebox.showinfo("Thông báo", msg)
        elif level == "ERROR":
            messagebox.showerror("Lỗi", msg)
        elif level == "WARNING":
            messagebox.showwarning("Cảnh báo", msg)

    # --- TAB THỐNG KÊ ---
    def _setup_dashboard_tab(self):
        top_frame = ctk.CTkFrame(self.dashboard_tab, fg_color="transparent")
        top_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(top_frame, text="Chọn Lớp:").pack(side="left", padx=10)
        self.cbo_dashboard_class = ctk.CTkComboBox(top_frame, values=["Tất cả"], command=lambda _: self._refresh_dashboard())
        self.cbo_dashboard_class.pack(side="left", padx=5)

        self.lbl_total_students = ctk.CTkLabel(self.dashboard_tab, text="Tổng Sinh Viên: 0", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_total_students.pack(pady=5)
        
        self.lbl_avg_score = ctk.CTkLabel(self.dashboard_tab, text="Điểm Trung Bình: 0.0", font=ctk.CTkFont(size=18, weight="bold"), text_color="green")
        self.lbl_avg_score.pack(pady=5)
        
        self.charts_frame = ctk.CTkFrame(self.dashboard_tab)
        self.charts_frame.pack(pady=10, padx=20, fill="both", expand=True)
        self.canvas_widget = None

    def _refresh_dashboard(self):
        filter_class = getattr(self, 'cbo_dashboard_class', None)
        selected_class = filter_class.get() if filter_class else "Tất cả"
        
        count_sub = sum(1 for _, sub in self.system.submissions_db.items() if selected_class == "Tất cả" or sub.student_class == selected_class)
        self.lbl_total_students.configure(text=f"Tổng Sinh Viên: {count_sub}")
        
        stats = self.system.generate_statistics(filter_class=selected_class)
        if stats:
            self.lbl_avg_score.configure(text=f"Điểm Trung Bình: {stats['avg']:.2f}")
            
            if hasattr(self, 'canvas_widget') and self.canvas_widget:
                self.canvas_widget.destroy()
                
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            
            exact_freqs = stats.get('exact_frequencies', {})
            if exact_freqs:
                scores = sorted(list(exact_freqs.keys()))
                counts = [exact_freqs[s] for s in scores]
                ax1.bar([str(s) for s in scores], counts, color='royalblue')
                ax1.set_title("Phân bố Điểm số")
                ax1.set_xlabel("Điểm")
                ax1.set_ylabel("Số lượng SV")
                for i, v in enumerate(counts):
                    ax1.text(i, v + 0.1, str(v), ha='center', va='bottom')
            else:
                ax1.text(0.5, 0.5, 'Chưa có dữ liệu', ha='center', va='center')
                ax1.set_title("Phân bố Điểm số")

            hard_qs = self.system.identify_hard_questions(top_n=5, filter_class=selected_class)
            if hard_qs:
                q_names = [f"Câu {q+1}" for q, _ in hard_qs]
                err_counts = [count for _, count in hard_qs]
                ax2.bar(q_names, err_counts, color='salmon')
                ax2.set_title("Top 5 Câu Hỏi Khó Nhất")
                ax2.set_ylabel("Số SV trả lời sai")
                for i, v in enumerate(err_counts):
                    ax2.text(i, v + 0.1, str(v), ha='center', va='bottom')
            else:
                ax2.text(0.5, 0.5, 'Chưa có dữ liệu', ha='center', va='center')
                ax2.set_title("Top Câu Hỏi Khó Nhất")

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
            self.canvas_widget = canvas.get_tk_widget()
            self.canvas_widget.pack(fill="both", expand=True)
            canvas.draw()
            
        else:
            self.lbl_avg_score.configure(text="Điểm Trung Bình: N/A (Chưa chấm điểm)")
            if hasattr(self, 'canvas_widget') and self.canvas_widget:
                self.canvas_widget.destroy()

    # --- TAB QUẢN LÝ ĐỀ THI ---
    def _setup_exams_tab(self):
        form_frame = ctk.CTkFrame(self.exams_tab)
        form_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(form_frame, text="Mã Đề:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_exam_code = ctk.CTkEntry(form_frame, width=120)
        self.ent_exam_code.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Số Câu Hỏi:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_num_qs = ctk.CTkEntry(form_frame, width=120)
        self.ent_num_qs.grid(row=0, column=3, padx=5, pady=5)
        
        btn_frame = ctk.CTkFrame(self.exams_tab)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(btn_frame, text="Thêm Bộ Đề", command=self._add_exam).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Nạp Đề thi (CSV)", command=self._import_exams_csv, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Xóa Bộ Đề", fg_color="red", command=self._delete_exam).pack(side="left", padx=5)
        
        tree_frame = ctk.CTkFrame(self.exams_tab)
        tree_frame.pack(expand=True, fill="both", padx=10, pady=10)
        cols = ("MaDe", "SoCauHoi", "TrangThai")
        self.exams_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)
        for col in cols:
            self.exams_tree.heading(col, text=col)
            self.exams_tree.column(col, anchor="center")
        self.exams_tree.pack(expand=True, fill="both")

    def _refresh_exams_list(self):
        for row in self.exams_tree.get_children():
            self.exams_tree.delete(row)
            
        for exam_code, exam in self.system.exams_db.items():
            status = "Đã Xóa" if exam.is_deleted else "Hoạt Động"
            self.exams_tree.insert("", "end", values=(exam.exam_code, exam.num_questions, status))

    def _add_exam(self):
        code = self.ent_exam_code.get().strip()
        num_qs_str = self.ent_num_qs.get().strip()
        if not code or not num_qs_str.isdigit():
            self._show_msg("Vui lòng nhập Mã Đề và Số câu hỏi hợp lệ.", "ERROR")
            return
            
        num_qs = int(num_qs_str)
        if num_qs <= 0 or num_qs > 100:
            self._show_msg("Số câu hỏi phải từ 1 đến 100.", "ERROR")
            return
            
        self._open_manual_exam_input(code, num_qs)

    def _open_manual_exam_input(self, code, num_qs):
        popup = ctk.CTkToplevel(self)
        popup.title(f"Nhập Đáp Án - Đề {code}")
        popup.geometry("400x500")
        popup.grab_set()
        
        ctk.CTkLabel(popup, text=f"Nhập đáp án cho {num_qs} câu hỏi\n(Ví dụ: A, B hoặc A,B nếu nhiều đáp án)", font=("Arial", 14, "bold")).pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(popup)
        scroll_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        entry_dict = {}
        for i in range(num_qs):
            row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            ctk.CTkLabel(row_frame, text=f"Câu {i+1}:", width=50).pack(side="left", padx=5)
            ent = ctk.CTkEntry(row_frame, width=150)
            ent.pack(side="left", padx=5)
            entry_dict[i] = ent
            
        def save_exam():
            exam = Exam(code, num_qs)
            for i in range(num_qs):
                ans_str = entry_dict[i].get().strip().upper()
                if ans_str:
                    ans_list = [a.strip() for a in ans_str.replace(" ", ",").split(",") if a.strip()]
                    exam.add_answer(i, ans_list)
                    
            self.system.add_exam(exam)
            import data_manager
            data_manager.save_exams(self.system.exams_db)
            
            self.ent_exam_code.delete(0, "end")
            self.ent_num_qs.delete(0, "end")
            self._refresh_exams_list()
            self._show_msg(f"Thêm thành công đề {code}.")
            popup.destroy()
            
        ctk.CTkButton(popup, text="Lưu Đề Thi", command=save_exam, fg_color="green").pack(pady=10)

    def _delete_exam(self):
        code = self.ent_exam_code.get().strip()
        if not code:
            selected = self.exams_tree.selection()
            if selected:
                code = self.exams_tree.item(selected[0], "values")[0]
                
        if code and messagebox.askyesno("Xác nhận", f"Xóa đề thi {code}?"):
            self.system.delete_exam(code, soft_delete=False)
            data_manager.save_exams(self.system.exams_db)
            self._refresh_exams_list()
            self._show_msg("Xóa thành công.")

    def _import_exams_csv(self):
        filepath = filedialog.askopenfilename(title="Chọn file Đề Thi (CSV)", filetypes=[("CSV Files", "*.csv")])
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    # Định dạng: exam_code, num_questions, ans1, ans2, ...
                    if len(row) < 2: continue
                    code = row[0].strip()
                    num_qs_str = row[1].strip()
                    if not num_qs_str.isdigit(): continue
                    num_qs = int(num_qs_str)
                    
                    exam = Exam(code, num_qs)
                    for i in range(num_qs):
                        if 2 + i < len(row):
                            ans = row[2 + i].strip()
                            exam.add_answer(i, [ans] if ans else [])
                    self.system.add_exam(exam)
                    count += 1
            data_manager.save_exams(self.system.exams_db)
            self._refresh_exams_list()
            self._show_msg(f"Đã nạp thành công {count} bộ đề thi từ CSV.")
        except Exception as e:
            self._show_msg(f"Lỗi khi đọc file CSV: {e}", "ERROR")

    # --- TAB BÀI LÀM SINH VIÊN ---
    def _setup_submissions_tab(self):
        # Khung Tìm kiếm
        search_frame = ctk.CTkFrame(self.submissions_tab)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(search_frame, text="Tìm kiếm:").grid(row=0, column=0, padx=5, pady=5)
        self.cbo_search_by = ctk.CTkComboBox(search_frame, values=["Họ Tên", "MSSV", "Lớp", "Mã Đề"], width=100)
        self.cbo_search_by.grid(row=0, column=1, padx=5, pady=5)
        self.cbo_search_by.set("Họ Tên")
        
        self.ent_search_query = ctk.CTkEntry(search_frame, width=200, placeholder_text="Nhập từ khóa...")
        self.ent_search_query.grid(row=0, column=2, padx=5, pady=5)
        
        ctk.CTkButton(search_frame, text="Tìm kiếm", command=self._search_submissions).grid(row=0, column=3, padx=5, pady=5)
        ctk.CTkButton(search_frame, text="Xóa", command=self._clear_search, fg_color="gray", width=60).grid(row=0, column=4, padx=5, pady=5)
        
        ctk.CTkFrame(self.submissions_tab, height=2, fg_color="gray50").pack(fill="x", padx=10, pady=5)

        form_frame = ctk.CTkFrame(self.submissions_tab)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(form_frame, text="MSSV:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_sub_id = ctk.CTkEntry(form_frame, width=100)
        self.ent_sub_id.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Tên:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_sub_name = ctk.CTkEntry(form_frame, width=150)
        self.ent_sub_name.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Lớp:").grid(row=0, column=4, padx=5, pady=5)
        self.ent_sub_class = ctk.CTkEntry(form_frame, width=100)
        self.ent_sub_class.grid(row=0, column=5, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Mã Đề:").grid(row=0, column=6, padx=5, pady=5)
        self.ent_sub_exam = ctk.CTkEntry(form_frame, width=100)
        self.ent_sub_exam.grid(row=0, column=7, padx=5, pady=5)
        
        btn_frame = ctk.CTkFrame(self.submissions_tab)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(btn_frame, text="Thêm Bài Làm Thủ Công", command=self._add_submission).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Nạp Bài Làm (CSV)", command=self._import_submissions_csv, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Xóa SV Đã Chọn", command=self._delete_student).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Xóa Toàn Bộ", command=self._delete_all_students, fg_color="red").pack(side="right", padx=5)
        
        tree_frame = ctk.CTkFrame(self.submissions_tab)
        tree_frame.pack(expand=True, fill="both", padx=10, pady=10)
        cols = ("MSSV", "HoTen", "Lop", "MaDe", "DiemSo")
        self.subs_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)
        for col in cols:
            self.subs_tree.heading(col, text=col)
            self.subs_tree.column(col, anchor="center")
        self.subs_tree.pack(expand=True, fill="both")
        self.subs_tree.bind("<Double-1>", self._show_student_details)

    def _delete_student(self):
        selected = self.subs_tree.selection()
        if not selected:
            self._show_msg("Vui lòng chọn một sinh viên để xóa.", "WARNING")
            return
        mssv = self.subs_tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Xác nhận", f"Xóa bài làm của sinh viên {mssv}?"):
            self.system.delete_submission(mssv)
            data_manager.save_submissions(self.system.submissions_db)
            self._refresh_submissions_list()
            self._show_msg("Đã xóa sinh viên.")

    def _delete_all_students(self):
        if messagebox.askyesno("Cảnh báo nguy hiểm", "Bạn có chắc chắn muốn xóa TOÀN BỘ bài làm của sinh viên không? Hành động này không thể hoàn tác."):
            self.system.clear_all_submissions()
            data_manager.save_submissions(self.system.submissions_db)
            self._refresh_submissions_list()
            self._show_msg("Đã xóa toàn bộ sinh viên.")

    def _show_student_details(self, event):
        selected = self.subs_tree.selection()
        if not selected: return
        mssv = self.subs_tree.item(selected[0], "values")[0]
        sub = self.system.get_submission(mssv)
        if not sub: return
        
        detail_win = ctk.CTkToplevel(self)
        detail_win.title(f"Chi tiết bài làm - {sub.name} ({mssv})")
        detail_win.geometry("500x400")
        detail_win.grab_set()
        
        ctk.CTkLabel(detail_win, text=f"Bài Làm của {sub.name}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        ctk.CTkLabel(detail_win, text=f"Mã Đề: {sub.exam_code} | Lớp: {sub.student_class} | Điểm: {sub.score:.2f}").pack(pady=5)
        
        scroll_frame = ctk.CTkScrollableFrame(detail_win)
        scroll_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        exam = self.system.get_exam(sub.exam_code)
        
        for i in range(len(sub.answers)):
            student_ans = list(sub.answers.get(i))
            student_str = ",".join(student_ans) if student_ans else "Chưa làm"
            
            correct_str = ""
            color = "white"
            if exam:
                correct_ans = list(exam.get_answer(i))
                correct_str = f" | Đáp án đúng: {','.join(correct_ans)}"
                if set(student_ans) == set(correct_ans) and len(correct_ans) > 0:
                    color = "lightgreen"
                else:
                    color = "salmon"
            
            lbl = ctk.CTkLabel(scroll_frame, text=f"Câu {i+1}: {student_str}{correct_str}", text_color=color)
            lbl.pack(anchor="w", pady=2)

    def _search_submissions(self):
        query = self.ent_search_query.get().strip().lower()
        search_by = self.cbo_search_by.get()
        self._refresh_submissions_list(search_by, query)

    def _clear_search(self):
        self.ent_search_query.delete(0, "end")
        self._refresh_submissions_list()

    def _refresh_submissions_list(self, search_by=None, query=""):
        for row in self.subs_tree.get_children():
            self.subs_tree.delete(row)
            
        classes = set()
        for sub_id, sub in self.system.submissions_db.items():
            classes.add(sub.student_class)
            if query:
                if search_by == "Họ Tên" and query not in sub.name.lower(): continue
                elif search_by == "MSSV" and query not in sub.student_id.lower(): continue
                elif search_by == "Lớp" and query not in sub.student_class.lower(): continue
                elif search_by == "Mã Đề" and query not in sub.exam_code.lower(): continue
                
            score_str = f"{sub.score:.2f}" if sub.score > 0 else "Chưa chấm"
            self.subs_tree.insert("", "end", values=(sub.student_id, sub.name, sub.student_class, sub.exam_code, score_str))
            
        class_list = ["Tất cả"] + sorted(list(classes))
        if hasattr(self, 'cbo_dashboard_class'):
            self.cbo_dashboard_class.configure(values=class_list)
        if hasattr(self, 'cbo_grading_class'):
            self.cbo_grading_class.configure(values=class_list)
            
        self._refresh_dashboard()

    def _add_submission(self):
        sid = self.ent_sub_id.get().strip()
        name = self.ent_sub_name.get().strip()
        sclass = self.ent_sub_class.get().strip()
        exam_code = self.ent_sub_exam.get().strip()
        
        if not sid or not name or not sclass or not exam_code:
            self._show_msg("Vui lòng điền đầy đủ thông tin sinh viên.", "ERROR")
            return
            
        exam = self.system.get_exam(exam_code)
        if not exam:
            self._show_msg(f"Mã đề {exam_code} không tồn tại!", "ERROR")
            return
            
        self._open_manual_submission_input(sid, name, sclass, exam_code, exam.num_questions)

    def _open_manual_submission_input(self, sid, name, sclass, exam_code, num_qs):
        popup = ctk.CTkToplevel(self)
        popup.title(f"Nhập Bài Làm - {name} ({sid})")
        popup.geometry("400x500")
        popup.grab_set()
        
        ctk.CTkLabel(popup, text=f"Nhập bài làm của {name}\nMã đề: {exam_code} ({num_qs} câu)", font=("Arial", 14, "bold")).pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(popup)
        scroll_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        entry_dict = {}
        for i in range(num_qs):
            row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            ctk.CTkLabel(row_frame, text=f"Câu {i+1}:", width=50).pack(side="left", padx=5)
            ent = ctk.CTkEntry(row_frame, width=150)
            ent.pack(side="left", padx=5)
            entry_dict[i] = ent
            
        def save_submission():
            sub = StudentSubmission(sid, name, sclass, exam_code, num_qs)
            for i in range(num_qs):
                ans_str = entry_dict[i].get().strip().upper()
                if ans_str:
                    ans_list = [a.strip() for a in ans_str.replace(" ", ",").split(",") if a.strip()]
                    sub.record_answer(i, ans_list)
                    
            try:
                self.system.load_submission(sub)
                import data_manager
                data_manager.save_submissions(self.system.submissions_db)
                self._refresh_submissions_list()
                
                self.ent_sub_id.delete(0, "end")
                self.ent_sub_name.delete(0, "end")
                self.ent_sub_class.delete(0, "end")
                self.ent_sub_exam.delete(0, "end")
                
                self._show_msg(f"Đã thêm bài làm cho {name}.")
                popup.destroy()
            except Exception as e:
                self._show_msg(str(e), "ERROR")
                
        ctk.CTkButton(popup, text="Lưu Bài Làm", command=save_submission, fg_color="green").pack(pady=10)

    def _import_submissions_csv(self):
        filepath = filedialog.askopenfilename(title="Chọn file Bài Làm (CSV)", filetypes=[("CSV Files", "*.csv")])
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    # Định dạng: student_id, name, class, exam_code, ans1, ans2, ...
                    if len(row) < 4: continue
                    sid = row[0].strip()
                    name = row[1].strip()
                    sclass = row[2].strip()
                    exam_code = row[3].strip()
                    
                    exam = self.system.get_exam(exam_code)
                    if not exam:
                        print(f"Bỏ qua MSSV {sid}: Mã đề {exam_code} không tồn tại.")
                        continue
                        
                    sub = StudentSubmission(sid, name, sclass, exam_code, exam.num_questions)
                    for i in range(exam.num_questions):
                        if 4 + i < len(row):
                            ans = row[4 + i].strip()
                            if ans:
                                sub.record_answer(i, [ans])
                    self.system.load_submission(sub)
                    count += 1
            data_manager.save_submissions(self.system.submissions_db)
            self._refresh_submissions_list()
            self._show_msg(f"Đã nạp thành công {count} bài làm từ CSV.")
        except Exception as e:
            self._show_msg(f"Lỗi khi đọc file CSV: {e}", "ERROR")

    # --- TAB CHẤM ĐIỂM & XUẤT ---
    def _setup_grading_tab(self):
        center_frame = ctk.CTkFrame(self.grading_tab)
        center_frame.pack(expand=True, padx=50, pady=50)
        
        ctk.CTkLabel(center_frame, text="Tiến hành Chấm điểm Tự động", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        filter_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        filter_frame.pack(pady=10)
        ctk.CTkLabel(filter_frame, text="Chọn Lớp:").pack(side="left", padx=10)
        self.cbo_grading_class = ctk.CTkComboBox(filter_frame, values=["Tất cả"])
        self.cbo_grading_class.pack(side="left", padx=5)
        
        ctk.CTkButton(center_frame, text="CHẤM TẤT CẢ BÀI LÀM", command=self._grade_all, height=50, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        ctk.CTkButton(center_frame, text="Xuất Báo Cáo CSV", command=self._export_csv, fg_color="green", height=40).pack(pady=10)

    def _grade_all(self):
        if len(self.system.submissions_db) == 0:
            self._show_msg("Không có bài làm nào để chấm.", "WARNING")
            return
            
        selected_class = self.cbo_grading_class.get()
        self.system.grade_all_submissions(total_score_scale=10.0, filter_class=selected_class)
        data_manager.save_submissions(self.system.submissions_db)
        self._refresh_submissions_list()
        self._show_msg("Chấm điểm hoàn tất! Chuyển sang tab Thống kê để xem kết quả.")

    def _export_csv(self):
        import os
        export_path = os.path.join(os.getcwd(), "bang_diem.csv")
        success = self.system.export_results_to_csv(export_path)
        if success:
            self._show_msg(f"Đã xuất file thành công tại:\n{export_path}")
        else:
            self._show_msg("Có lỗi khi xuất file.", "ERROR")

if __name__ == "__main__":
    app = QuizAppGUI()
    app.mainloop()
