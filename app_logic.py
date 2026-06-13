"""Logic nghiệp vụ cho việc đọc CSV, chấm điểm và tra cứu kết quả.

Module không phụ thuộc giao diện. Dữ liệu được truyền qua tham số và trả về
dưới dạng model hoặc cấu trúc dữ liệu; chỉ các hàm ``load_*`` và ``export_*``
thực hiện đọc/ghi file.
"""

import csv
import math
import os

from custom_structures import HashTable, List, MinHeap, PrefixTrie, merge_sort
from models import (
    Question,
    ExamInfo,
    Student,
    ExamResult,
)

# Giá trị mặc định và nhãn sắp xếp là cấu hình dùng chung giữa logic và GUI.
DEFAULT_EXAM_ID = "EXAM001"

SORT_CSV_ORDER = "Mặc định theo CSV"
SORT_SCORE_DESC = "Điểm cao đến thấp"
SORT_SCORE_ASC = "Điểm thấp đến cao"

SORT_OPTIONS = (
    SORT_CSV_ORDER,
    SORT_SCORE_DESC,
    SORT_SCORE_ASC,
)

ANSWER_KEY_REQUIRED_COLUMNS = ("question_id", "correct_answer")
STUDENT_ID_COLUMNS = ("mssv", "student_id", "student_code")
STUDENT_NAME_COLUMNS = ("ho_ten", "student_name", "name", "full_name")


class StudentSearchIndex:
    """Gom các bảng băm và Trie phục vụ tra cứu kết quả sinh viên."""

    def __init__(self):
        """Khởi tạo các chỉ mục rỗng; không đọc hoặc thay đổi dữ liệu ngoài."""
        self.by_student_id = HashTable()
        self.student_id_trie = PrefixTrie()
        self.name_trie = PrefixTrie()
        self.all_rows = List()


class AnswerKeyBook:
    """Quản lý đáp án nhiều kỳ thi bằng bảng băm hai cấp."""

    def __init__(self):
        """Khởi tạo kho đáp án rỗng và bộ đếm câu hỏi bằng 0."""
        self.exam_keys = HashTable()
        self.size = 0

    def put(self, exam_id: str, question: Question) -> None:
        """Thêm/cập nhật câu hỏi và duy trì tổng số câu không trùng."""
        exam_id = _normalize_exam_id(exam_id)
        exam_key = self.exam_keys.get(exam_id)
        if exam_key is None:
            exam_key = HashTable()
            self.exam_keys.put(exam_id, exam_key)

        if exam_key.get(question.question_id) is None:
            self.size += 1
        exam_key.put(question.question_id, question)

    def get_exam_key(self, exam_id: str) -> HashTable | None:
        """Trả về bảng đáp án của kỳ thi, hoặc ``None`` nếu chưa có."""
        return self.exam_keys.get(_normalize_exam_id(exam_id))

    def exam_ids(self) -> List:
        """Trả về danh sách mã kỳ thi tăng dần."""
        return merge_sort(self.exam_keys.keys(), key=lambda exam_id: exam_id)

    def question_ids(self, exam_id: str) -> List:
        """Trả về mã câu hỏi của kỳ thi, hoặc danh sách rỗng nếu không có."""
        exam_key = self.get_exam_key(exam_id)
        return exam_key.keys() if exam_key is not None else List()

    def remove_question(self, exam_id: str, question_id: str) -> bool:
        """Xóa một câu hỏi và trả về việc câu hỏi có tồn tại hay không."""
        exam_id = _normalize_exam_id(exam_id)
        exam_key = self.get_exam_key(exam_id)
        if exam_key is None:
            return False

        removed = exam_key.remove(question_id)
        if removed:
            self.size -= 1
            if len(exam_key) == 0:
                self.exam_keys.remove(exam_id)
        return removed

    def remove_exam(self, exam_id: str) -> int:
        """Xóa toàn bộ kỳ thi và trả về số câu hỏi đã xóa."""
        exam_id = _normalize_exam_id(exam_id)
        exam_key = self.get_exam_key(exam_id)
        if exam_key is None:
            return 0

        removed_count = len(exam_key)
        if self.exam_keys.remove(exam_id):
            self.size -= removed_count
            return removed_count
        return 0

    def max_question_count(self) -> int:
        """Trả về số câu lớn nhất trong một kỳ thi, hoặc 0 khi kho rỗng."""
        max_count = 0
        for exam_key in self.exam_keys.values():
            if len(exam_key) > max_count:
                max_count = len(exam_key)
        return max_count

    def __len__(self):
        return self.size


