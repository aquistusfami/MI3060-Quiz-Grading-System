"""
sys_logics.py
Cung cấp các lớp logic nghiệp vụ chính cho Hệ thống Chấm điểm Trắc nghiệm.
- Quản lý bộ đề và đáp án.
- Quản lý bài làm của sinh viên.
- Chấm điểm tự động và thống kê kết quả.
"""

from custom_structures import Array, HashTable, CounterArray, SequentialFile
import csv

class Exam:
    """Đại diện cho một bộ đề thi và đáp án."""
    def __init__(self, exam_code, num_questions):
        self.exam_code = exam_code
        self.num_questions = num_questions
        # Mảng lưu trữ đáp án. Mỗi phần tử là một Set (hỗ trợ nhiều đáp án đúng)
        self.answers = Array(num_questions)
        for i in range(num_questions):
            self.answers.set(i, set())
        
        self.is_deleted = False  # Phục vụ tính năng xóa mềm (soft delete)

    def add_answer(self, question_index, answer_set):
        """Cập nhật đáp án đúng cho một câu hỏi cụ thể."""
        if 0 <= question_index < self.num_questions:
            self.answers.set(question_index, set(answer_set))
        else:
            raise IndexError(f"Câu hỏi số {question_index} vượt quá giới hạn đề thi.")

    def get_answer(self, question_index):
        """Lấy đáp án đúng của một câu hỏi."""
        if 0 <= question_index < self.num_questions:
            return self.answers.get(question_index)
        return set()


class StudentSubmission:
    """Đại diện cho bài làm trắc nghiệm của một sinh viên."""
    def __init__(self, student_id, name, student_class, exam_code, num_questions):
        # Chuẩn hóa dữ liệu đầu vào (loại bỏ khoảng trắng thừa)
        self.student_id = student_id.strip()
        self.name = name.strip()
        self.student_class = student_class.strip()
        self.exam_code = exam_code.strip()
        
        # Mảng lưu câu trả lời của SV
        self.answers = Array(num_questions)
        for i in range(num_questions):
            self.answers.set(i, set())
            
        self.score = 0.0

    def record_answer(self, question_index, answer_set):
        """Ghi nhận lựa chọn của sinh viên cho một câu hỏi."""
        if 0 <= question_index < len(self.answers):
            self.answers.set(question_index, set(answer_set))


