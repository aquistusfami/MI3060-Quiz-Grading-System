# app_logic.py
# Logic nghiệp vụ: đọc CSV, chấm điểm, thống kê.
# Không phụ thuộc vào giao diện.

import csv
import os

from custom_structures import HashTable, List, MinHeap, PrefixTrie, merge_sort
from models import (
    Question,
    ExamInfo,
    Student,
    ExamResult,
    ExamStatistics,
    normalize_answer,
    normalize_question_id,
)

DEFAULT_EXAM_ID = "EXAM001"


class AnswerKeyBook:
    """Tập đáp án cho nhiều kỳ thi, mỗi kỳ thi có một bảng băm câu hỏi."""

    def __init__(self):
        self.exam_keys = HashTable()
        self.size = 0

    def put(self, exam_id: str, question: Question) -> None:
        exam_id = _normalize_exam_id(exam_id)
        question.question_id = normalize_question_id(question.question_id)
        exam_key = self.exam_keys.get(exam_id)
        if exam_key is None:
            exam_key = HashTable()
            self.exam_keys.put(exam_id, exam_key)

        if exam_key.get(question.question_id) is None:
            self.size += 1
        exam_key.put(question.question_id, question)

    def get_exam_key(self, exam_id: str) -> HashTable | None:
        return self.exam_keys.get(_normalize_exam_id(exam_id))

    def exam_ids(self) -> list:
        return merge_sort(self.exam_keys.keys(), key=lambda exam_id: exam_id)

    def question_ids(self, exam_id: str) -> list:
        exam_key = self.get_exam_key(exam_id)
        return exam_key.keys() if exam_key is not None else []

    def question_count(self, exam_id: str) -> int:
        exam_key = self.get_exam_key(exam_id)
        return len(exam_key) if exam_key is not None else 0

    def get_question(self, exam_id: str, question_id: str) -> Question | None:
        exam_key = self.get_exam_key(exam_id)
        if exam_key is None:
            return None
        return exam_key.get(normalize_question_id(question_id))

    def update_answer(self, exam_id: str, question_id: str, answer: str) -> None:
        question = self.get_question(exam_id, question_id)
        if question is None:
            raise ValueError(f"Không tìm thấy câu {question_id} trong kỳ thi {exam_id}.")
        question.correct_answer = normalize_answer(answer)

    def max_question_count(self) -> int:
        max_count = 0
        for exam_key in self.exam_keys.values():
            if len(exam_key) > max_count:
                max_count = len(exam_key)
        return max_count

    def collision_info(self) -> dict:
        return self.exam_keys.collision_info()

    def __len__(self):
        return self.size


class ExamStore:
    """Kho thông tin kỳ thi, tra cứu O(1) theo exam_id."""

    def __init__(self):
        self.exams = HashTable()

    def put(self, exam: ExamInfo) -> None:
        self.exams.put(exam.exam_id, exam)

    def get(self, exam_id: str) -> ExamInfo | None:
        return self.exams.get(_normalize_exam_id(exam_id))

    def ensure(self, exam_id: str) -> ExamInfo:
        exam_id = _normalize_exam_id(exam_id)
        exam = self.get(exam_id)
        if exam is None:
            exam = ExamInfo(exam_id=exam_id)
            self.put(exam)
        return exam

    def values(self) -> list:
        return merge_sort(self.exams.values(), key=lambda exam: exam.exam_id)

    def __len__(self):
        return len(self.exams)


def _normalize_exam_id(exam_id: str) -> str:
    return str(exam_id).strip() or DEFAULT_EXAM_ID


def _get_exam_id(row: dict) -> str:
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
    """Đọc metadata kỳ thi; trả về kho rỗng nếu chưa có file."""
    store = ExamStore()
    if not filepath or not os.path.exists(filepath):
        return store

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
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


# --- Đọc dữ liệu từ CSV ---

def load_answer_key(filepath: str) -> AnswerKeyBook:
    """
    Đọc file đáp án.
    Trả về AnswerKeyBook: {exam_id -> {question_id -> Question}}.
    """
    answer_key = AnswerKeyBook()

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            exam_id = _get_exam_id(row)
            q = Question(
                question_id=row["question_id"].strip(),
                correct_answer=row["correct_answer"].strip(),
                exam_id=exam_id,
            )
            answer_key.put(exam_id, q)

    return answer_key