class ExamStore:
    """Kho metadata kỳ thi, tra cứu trung bình O(1) theo ``exam_id``."""

    def __init__(self):
        """Khởi tạo kho metadata rỗng."""
        self.exams = HashTable()

    def put(self, exam: ExamInfo) -> None:
        """Thêm hoặc thay thế metadata theo ``exam.exam_id``."""
        self.exams.put(exam.exam_id, exam)

    def get(self, exam_id: str) -> ExamInfo | None:
        """Trả về metadata kỳ thi, hoặc ``None`` nếu chưa có."""
        return self.exams.get(_normalize_exam_id(exam_id))

    def ensure(self, exam_id: str) -> ExamInfo:
        """Trả về metadata hiện có hoặc tạo bản tối thiểu khi còn thiếu."""
        exam_id = _normalize_exam_id(exam_id)
        exam = self.get(exam_id)
        if exam is None:
            exam = ExamInfo(exam_id=exam_id)
            self.put(exam)
        return exam

    def __len__(self):
        return len(self.exams)


def _normalize_exam_id(exam_id: str) -> str:
    """Chuẩn hóa mã kỳ thi và thay chuỗi rỗng bằng mã mặc định."""
    return str(exam_id).strip() or DEFAULT_EXAM_ID


def _row_from_csv(headers, values) -> HashTable:
    """Chuyển một dòng ``csv.reader`` thành bảng băm tự cài đặt."""
    row = HashTable()
    for index, header in enumerate(headers):
        value = values[index] if index < len(values) else ""
        row.put(header, value)
    return row


def _header_table(headers) -> HashTable:
    """Tạo tập tên cột bằng ``HashTable`` để kiểm tra tồn tại trung bình O(1)."""
    table = HashTable()
    for header in headers:
        table.put(header, True)
    return table


def _record(*pairs) -> HashTable:
    """Tạo bản ghi nghiệp vụ từ các cặp ``(key, value)``."""
    record = HashTable()
    for key, value in pairs:
        record.put(key, value)
    return record


def _list_of(*items) -> List:
    """Tạo ``List`` tự cài đặt từ các phần tử truyền vào."""
    result = List()
    result.extend(items)
    return result


def _get_exam_id(row: HashTable) -> str:
    """Suy ra mã kỳ thi từ các tên cột CSV được hỗ trợ."""
    for col in ("exam_id", "exam", "ma_de", "MaDe", "de_thi"):
        if col in row and row[col].strip():
            return row[col].strip()
    course_code = _get_first_value(row, ("ma_hp", "course_code", "hoc_phan"))
    semester = _get_first_value(row, ("hoc_ky", "semester"))
    section_id = _get_first_value(row, ("id_lop_hp", "class_id", "ma_lop_hp"))
    if course_code or semester or section_id:
        return "-".join(part for part in (course_code, semester, section_id) if part)
    return DEFAULT_EXAM_ID


def load_exam_store(filepath: str | None = None) -> ExamStore:
    """Đọc metadata kỳ thi từ CSV.

    ``filepath`` có thể rỗng hoặc không tồn tại; khi đó hàm trả về kho rỗng.
    """
    store = ExamStore()
    if not filepath or not os.path.exists(filepath):
        return store

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader, ())
        for values in reader:
            row = _row_from_csv(headers, values)
            exam = ExamInfo(
                exam_id=_get_exam_id(row),
                course_code=_get_first_value(row, ("ma_hp", "course_code")),
                course_name=_get_first_value(row, ("ten_hp", "course_name")),
                semester=_get_first_value(row, ("hoc_ky", "semester")),
                exam_name=_get_first_value(row, ("ten_ky_thi", "exam_name")),
                exam_date=_get_first_value(row, ("ngay_thi", "exam_date")),
                duration_minutes=_get_first_value(row, ("thoi_luong_phut", "duration_minutes")),
                note=_get_first_value(row, ("ghi_chu", "note")),
            )
            store.put(exam)

    return store


