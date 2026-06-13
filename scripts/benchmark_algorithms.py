"""Đo thời gian các thao tác chính trên bộ dữ liệu hiệu năng có sẵn.

Script đọc ba file trong ``data/performance`` và chỉ ghi kết quả đo ra stdout;
không thay đổi dữ liệu nguồn.
"""

import os
import sys
import time

# Đưa thư mục project vào đường dẫn import khi chạy script trực tiếp.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app_logic import (
    build_score_index,
    build_student_search_index,
    compute_question_stats,
    get_hardest_questions,
    get_ranking,
    get_student_id_suggestions,
    get_student_name_suggestions,
    get_students_in_score_range,
    grade_all,
    load_answer_key,
    load_exam_store,
    load_students,
    search_students_indexed,
)
from custom_structures import List


PERF_DIR = os.path.join(BASE_DIR, "data", "performance")
ANSWER_KEY_PATH = os.path.join(PERF_DIR, "answer_key.csv")
STUDENTS_PATH = os.path.join(PERF_DIR, "students.csv")
EXAMS_PATH = os.path.join(PERF_DIR, "exams.csv")


def main():
    """Chạy toàn bộ benchmark và in thời gian từng thao tác ra stdout."""
    if not os.path.exists(ANSWER_KEY_PATH) or not os.path.exists(STUDENTS_PATH):
        print("Thiếu dữ liệu hiệu năng. Chạy: python scripts/generate_perf_data.py")
        return

    timings = List()
    answer_key = timed(timings, "Tải đáp án", lambda: load_answer_key(ANSWER_KEY_PATH))
    students = timed(timings, "Tải bài làm", lambda: load_students(STUDENTS_PATH, answer_key.max_question_count()))
    timed(timings, "Tải metadata kỳ thi", lambda: load_exam_store(EXAMS_PATH))
    results = timed(timings, "Chấm điểm", lambda: grade_all(students, answer_key))
    score_index = timed(timings, "Tạo chỉ mục điểm", lambda: build_score_index(results))
    timed(timings, "Sắp xếp xếp hạng", lambda: get_ranking(results))
    timed(timings, "Lọc khoảng điểm", lambda: get_students_in_score_range(score_index, 7.0, 8.5))
    question_stats = timed(timings, "Thống kê câu hỏi", lambda: compute_question_stats(students, answer_key))
    timed(timings, "Top câu khó", lambda: get_hardest_questions(question_stats, 20))
    search_index = timed(timings, "Tạo chỉ mục tìm kiếm", lambda: build_student_search_index(results))
    timed(timings, "Tra cứu MSSV bằng chỉ mục", lambda: search_students_indexed(search_index, "202600001"))
    timed(timings, "Gợi ý MSSV bằng trie", lambda: get_student_id_suggestions(search_index.student_id_trie, "2026", 8))
    timed(timings, "Gợi ý họ tên bằng trie", lambda: get_student_name_suggestions(search_index, "nguyen", 8))

    print()
    print("Kết quả benchmark")
    print("-" * 58)
    print(f"Số thí sinh        : {len(students)}")
    print(f"Số kết quả         : {len(results)}")
    print(f"Số đáp án          : {len(answer_key)}")
    print(f"Số thống kê câu hỏi: {len(question_stats)}")
    print("-" * 58)
    for label, elapsed_ms in timings:
        print(f"{label:<28} {elapsed_ms:>10.2f} ms")


def timed(timings, label, action):
    """Đo một callable và thêm ``(label, milliseconds)`` vào ``timings``.

    Returns:
        Giá trị do ``action`` trả về để bước benchmark sau có thể tái sử dụng.
    """
    start = time.perf_counter()
    result = action()
    elapsed_ms = (time.perf_counter() - start) * 1000
    timings.append((label, elapsed_ms))
    return result


if __name__ == "__main__":
    main()