def load_students(filepath: str, num_questions: int | None = None) -> List:
    """
    Đọc file bài làm thí sinh.
    Trả về List chứa các đối tượng Student.
    """
    students = List()

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        question_columns = [
            col for col in (reader.fieldnames or [])
            if col.lower().startswith("q") and col[1:].isdigit()
        ]
        for row in reader:
            # Lấy đáp án từ các cột q1, q2, ...
            answers = {}
            columns = question_columns
            if num_questions is not None:
                columns = [f"q{i}" for i in range(1, num_questions + 1)]

            for col in columns:
                if col in row:
                    answers[col[1:]] = row[col]

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


def _get_class_name(row: dict) -> str:
    """Đọc tên lớp từ các tên cột phổ biến."""
    return _get_first_value(row, ("ten_lop", "class_name", "class", "lop", "Lop", "Class"))


def _get_class_id(row: dict) -> str:
    """Đọc mã lớp học phần HUST, ví dụ 163613."""
    return _get_first_value(row, ("id_lop_hp", "class_id", "ma_lop_hp"))


def _get_admin_class_id(row: dict) -> str:
    """Đọc mã lớp hành chính của sinh viên, ví dụ 23D1."""
    return _get_first_value(row, ("ma_lop", "admin_class_id"))


def _get_student_id(row: dict) -> str:
    return _get_first_value(row, ("mssv", "student_id", "student_code"))


def _get_student_name(row: dict) -> str:
    return _get_first_value(row, ("ho_ten", "student_name", "name", "full_name"))


def _get_first_value(row: dict, columns: tuple[str, ...]) -> str:
    for col in columns:
        if col in row and row[col].strip():
            return row[col].strip()
    return ""


# --- Chấm điểm bài làm ---

def grade_student(
    student: Student,
    answer_key: AnswerKeyBook,
    question_ids: list | None = None,
) -> ExamResult:
    """
    Chấm điểm một thí sinh.
    Dùng bảng băm để tra cứu đáp án theo từng câu.
    """
    correct_count = 0
    wrong_questions = []
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
        results.put(_result_key(student.exam_id, student.student_id), result)

    return results


# --- Thống kê câu hỏi ---

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
                entry = {
                    "exam_id": student.exam_id,
                    "question_id": qid,
                    "correct": 0,
                    "total": 0,
                }
                stats.put(key, entry)

            question: Question = exam_key.get(qid)
            entry["total"] += 1
            if student.get_answer(qid) == question.correct_answer:
                entry["correct"] += 1

    return stats


def _result_key(exam_id: str, student_id: str) -> str:
    return f"{_normalize_exam_id(exam_id)}|{str(student_id).strip()}"


def _question_stat_key(exam_id: str, question_id: str) -> str:
    return f"{_normalize_exam_id(exam_id)}|{normalize_question_id(question_id)}"


# --- Xuất kết quả ra CSV ---

def export_results_csv(results: HashTable, output_path: str) -> None:
    """Xuất kết quả chấm điểm ra CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    all_results = get_ranking(results)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Hạng", "Kỳ thi", "MSSV", "Họ tên", "ID lớp HP", "Mã lớp SV", "Tên lớp SV",
            "Điểm", "Số câu đúng", "Tổng số câu",
            "Tỷ lệ (%)",
        ])
        for rank_pos, r in enumerate(all_results, start=1):
            writer.writerow([
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
            ])


def export_question_stats_csv(
    question_stats: HashTable,
    output_path: str,
) -> None:
    """Xuất thống kê câu hỏi ra CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    items = get_question_stats_items(question_stats)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Kỳ thi", "Câu hỏi", "Số người đúng", "Số người sai", "Tỷ lệ đúng (%)"])
        for data in items:
            total = data["total"]
            correct = data["correct"]
            wrong = total - correct
            rate = round(correct / total * 100, 1) if total > 0 else 0.0
            writer.writerow([data["exam_id"], f"Cau {data['question_id']}", correct, wrong, rate])


# --- Hàm tiện ích tìm kiếm, lọc và thống kê ---