# Đọc dữ liệu CSV

def load_answer_key(filepath: str) -> AnswerKeyBook:
    """
    Đọc file đáp án.
    Trả về AnswerKeyBook: {exam_id -> {question_id -> Question}}.
    """
    answer_key = AnswerKeyBook()

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader, ())
        for values in reader:
            row = _row_from_csv(headers, values)
            exam_id = _get_exam_id(row)
            q = Question(
                question_id=row["question_id"].strip(),
                correct_answer=row["correct_answer"],
                exam_id=exam_id,
            )
            answer_key.put(exam_id, q)

    return answer_key


def validate_answer_key_csv(filepath: str) -> List:
    """Trả về danh sách lỗi cấu trúc/dữ liệu của file đáp án."""
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader, ())
        fieldnames = _header_table(headers)
        missing = List()
        for column in ANSWER_KEY_REQUIRED_COLUMNS:
            if column not in fieldnames:
                missing.append(column)
        if missing:
            errors = List()
            errors.append(f"File đáp án thiếu cột bắt buộc: {', '.join(missing)}.")
            return errors

        errors = List()
        seen_questions = HashTable()
        for line_number, values in enumerate(reader, start=2):
            row = _row_from_csv(headers, values)
            exam_id = _get_exam_id(row)
            question_id = row["question_id"].strip()
            correct_answer = row["correct_answer"]

            if (
                not question_id.isdigit()
                or int(question_id) < 1
                or question_id != str(int(question_id))
            ):
                errors.append(
                    f"Dòng {line_number}: question_id phải có dạng 1, 2, 3, ..."
                )
            if not correct_answer.strip():
                errors.append(f"Dòng {line_number}: correct_answer không được để trống.")

            question_key = f"{exam_id}|{question_id}"
            if seen_questions.contains(question_key):
                errors.append(
                    f"Dòng {line_number}: trùng câu {question_id} của kỳ thi {exam_id}."
                )
            else:
                seen_questions.put(question_key, True)

        return errors


def load_students(filepath: str, num_questions: int | None = None) -> List:
    """
    Đọc file bài làm thí sinh.
    Trả về List chứa các đối tượng Student.
    """
    students = List()

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader, ())
        question_columns = List()
        for col in headers:
            if col.lower().startswith("q") and col[1:].isdigit():
                question_columns.append(col)
        for values in reader:
            row = _row_from_csv(headers, values)
            # Tên cột q1, q2, ... trở thành mã câu 1, 2, ...
            answers = HashTable()
            columns = question_columns
            if num_questions is not None:
                columns = List()
                for i in range(1, num_questions + 1):
                    columns.append(f"q{i}")

            for col in columns:
                if col in row:
                    answers.put(col[1:], row[col])

            student = Student(
                student_id=_get_student_id(row),
                student_name=_get_student_name(row),
                answers=answers,
                class_name=_get_class_name(row),
                class_id=_get_class_id(row),
                admin_class_id=_get_admin_class_id(row),
                exam_id=_get_exam_id(row),
            )
            students.append(student)

    return students


def validate_students_csv(filepath: str) -> List:
    """Trả về danh sách lỗi của file sinh viên, gồm cả file rỗng."""
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader, ())
        fieldnames = _header_table(headers)
        errors = List()
        has_student_id = _has_any_column(fieldnames, STUDENT_ID_COLUMNS)
        has_student_name = _has_any_column(fieldnames, STUDENT_NAME_COLUMNS)

        if not has_student_id:
            errors.append(
                "File thí sinh thiếu cột MSSV. "
                f"Cần một trong các cột: {', '.join(STUDENT_ID_COLUMNS)}."
            )
        if not has_student_name:
            errors.append(
                "File thí sinh thiếu cột họ tên. "
                f"Cần một trong các cột: {', '.join(STUDENT_NAME_COLUMNS)}."
            )
        if not any(col.lower().startswith("q") and col[1:].isdigit() for col in fieldnames):
            errors.append("File thí sinh phải có ít nhất một cột đáp án dạng q1, q2, ...")

        if errors:
            return errors

        row_count = 0
        for line_number, values in enumerate(reader, start=2):
            row = _row_from_csv(headers, values)
            row_count += 1
            if not _get_student_id(row):
                errors.append(f"Dòng {line_number}: MSSV không được để trống.")
            if not _get_student_name(row):
                errors.append(f"Dòng {line_number}: họ tên không được để trống.")

        if row_count == 0:
            errors.append("File thí sinh không có dữ liệu.")

        return errors