class GradingSystem:
    """Hệ thống quản lý chấm điểm và thống kê tổng thể."""
    def __init__(self, max_questions_per_exam=50):
        # Kho lưu trữ Đề thi (Key: Mã đề -> Value: đối tượng Exam)
        self.exams_db = HashTable()
        
        # Kho lưu trữ Bài làm (Key: MSSV -> Value: đối tượng StudentSubmission)
        self.submissions_db = HashTable()
        
        # Cấu hình & Thống kê
        self.max_questions = max_questions_per_exam
        # Đếm số lượng sinh viên sai trên từng câu hỏi (kích thước = số câu hỏi tối đa)
        self.wrong_answers_counter = CounterArray(max_questions_per_exam)
        # Lưu lại điểm số của toàn bộ danh sách để tính toán phân phối
        self.scores_list = SequentialFile()

    # Quản lý Đề thi và Đáp án

    def add_exam(self, exam):
        """Thêm bộ đề mới vào hệ thống."""
        self.exams_db.put_item(exam.exam_code, exam)

    def update_exam(self, exam_code, new_exam):
        """Cập nhật nội dung bộ đề đã tồn tại."""
        if self.exams_db.contains_key(exam_code):
            self.exams_db.put_item(exam_code, new_exam)
        else:
            raise ValueError(f"Không tìm thấy mã đề {exam_code} để cập nhật.")

    def delete_exam(self, exam_code, soft_delete=True):
        """Xóa bộ đề thi."""
        if soft_delete:
            exam = self.get_exam(exam_code)
            if exam:
                exam.is_deleted = True
        else:
            self.exams_db.delete_item(exam_code)

    def get_exam(self, exam_code):
        """Truy xuất một bộ đề dựa trên mã đề."""
        try:
            exam = self.exams_db.get_item(exam_code)
            # Chỉ trả về nếu đề thi chưa bị xóa mềm
            return exam if not exam.is_deleted else None
        except KeyError:
            return None

    # Quản lý Bài làm Sinh viên
    
    def load_submission(self, submission):
        """Nạp bài làm của sinh viên. Đảm bảo mã đề hợp lệ."""
        # Validate xem mã đề có trong kho không
        if not self.get_exam(submission.exam_code):
            raise ValueError(f"Bài làm của {submission.student_id} sử dụng mã đề không tồn tại: {submission.exam_code}")
        
        self.submissions_db.put_item(submission.student_id, submission)

    def get_submission(self, student_id):
        """Tra cứu chi tiết bài làm theo MSSV."""
        try:
            return self.submissions_db.get_item(student_id)
        except KeyError:
            return None

    def delete_submission(self, student_id):
        """Xóa bài làm của sinh viên."""
        self.submissions_db.delete_item(student_id)

    def clear_all_submissions(self):
        """Xóa toàn bộ bài làm sinh viên."""
        from custom_structures import HashTable
        self.submissions_db = HashTable()

    # Quá trình chấm điểm
    def grade_student(self, student_id, total_score_scale=10.0):
        """Chấm bài cho một cá nhân sinh viên cụ thể."""
        submission = self.get_submission(student_id)
        if not submission:
            raise ValueError(f"Không tìm thấy bài làm của MSSV {student_id}")

        exam = self.get_exam(submission.exam_code)
        if not exam:
            raise ValueError(f"Mã đề {submission.exam_code} của SV này không tồn tại hoặc đã bị xóa.")

        # Tính điểm dựa trên số câu đúng
        correct_count = 0
        score_per_question = total_score_scale / exam.num_questions

        for i in range(exam.num_questions):
            correct_answer = exam.get_answer(i)
            student_answer = submission.answers.get(i)
            
            # So sánh Set câu trả lời
            if len(correct_answer) > 0 and student_answer == correct_answer:
                correct_count += 1

        # Lưu lại kết quả
        submission.score = correct_count * score_per_question
        return submission.score

    def grade_all_submissions(self, total_score_scale=10.0, filter_class=None):
        """Chấm tự động toàn bộ bài làm trong kho dữ liệu."""
        for student_id, submission in self.submissions_db.items():
            if filter_class and filter_class != "Tất cả" and submission.student_class != filter_class:
                continue
            try:
                self.grade_student(student_id, total_score_scale)
            except ValueError as e:
                print(f"[Cảnh báo] Lỗi khi chấm bài {student_id}: {e}")

    # Thống kê và Phân tích

    def generate_statistics(self, filter_class=None):
        """Tính toán các chỉ số thống kê tổng quát và phân phối điểm số."""
        scores = []
        for _, sub in self.submissions_db.items():
            if filter_class and filter_class != "Tất cả" and sub.student_class != filter_class:
                continue
            scores.append(sub.score)

        if not scores:
            return None
        
        # Chỉ số chung
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)

        # Tần suất chính xác cho biểu đồ
        exact_frequencies = {}

        for s in scores:
            # Làm tròn điểm để gom nhóm (vd: 8.0, 8.5)
            score_rounded = round(s, 2)
            exact_frequencies[score_rounded] = exact_frequencies.get(score_rounded, 0) + 1


        return {
            "avg": round(avg_score, 2),
            "max": round(max_score, 2),
            "min": round(min_score, 2),
            "exact_frequencies": exact_frequencies
        }

    def identify_hard_questions(self, top_n=5, filter_class=None):
        """
        Xác định top N câu hỏi có tỷ lệ sai nhiều nhất,
        hỗ trợ giáo viên phân tích mức độ khó của đề thi.
        """
        error_counts = {}
        for _, sub in self.submissions_db.items():
            if filter_class and filter_class != "Tất cả" and sub.student_class != filter_class:
                continue
            
            exam = self.get_exam(sub.exam_code)
            if not exam: continue
            
            for i in range(exam.num_questions):
                correct_answer = exam.get_answer(i)
                student_answer = sub.answers.get(i)
                # Tính là làm sai nếu chưa có đáp án đúng, hoặc sinh viên chọn sai
                if len(correct_answer) == 0 or student_answer != correct_answer:
                    error_counts[i] = error_counts.get(i, 0) + 1
                    
        errors = [(q, count) for q, count in error_counts.items() if count > 0]
        # Sắp xếp giảm dần theo số lượng sinh viên làm sai
        errors.sort(key=lambda x: x[1], reverse=True)
        return errors[:top_n]

    # Lưu trữ và Phục hồi

    def export_results_to_csv(self, filepath="bang_diem.csv"):
        """Xuất danh sách sinh viên cùng điểm số ra file CSV."""
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["MSSV", "Họ và tên", "Lớp", "Mã đề", "Điểm số"])
                
                for student_id, submission in self.submissions_db.items():
                    writer.writerow([
                        submission.student_id,
                        submission.name,
                        submission.student_class,
                        submission.exam_code,
                        round(submission.score, 2)
                    ])
            return True
        except Exception as e:
            print(f"[Lỗi] Không thể ghi file {filepath}: {e}")
            return False