def search_student(
    results: HashTable,
    student_id: str,
    exam_id: str | None = None,
) -> ExamResult | None:
    """Tìm một kết quả theo MSSV, có thể giới hạn theo kỳ thi."""
    student_id = student_id.strip()
    if exam_id and exam_id != "Tất cả":
        result = results.get(_result_key(exam_id, student_id))
        if result is not None:
            return result

    for result in results.values():
        if result.student_id == student_id:
            if not exam_id or exam_id == "Tất cả" or result.exam_id == exam_id:
                return result
    return None


def search_students(
    results: HashTable,
    student_id: str,
    exam_id: str | None = None,
) -> list:
    """Tìm tất cả kết quả của một MSSV qua các kỳ thi."""
    student_id = student_id.strip()
    matches = []
    for result in results.values():
        if result.student_id == student_id:
            if not exam_id or exam_id == "Tất cả" or result.exam_id == exam_id:
                matches.append(result)
    return merge_sort(matches, key=lambda r: r.exam_id)


def search_students_by_name(
    results: HashTable,
    name_query: str,
    exam_id: str | None = None,
) -> list:
    """Tìm kết quả theo họ tên sinh viên, dùng so khớp chứa không phân biệt hoa thường."""
    query = name_query.strip().lower()
    if not query:
        return []

    matches = []
    for result in results.values():
        if query in result.student_name.lower():
            if not exam_id or exam_id == "Tất cả" or result.exam_id == exam_id:
                matches.append(result)
    return merge_sort(matches, key=lambda r: (r.student_name, r.exam_id, r.student_id))


def build_student_id_trie(results: HashTable) -> PrefixTrie:
    """Tạo trie gợi ý MSSV từ bảng kết quả."""
    trie = PrefixTrie()
    seen = HashTable()

    student_ids = []
    for result in results.values():
        if not seen.contains(result.student_id):
            seen.put(result.student_id, True)
            student_ids.append(result.student_id)

    for student_id in merge_sort(student_ids, key=lambda item: item):
        trie.insert(student_id)

    return trie


def get_student_id_suggestions(
    student_id_trie: PrefixTrie | None,
    prefix: str,
    limit: int = 8,
) -> list:
    """Lấy danh sách MSSV bắt đầu bằng prefix."""
    if student_id_trie is None:
        return []
    return student_id_trie.autocomplete(prefix, limit)


def get_ranking(results: HashTable) -> list:
    """Trả về kết quả đã sắp xếp theo điểm giảm dần."""
    return merge_sort(
        results.values(),
        key=lambda r: (r.score, r.correct_count, r.exam_id, r.student_id),
        reverse=True,
    )


def build_score_index(results: HashTable) -> list:
    """Tạo chỉ mục điểm tăng dần để tìm kiếm nhị phân."""
    return merge_sort(
        results.values(),
        key=lambda r: (r.score, r.exam_id, r.student_id),
    )


def _lower_bound_score(score_index: list, target_score: float) -> int:
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
    score_index: list,
    low: float,
    high: float,
) -> list:
    """Lấy thí sinh có điểm trong khoảng [low, high]."""
    if low > high:
        low, high = high, low

    left = _lower_bound_score(score_index, low)
    right = _lower_bound_score(score_index, high + 0.001)
    return list(reversed(score_index[left:right]))


def get_hardest_questions(question_stats: HashTable, n: int = 5) -> list:
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

    hardest = []
    for _ in range(min(n, len(heap))):
        _, item = heap.pop()
        hardest.append(item)
    return hardest


def get_question_stats_items(question_stats: HashTable) -> list:
    """Trả về thống kê câu hỏi đã sắp xếp."""
    return merge_sort(
        question_stats.values(),
        key=lambda data: (data["exam_id"], _question_sort_value(data["question_id"])),
    )


def get_answer_key_items(answer_key: AnswerKeyBook, exam_id: str | None = None) -> list:
    """Trả về danh sách đáp án theo kỳ thi và số thứ tự câu."""
    items = []
    exam_ids = answer_key.exam_ids()
    for current_exam_id in exam_ids:
        if exam_id and exam_id != "Tất cả" and current_exam_id != exam_id:
            continue
        exam_key = answer_key.get_exam_key(current_exam_id)
        if exam_key is None:
            continue
        for question in exam_key.values():
            items.append(question)
    return merge_sort(
        items,
        key=lambda q: (q.exam_id, _question_sort_value(q.question_id)),
    )