def validate_grading_inputs(answer_key: AnswerKeyBook, students: List) -> List:
    """Trả về lỗi liên kết đáp án-sinh viên và MSSV trùng trước khi chấm."""
    errors = List()
    if len(answer_key) == 0:
        errors.append("File đáp án không có câu hỏi nào.")

    seen_students = HashTable()
    missing_exam_ids = HashTable()
    for student in students:
        student_key = _result_key(student.exam_id, student.student_id)
        if seen_students.contains(student_key):
            errors.append(f"Trùng MSSV {student.student_id} trong kỳ thi {student.exam_id}.")
        else:
            seen_students.put(student_key, True)

        if answer_key.get_exam_key(student.exam_id) is None:
            missing_exam_ids.put(student_key, (student.exam_id, student.student_id))

    missing_rows = List()
    for exam_id, student_id in missing_exam_ids.values():
        missing_rows.append((exam_id, student_id))
    for exam_id, student_id in merge_sort(missing_rows, key=lambda item: item):
        errors.append(
            f"Sinh viên {student_id} thuộc kỳ thi {exam_id} nhưng không có đáp án tương ứng."
        )
    return errors


def infer_exam_store(
    answer_key: AnswerKeyBook,
    students: List | None = None,
    existing_store: ExamStore | None = None,
) -> ExamStore:
    """Bổ sung metadata kỳ thi từ đáp án và bài làm."""
    store = existing_store if existing_store is not None else ExamStore()

    for exam_id in answer_key.exam_ids():
        store.ensure(exam_id)

    if students is None:
        return store

    for student in students:
        exam = store.ensure(student.exam_id)
        if not exam.course_code:
            # Suy ra thông tin từ exam_id khi file không có metadata riêng.
            parts = student.exam_id.split("-")
            if len(parts) >= 1:
                exam.course_code = parts[0] if parts[0] != DEFAULT_EXAM_ID else exam.course_code
            if len(parts) >= 2:
                exam.semester = parts[1]

    return store


def _get_class_name(row: HashTable) -> str:
    """Đọc tên lớp từ các tên cột phổ biến."""
    return _get_first_value(row, ("ten_lop", "class_name", "class", "lop", "Lop", "Class"))


def _get_class_id(row: HashTable) -> str:
    """Đọc mã lớp học phần HUST, ví dụ 163613."""
    return _get_first_value(row, ("id_lop_hp", "class_id", "ma_lop_hp"))


def _get_admin_class_id(row: HashTable) -> str:
    """Đọc mã lớp hành chính của sinh viên, ví dụ 23D1."""
    return _get_first_value(row, ("ma_lop", "admin_class_id"))


def _get_student_id(row: HashTable) -> str:
    """Lấy MSSV từ tên cột đầu tiên được hỗ trợ và có dữ liệu."""
    return _get_first_value(row, ("mssv", "student_id", "student_code"))


def _get_student_name(row: HashTable) -> str:
    """Lấy họ tên từ tên cột đầu tiên được hỗ trợ và có dữ liệu."""
    return _get_first_value(row, ("ho_ten", "student_name", "name", "full_name"))


def _get_first_value(row: HashTable, columns: tuple[str, ...]) -> str:
    """Trả về giá trị không rỗng đầu tiên trong các cột ưu tiên."""
    for col in columns:
        if col in row and row[col].strip():
            return row[col].strip()
    return ""


def _has_any_column(fieldnames: HashTable, columns: tuple[str, ...]) -> bool:
    """Kiểm tra header có ít nhất một tên cột được hỗ trợ."""
    return any(column in fieldnames for column in columns)


# Chấm điểm

