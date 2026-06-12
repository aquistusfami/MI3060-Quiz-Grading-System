"""Các kiểu dữ liệu miền dùng chung trong hệ thống chấm điểm.

Các lớp trong module chỉ lưu trạng thái và cung cấp thuộc tính dẫn xuất;
chúng không đọc file, ghi file hoặc phụ thuộc vào giao diện.
"""

class Question:
    """Lưu mã câu hỏi và đáp án đúng của một kỳ thi."""

    def __init__(
        self,
        question_id: str,
        correct_answer: str,
        exam_id: str = "EXAM001",
    ):
        """Khởi tạo câu hỏi từ các giá trị đã được lớp nghiệp vụ kiểm tra."""
        self.exam_id = str(exam_id).strip() or "EXAM001"
        self.question_id = question_id
        self.correct_answer = correct_answer

    def __repr__(self):
        return f"Question(id={self.question_id}, answer={self.correct_answer})"


class ExamInfo:
    """Lưu metadata kỳ thi, không chứa đáp án hoặc bài làm sinh viên."""

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
        """Khởi tạo metadata và chuẩn hóa các trường chuỗi tùy chọn."""
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


class Student:
    """Lưu thông tin thí sinh và đáp án theo mã câu hỏi."""

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
        """Khởi tạo thí sinh.

        Args:
            answers: Ánh xạ ``question_id -> answer``, ví dụ
                ``{"1": "A", "2": "C"}``.
            Các tham số còn lại là thông tin định danh và phân lớp.
        """
        self.student_id = str(student_id).strip()
        self.student_name = student_name.strip()
        self.class_id = class_id.strip() or "Chưa có lớp học phần"
        self.admin_class_id = admin_class_id.strip() or "Chưa phân lớp"
        self.class_name = class_name.strip() or self.class_id
        self.exam_id = str(exam_id).strip() or "EXAM001"
        self.answers = answers

    def get_answer(self, question_id: str) -> str:
        """Lấy đáp án của một câu hỏi; trả về rỗng nếu thiếu."""
        return self.answers.get(question_id, "")

    def __repr__(self):
        return f"Student(id={self.student_id}, name={self.student_name})"


class ExamResult:
    """Lưu điểm, số câu đúng và các câu sai của một thí sinh."""

    def __init__(
        self,
        student: Student,
        score: float,
        correct_count: int,
        total_questions: int,
        wrong_questions: list,
    ):
        """Khởi tạo kết quả và làm tròn điểm về hai chữ số thập phân."""
        self.student = student
        self.score = round(score, 2)
        self.correct_count = correct_count
        self.total_questions = total_questions
        self.wrong_questions = wrong_questions

    @property
    def student_id(self) -> str:
        """Trả về MSSV của thí sinh sở hữu kết quả."""
        return self.student.student_id

    @property
    def student_name(self) -> str:
        """Trả về họ tên của thí sinh sở hữu kết quả."""
        return self.student.student_name

    @property
    def class_name(self) -> str:
        """Trả về tên lớp hành chính của thí sinh."""
        return self.student.class_name

    @property
    def class_id(self) -> str:
        """Trả về mã lớp học phần của thí sinh."""
        return self.student.class_id

    @property
    def admin_class_id(self) -> str:
        """Trả về mã lớp hành chính của thí sinh."""
        return self.student.admin_class_id

    @property
    def exam_id(self) -> str:
        """Trả về mã kỳ thi của kết quả."""
        return self.student.exam_id

    @property
    def accuracy_percent(self) -> float:
        """Trả về tỷ lệ đúng, làm tròn đến một chữ số thập phân."""
        if self.total_questions == 0:
            return 0.0
        return round(self.correct_count / self.total_questions * 100, 1)

    def __repr__(self):
        return (
            f"ExamResult(id={self.student_id}, "
            f"score={self.score})"
        )