def get_student_answer_items(result: ExamResult, answer_key: AnswerKeyBook) -> list:
    """Trả về từng đáp án sinh viên đã chọn và đáp án đúng."""
    exam_key = answer_key.get_exam_key(result.exam_id)
    if exam_key is None:
        return []

    items = []
    question_ids = merge_sort(exam_key.keys(), key=_question_sort_value)
    for qid in question_ids:
        question = exam_key.get(qid)
        selected = result.student.get_answer(qid)
        is_correct = selected == question.correct_answer
        items.append({
            "question_id": qid,
            "selected_answer": selected or "-",
            "correct_answer": question.correct_answer,
            "is_correct": is_correct,
        })
    return items


def _question_sort_value(question_id: str) -> tuple[int, int | str]:
    question_id = normalize_question_id(question_id)
    if str(question_id).isdigit():
        return (0, int(question_id))
    return (1, str(question_id))


def get_class_names(results: HashTable) -> list:
    """Trả về danh sách id_lop_hp duy nhất."""
    seen = HashTable()
    for result in results.values():
        seen.put(result.class_id, True)
    return merge_sort(seen.keys(), key=lambda name: name)


def get_exam_ids(results: HashTable) -> list:
    """Trả về danh sách exam_id duy nhất trong kết quả."""
    seen = HashTable()
    for result in results.values():
        seen.put(result.exam_id, True)
    return merge_sort(seen.keys(), key=lambda exam_id: exam_id)


def get_results_by_exam(ranking: list, exam_id: str) -> list:
    """Lọc kết quả theo kỳ thi."""
    if not exam_id or exam_id == "Tất cả":
        return ranking[:]
    return [result for result in ranking if result.exam_id == exam_id]


def get_results_by_class(ranking: list, class_name: str) -> list:
    """Lọc kết quả theo lớp học phần."""
    if not class_name or class_name == "Tất cả":
        return ranking[:]
    return [result for result in ranking if result.class_id == class_name]


def build_class_summary(results: HashTable) -> list:
    """Thống kê số thí sinh, điểm trung bình và tỷ lệ đạt theo lớp."""
    groups = HashTable()
    for result in results.values():
        key = f"{result.exam_id}|{result.class_id}"
        entry = groups.get(key)
        if entry is None:
            entry = {
                "exam_id": result.exam_id,
                "class_id": result.class_id,
                "class_name": result.class_name,
                "count": 0,
                "total_score": 0.0,
                "passing": 0,
            }
            groups.put(key, entry)

        entry["count"] += 1
        entry["total_score"] += result.score
        if result.score >= 5.0:
            entry["passing"] += 1

    summary = []
    for entry in groups.values():
        count = entry["count"]
        summary.append({
            "class_name": entry["class_name"],
            "class_id": entry["class_id"],
            "exam_id": entry["exam_id"],
            "count": count,
            "average": round(entry["total_score"] / count, 2) if count else 0.0,
            "passing_rate": round(entry["passing"] / count * 100, 1) if count else 0.0,
        })

    return merge_sort(summary, key=lambda item: (item["exam_id"], item["class_id"]))


def build_class_roster_summary(students: List) -> list:
    """Tạo danh sách lớp học phần từ file thí sinh, chưa cần chấm điểm."""
    groups = HashTable()
    for student in students:
        key = f"{student.exam_id}|{student.class_id}"
        entry = groups.get(key)
        if entry is None:
            entry = {
                "exam_id": student.exam_id,
                "class_id": student.class_id,
                "class_name": student.class_name,
                "count": 0,
                "average": None,
                "passing_rate": None,
            }
            groups.put(key, entry)
        entry["count"] += 1

    return merge_sort(
        groups.values(),
        key=lambda item: (item["exam_id"], item["class_id"]),
    )