def grade_student(
    student: Student,
    answer_key: AnswerKeyBook,
    question_ids: List | None = None,
) -> ExamResult:
    """
    Chấm điểm một thí sinh.
    Dùng bảng băm để tra cứu đáp án theo từng câu.
    """
    correct_count = 0
    wrong_questions = List()
    exam_key = answer_key.get_exam_key(student.exam_id)
    if exam_key is None:
        raise ValueError(f"Không có đáp án cho kỳ thi/đề thi: {student.exam_id}")

    question_ids = question_ids if question_ids is not None else exam_key.keys()
    total = len(question_ids)

    for qid in question_ids:
        question: Question = exam_key.get(qid)
        student_answer = student.get_answer(qid)

        if student_answer == question.correct_answer:
            correct_count += 1
        else:
            wrong_questions.append(qid)

    score = (correct_count / total * 10) if total > 0 else 0.0

    return ExamResult(
        student=student,
        score=score,
        correct_count=correct_count,
        total_questions=total,
        wrong_questions=wrong_questions,
    )


def grade_all(students: List, answer_key: AnswerKeyBook) -> HashTable:
    """
    Chấm điểm toàn bộ thí sinh.
    Trả về HashTable: {exam_id|student_id -> ExamResult}.
    """
    results = HashTable()
    question_id_cache = HashTable()

    for student in students:
        question_ids = question_id_cache.get(student.exam_id)
        if question_ids is None:
            question_ids = answer_key.question_ids(student.exam_id)
            question_id_cache.put(student.exam_id, question_ids)

        result = grade_student(student, answer_key, question_ids)
        key = _result_key(student.exam_id, student.student_id)
        if results.get(key) is not None:
            raise ValueError(
                f"Trùng kết quả chấm cho sinh viên {student.student_id} trong kỳ thi {student.exam_id}."
            )
        results.put(key, result)

    return results


# Thống kê câu hỏi

def compute_question_stats(
    students: List,
    answer_key: AnswerKeyBook,
) -> HashTable:
    """
    Tính số đúng/sai theo từng câu hỏi.
    Trả về HashTable chứa thống kê theo exam_id và question_id.
    """
    stats = HashTable()
    question_id_cache = HashTable()

    # Đếm số thí sinh trả lời đúng từng câu.
    for student in students:
        exam_key = answer_key.get_exam_key(student.exam_id)
        if exam_key is None:
            raise ValueError(f"Không có đáp án cho kỳ thi/đề thi: {student.exam_id}")

        question_ids = question_id_cache.get(student.exam_id)
        if question_ids is None:
            question_ids = exam_key.keys()
            question_id_cache.put(student.exam_id, question_ids)

        for qid in question_ids:
            key = _question_stat_key(student.exam_id, qid)
            entry = stats.get(key)
            if entry is None:
                entry = _record(
                    ("exam_id", student.exam_id),
                    ("question_id", qid),
                    ("correct", 0),
                    ("total", 0),
                )
                stats.put(key, entry)

            question: Question = exam_key.get(qid)
            entry["total"] += 1
            if student.get_answer(qid) == question.correct_answer:
                entry["correct"] += 1

    return stats


def _result_key(exam_id: str, student_id: str) -> str:
    """Tạo khóa kết quả duy nhất trong phạm vi kỳ thi."""
    return f"{_normalize_exam_id(exam_id)}|{str(student_id).strip()}"


def _question_stat_key(exam_id: str, question_id: str) -> str:
    """Tạo khóa thống kê duy nhất trong phạm vi kỳ thi."""
    return f"{_normalize_exam_id(exam_id)}|{question_id}"


def build_result_rows_in_student_order(students: List, results: HashTable) -> List:
    """Tạo danh sách kết quả theo đúng thứ tự thí sinh trong file CSV."""
    rows = List()
    for student in students:
        key = _result_key(student.exam_id, student.student_id)
        result = results.get(key)
        if result is None:
            raise ValueError(
                f"Thiếu kết quả chấm cho sinh viên {student.student_id} trong kỳ thi {student.exam_id}."
            )
        rows.append(result)
    return rows


def sort_results(rows: List, sort_option: str) -> List:
    """Trả về bản sao danh sách kết quả theo tùy chọn sắp xếp đã chọn."""
    if sort_option == SORT_CSV_ORDER:
        return rows.copy()
    if sort_option == SORT_SCORE_DESC:
        return merge_sort(
            rows,
            key=lambda r: (r.score, r.correct_count, r.exam_id, r.student_id),
            reverse=True,
        )
    if sort_option == SORT_SCORE_ASC:
        return merge_sort(
            rows,
            key=lambda r: (r.score, r.correct_count, r.exam_id, r.student_id),
        )

    raise ValueError(f"Tùy chọn sắp xếp kết quả không được hỗ trợ: {sort_option}")


