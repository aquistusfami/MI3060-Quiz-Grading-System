# models.py
# Các lớp dữ liệu của hệ thống.

def normalize_answer(answer: str) -> str:
    return str(answer).strip().upper()


# --- Question (Câu hỏi trong đề thi) ---

class Question:
    """Đại diện một câu hỏi trong đề thi."""

    def __init__(
        self,
        question_id: str,
        correct_answer: str,
        exam_id: str = "EXAM001",
    ):
        self.exam_id = str(exam_id).strip() or "EXAM001"
        self.question_id = question_id
        self.correct_answer = normalize_answer(correct_answer)

    def __repr__(self):
        return f"Question(id={self.question_id}, answer={self.correct_answer})"


# --- ExamInfo (Thông tin kỳ thi / đề thi) ---

class ExamInfo:
    """Thông tin tổng quan của kỳ thi, không lưu nội dung câu hỏi."""

    def __init__(
        self,
        exam_id: str,
        course_code: str = "",
        course_name: str = "",
        semester: str = "",
        exam_name: str = "",
        exam_date: str = "",
        duration_minutes: str = "",
        note: str = "",
    ):
        self.exam_id = str(exam_id).strip() or "EXAM001"
        self.course_code = course_code.strip()
        self.course_name = course_name.strip()
        self.semester = semester.strip()
        self.exam_name = exam_name.strip() or self.exam_id
        self.exam_date = exam_date.strip()
        self.duration_minutes = str(duration_minutes).strip()
        self.note = note.strip()

    def __repr__(self):
        return f"ExamInfo(id={self.exam_id}, course={self.course_code})"


# --- Student (Thí sinh và bài làm) ---

class Student:
    """Đại diện một thí sinh và bài làm của thí sinh đó."""

    def __init__(
        self,
        student_id: str,
        student_name: str,
        answers: dict,
        class_name: str = "",
        class_id: str = "",
        admin_class_id: str = "",
        exam_id: str = "EXAM001",
    ):
        """
        answers: {question_id (str): answer (str)}
        Ví dụ: {"1": "A", "2": "C", ...}
        """
        self.student_id = str(student_id).strip()
        self.student_name = student_name.strip()
        self.class_id = class_id.strip() or "Chưa có lớp học phần"
        self.admin_class_id = admin_class_id.strip() or "Chưa phân lớp"
        self.class_name = class_name.strip() or self.class_id
        self.exam_id = str(exam_id).strip() or "EXAM001"
        # Chuẩn hóa đáp án để so sánh ổn định.
        self.answers = {k: normalize_answer(v) for k, v in answers.items()}

    def get_answer(self, question_id: str) -> str:
        """Lấy đáp án của một câu hỏi; trả về rỗng nếu thiếu."""
        return self.answers.get(question_id, "")

    def __repr__(self):
        return f"Student(id={self.student_id}, name={self.student_name})"


# --- ExamResult (Kết quả chấm điểm) ---

class ExamResult:
    """Kết quả chấm điểm của một thí sinh."""

    def __init__(
        self,
        student: Student,
        score: float,
        correct_count: int,
        total_questions: int,
        wrong_questions: list,   # Danh sách mã câu sai.
    ):
        self.student = student
        self.score = round(score, 2)          # Điểm thang 10.
        self.correct_count = correct_count
        self.total_questions = total_questions
        self.wrong_questions = wrong_questions

    @property
    def student_id(self) -> str:
        return self.student.student_id

    @property
    def student_name(self) -> str:
        return self.student.student_name

    @property
    def class_name(self) -> str:
        return self.student.class_name

    @property
    def class_id(self) -> str:
        return self.student.class_id

    @property
    def admin_class_id(self) -> str:
        return self.student.admin_class_id

    @property
    def exam_id(self) -> str:
        return self.student.exam_id

    @property
    def accuracy_percent(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return round(self.correct_count / self.total_questions * 100, 1)

    def __repr__(self):
        return (
            f"ExamResult(id={self.student_id}, "
            f"score={self.score})"
        )