def build_exam_summary(
    exam_store: ExamStore,
    answer_key: AnswerKeyBook,
    students: List,
    results: HashTable | None = None,
) -> list:
    """Tóm tắt từng kỳ thi để hiển thị, không kèm danh sách câu hỏi."""
    summary = HashTable()

    for exam in exam_store.values():
        summary.put(exam.exam_id, {
            "exam_id": exam.exam_id,
            "exam_name": exam.exam_name,
            "course_code": exam.course_code,
            "course_name": exam.course_name,
            "semester": exam.semester,
            "exam_date": exam.exam_date,
            "duration_minutes": exam.duration_minutes,
            "note": exam.note,
            "question_count": answer_key.question_count(exam.exam_id),
            "student_count": 0,
            "class_count": 0,
            "average": 0.0,
            "passing_rate": 0.0,
            "_class_seen": HashTable(),
        })

    for student in students:
        entry = summary.get(student.exam_id)
        if entry is None:
            exam = exam_store.ensure(student.exam_id)
            entry = {
                "exam_id": exam.exam_id,
                "exam_name": exam.exam_name,
                "course_code": exam.course_code,
                "course_name": exam.course_name,
                "semester": exam.semester,
                "exam_date": exam.exam_date,
                "duration_minutes": exam.duration_minutes,
                "note": exam.note,
                "question_count": answer_key.question_count(exam.exam_id),
                "student_count": 0,
                "class_count": 0,
                "average": 0.0,
                "passing_rate": 0.0,
                "_class_seen": HashTable(),
            }
            summary.put(student.exam_id, entry)

        entry["student_count"] += 1
        entry["_class_seen"].put(student.class_id, True)

    if results is not None:
        score_groups = HashTable()
        for result in results.values():
            group = score_groups.get(result.exam_id)
            if group is None:
                group = {"count": 0, "total_score": 0.0, "passing": 0}
                score_groups.put(result.exam_id, group)
            group["count"] += 1
            group["total_score"] += result.score
            if result.score >= 5.0:
                group["passing"] += 1

        for exam_id, group in score_groups.items():
            entry = summary.get(exam_id)
            if entry is not None and group["count"]:
                entry["average"] = round(group["total_score"] / group["count"], 2)
                entry["passing_rate"] = round(group["passing"] / group["count"] * 100, 1)

    items = []
    for entry in summary.values():
        entry["class_count"] = len(entry["_class_seen"])
        del entry["_class_seen"]
        items.append(entry)

    return merge_sort(items, key=lambda item: item["exam_id"])


def get_top_k_results(results: HashTable, k: int) -> list:
    """Lấy top-k theo điểm bằng quick select, rồi sắp xếp top-k."""
    arr = results.values()
    if k <= 0:
        return []
    if k >= len(arr):
        return get_ranking(results)

    cutoff = len(arr) - k
    _quick_select(arr, 0, len(arr) - 1, cutoff)
    top_k = arr[cutoff:]
    return merge_sort(
        top_k,
        key=lambda r: (r.score, r.correct_count, r.exam_id, r.student_id),
        reverse=True,
    )


def _quick_select(arr: list, lo: int, hi: int, target: int) -> None:
    while lo < hi:
        left_eq, right_eq = _partition(arr, lo, hi)
        if left_eq <= target <= right_eq:
            return
        if target < left_eq:
            hi = left_eq - 1
        else:
            lo = right_eq + 1


def _partition(arr: list, lo: int, hi: int) -> tuple[int, int]:
    mid = (lo + hi) // 2
    pivot_key = (arr[mid].score, arr[mid].correct_count, arr[mid].exam_id, arr[mid].student_id)
    lt = lo
    i = lo
    gt = hi

    while i <= gt:
        item_key = (arr[i].score, arr[i].correct_count, arr[i].exam_id, arr[i].student_id)
        if item_key < pivot_key:
            arr[lt], arr[i] = arr[i], arr[lt]
            lt += 1
            i += 1
        elif item_key > pivot_key:
            arr[i], arr[gt] = arr[gt], arr[i]
            gt -= 1
        else:
            i += 1

    return lt, gt


def build_exam_statistics(results: HashTable) -> ExamStatistics:
    """Tạo ExamStatistics từ bảng kết quả."""
    return ExamStatistics(results.values())