# Xuất CSV

def export_results_csv(results: HashTable, output_path: str) -> None:
    """Xuất kết quả chấm điểm ra CSV."""
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    all_results = get_ranking(results)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(_list_of(
            "Hạng", "Kỳ thi", "MSSV", "Họ tên", "ID lớp HP", "Mã lớp SV", "Tên lớp SV",
            "Điểm", "Số câu đúng", "Tổng số câu",
            "Tỷ lệ (%)",
        ))
        for rank_pos, r in enumerate(all_results, start=1):
            writer.writerow(_list_of(
                rank_pos,
                r.exam_id,
                r.student_id,
                r.student_name,
                r.class_id,
                r.admin_class_id,
                r.class_name,
                r.score,
                r.correct_count,
                r.total_questions,
                r.accuracy_percent,
            ))


def export_question_stats_csv(
    question_stats: HashTable,
    output_path: str,
) -> None:
    """Xuất thống kê câu hỏi ra CSV."""
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    items = get_question_stats_items(question_stats)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(_list_of("Kỳ thi", "Câu hỏi", "Số người đúng", "Số người sai", "Tỷ lệ đúng (%)"))
        for data in items:
            total = data["total"]
            correct = data["correct"]
            wrong = total - correct
            rate = round(correct / total * 100, 1) if total > 0 else 0.0
            writer.writerow(_list_of(data["exam_id"], f"Cau {data['question_id']}", correct, wrong, rate))


def export_answer_key_csv(answer_key: AnswerKeyBook, output_path: str) -> None:
    """Xuất đáp án hiện tại ra CSV."""
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    rows = List()
    for exam_id in answer_key.exam_ids():
        exam_key = answer_key.get_exam_key(exam_id)
        if exam_key is None:
            continue
        for question_id in merge_sort(exam_key.keys(), key=_question_sort_value):
            question = exam_key.get(question_id)
            rows.append((exam_id, question.question_id, question.correct_answer))

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(_list_of("exam_id", "question_id", "correct_answer"))
        writer.writerows(rows)


# Tìm kiếm, lọc và thống kê

def build_student_search_index(results: HashTable) -> StudentSearchIndex:
    """Tạo chỉ mục tra cứu MSSV và họ tên từ bảng kết quả."""
    index = StudentSearchIndex()
    seen_student_ids = HashTable()
    seen_names = HashTable()
    rows = merge_sort(
        results.values(),
        key=lambda r: (r.student_name.lower(), r.exam_id, r.student_id),
    )
    index.all_rows = rows

    for result in rows:
        student_rows = index.by_student_id.get(result.student_id)
        if student_rows is None:
            student_rows = List()
            index.by_student_id.put(result.student_id, student_rows)
        student_rows.append(result)

        if not seen_student_ids.contains(result.student_id):
            seen_student_ids.put(result.student_id, True)
            index.student_id_trie.insert(result.student_id)

        normalized_name = _normalize_search_text(result.student_name)
        if normalized_name and not seen_names.contains(normalized_name):
            seen_names.put(normalized_name, result.student_name)
            index.name_trie.insert(normalized_name, result.student_name)

    return index


def search_students_indexed(
    student_search_index: StudentSearchIndex,
    student_id: str,
    exam_id: str | None = None,
) -> List:
    """Tra cứu kết quả theo MSSV bằng chỉ mục bảng băm."""
    rows = student_search_index.by_student_id.get(str(student_id).strip(), List())
    rows = _filter_results_by_exam(rows, exam_id)
    return merge_sort(rows, key=lambda r: r.exam_id)


def search_students_by_name_prefix(
    student_search_index: StudentSearchIndex,
    prefix: str,
    exam_id: str | None = None,
    limit: int = 20,
) -> List:
    """Tra cứu kết quả theo tiền tố họ tên bằng trie."""
    if limit <= 0:
        return List()

    normalized_prefix = _normalize_search_text(prefix)
    if not normalized_prefix:
        return List()

    names = student_search_index.name_trie.autocomplete(
        normalized_prefix,
        limit=len(student_search_index.all_rows),
    )
    name_set = HashTable()
    for name in names:
        name_set.put(_normalize_search_text(name), True)

    rows = List()
    for result in student_search_index.all_rows:
        if not name_set.contains(_normalize_search_text(result.student_name)):
            continue
        if exam_id and exam_id != "Tất cả" and result.exam_id != exam_id:
            continue
        rows.append(result)
        if len(rows) >= limit:
            break
    return rows


def get_student_name_suggestions(
    student_search_index: StudentSearchIndex | None,
    prefix: str,
    limit: int = 8,
) -> List:
    """Lấy gợi ý họ tên sinh viên theo tiền tố."""
    if student_search_index is None:
        return List()
    return student_search_index.name_trie.autocomplete(_normalize_search_text(prefix), limit)


def _filter_results_by_exam(rows: List, exam_id: str | None) -> List:
    """Trả về bản sao các kết quả thuộc kỳ thi được chọn."""
    if not exam_id or exam_id == "Tất cả":
        return rows.copy()
    filtered = List()
    for result in rows:
        if result.exam_id == exam_id:
            filtered.append(result)
    return filtered


def _normalize_search_text(value: str) -> str:
    """Chuẩn hóa chữ thường và khoảng trắng cho khóa tìm kiếm."""
    return " ".join(str(value).strip().lower().split())


def get_student_id_suggestions(
    student_id_trie: PrefixTrie | None,
    prefix: str,
    limit: int = 8,
) -> List:
    """Lấy danh sách MSSV bắt đầu bằng prefix."""
    if student_id_trie is None:
        return List()
    return student_id_trie.autocomplete(prefix, limit)


def get_ranking(results: HashTable) -> List:
    """Trả về kết quả đã sắp xếp theo điểm giảm dần."""
    return merge_sort(
        results.values(),
        key=lambda r: (r.score, r.correct_count, r.exam_id, r.student_id),
        reverse=True,
    )


def build_score_index(results: HashTable) -> List:
    """Tạo chỉ mục điểm tăng dần để tìm kiếm nhị phân."""
    return merge_sort(
        results.values(),
        key=lambda r: (r.score, r.exam_id, r.student_id),
    )


def parse_score_range(low_value: str, high_value: str) -> tuple[float, float]:
    """Trả về ``(low, high)`` và từ chối giá trị không phải số hữu hạn."""
    try:
        low = float(low_value)
        high = float(high_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Điểm lọc phải là số.") from exc

    if not math.isfinite(low) or not math.isfinite(high):
        raise ValueError("Điểm lọc phải là số hữu hạn.")
    return low, high


def _lower_bound_score(score_index: List, target_score: float) -> int:
    """Trả về vị trí đầu tiên có điểm không nhỏ hơn ``target_score``."""
    lo = 0
    hi = len(score_index)
    while lo < hi:
        mid = (lo + hi) // 2
        if score_index[mid].score < target_score:
            lo = mid + 1
        else:
            hi = mid
    return lo


def get_students_in_score_range(
    score_index: List,
    low: float,
    high: float,
) -> List:
    """Lấy thí sinh có điểm trong khoảng [low, high]."""
    if low > high:
        low, high = high, low

    left = _lower_bound_score(score_index, low)
    right = _lower_bound_score(score_index, high + 0.001)
    result = List()
    for item in reversed(score_index[left:right]):
        result.append(item)
    return result


def get_hardest_questions(question_stats: HashTable, n: int = 5) -> List:
    """Trả về n câu hỏi có tỷ lệ đúng thấp nhất."""
    heap = MinHeap()
    for _, data in question_stats.items():
        total = data["total"]
        correct = data["correct"]
        rate = round(correct / total * 100, 1) if total > 0 else 0.0
        qid = data["question_id"]
        heap.push(
            (rate, data["exam_id"], _question_sort_value(qid)),
            (data["exam_id"], qid, correct, total, rate),
        )

    hardest = List()
    for _ in range(min(n, len(heap))):
        _, item = heap.pop()
        hardest.append(item)
    return hardest


def get_question_stats_items(question_stats: HashTable) -> List:
    """Trả về thống kê câu hỏi đã sắp xếp."""
    return merge_sort(
        question_stats.values(),
        key=lambda data: (data["exam_id"], _question_sort_value(data["question_id"])),
    )


def get_student_answer_items(result: ExamResult, answer_key: AnswerKeyBook) -> List:
    """Trả về từng đáp án sinh viên đã chọn và đáp án đúng."""
    exam_key = answer_key.get_exam_key(result.exam_id)
    if exam_key is None:
        return List()

    items = List()
    question_ids = merge_sort(exam_key.keys(), key=_question_sort_value)
    for qid in question_ids:
        question = exam_key.get(qid)
        selected = result.student.get_answer(qid)
        is_correct = selected == question.correct_answer
        items.append(_record(
            ("question_id", qid),
            ("selected_answer", selected or "-"),
            ("correct_answer", question.correct_answer),
            ("is_correct", is_correct),
        ))
    return items


def _question_sort_value(question_id: str) -> int:
    """Chuyển mã câu hỏi hợp lệ thành khóa sắp xếp số."""
    return int(question_id)


def get_class_names(results: HashTable) -> List:
    """Trả về danh sách id_lop_hp duy nhất."""
    seen = HashTable()
    for result in results.values():
        seen.put(result.class_id, True)
    return merge_sort(seen.keys(), key=lambda name: name)


def get_exam_ids(results: HashTable) -> List:
    """Trả về danh sách exam_id duy nhất trong kết quả."""
    seen = HashTable()
    for result in results.values():
        seen.put(result.exam_id, True)
    return merge_sort(seen.keys(), key=lambda exam_id: exam_id)


def get_results_by_exam(ranking: List, exam_id: str) -> List:
    """Lọc kết quả theo kỳ thi."""
    if not exam_id or exam_id == "Tất cả":
        return ranking.copy()
    filtered = List()
    for result in ranking:
        if result.exam_id == exam_id:
            filtered.append(result)
    return filtered


def get_results_by_class(ranking: List, class_name: str) -> List:
    """Lọc kết quả theo lớp học phần."""
    if not class_name or class_name == "Tất cả":
        return ranking.copy()
    filtered = List()
    for result in ranking:
        if result.class_id == class_name:
            filtered.append(result)
    return filtered


def build_class_summary(results: HashTable) -> List:
    """Thống kê số thí sinh, điểm trung bình và tỷ lệ đạt theo lớp."""
    groups = HashTable()
    for result in results.values():
        key = f"{result.exam_id}|{result.class_id}"
        entry = groups.get(key)
        if entry is None:
            entry = _record(
                ("exam_id", result.exam_id),
                ("class_id", result.class_id),
                ("class_name", result.class_name),
                ("count", 0),
                ("total_score", 0.0),
                ("passing", 0),
            )
            groups.put(key, entry)

        entry["count"] += 1
        entry["total_score"] += result.score
        if result.score >= 5.0:
            entry["passing"] += 1

    summary = List()
    for entry in groups.values():
        count = entry["count"]
        summary.append(_record(
            ("class_name", entry["class_name"]),
            ("class_id", entry["class_id"]),
            ("exam_id", entry["exam_id"]),
            ("count", count),
            ("average", round(entry["total_score"] / count, 2) if count else 0.0),
            ("passing_rate", round(entry["passing"] / count * 100, 1) if count else 0.0),
        ))

    return merge_sort(summary, key=lambda item: (item["exam_id"], item["class_id"]))


def build_class_roster_summary(students: List) -> List:
    """Tạo danh sách lớp học phần từ file thí sinh, chưa cần chấm điểm."""
    groups = HashTable()
    for student in students:
        key = f"{student.exam_id}|{student.class_id}"
        entry = groups.get(key)
        if entry is None:
            entry = _record(
                ("exam_id", student.exam_id),
                ("class_id", student.class_id),
                ("class_name", student.class_name),
                ("count", 0),
                ("average", None),
                ("passing_rate", None),
            )
            groups.put(key, entry)
        entry["count"] += 1

    return merge_sort(
        groups.values(),
        key=lambda item: (item["exam_id"], item["class_id"]),
    )
