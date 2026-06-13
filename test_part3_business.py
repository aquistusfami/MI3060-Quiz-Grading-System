# test_part3_business.py
# Kiểm thử nghiệp vụ Phần 3: Chấm điểm
# Chạy: python test_part3_business.py

import csv
import os
import sys
import time
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_logic import (
    load_answer_key,
    load_students,
    grade_student,
    grade_all,
    build_result_rows_in_student_order,
    sort_results,
    get_students_in_score_range,
    build_score_index,
    SORT_CSV_ORDER,
    SORT_SCORE_DESC,
    SORT_SCORE_ASC,
)
from models import ExamResult


# ─────────────────────────────────────────────
#  Tiện ích in
# ─────────────────────────────────────────────

WIDTH = 70

def print_separator(char="="):
    print(char * WIDTH)

def print_header(title: str):
    print_separator("=")
    print(f"[TEST CASE] {title}")

def print_subheader(subtitle: str):
    print_separator("-")
    print(subtitle)
    print_separator("-")

def print_result(label: str, value, expected=None):
    if expected is not None:
        print(f"  [*] {label:<24}: {value}  (kỳ vọng: {expected})")
    else:
        print(f"  [*] {label:<24}: {value}")

def print_pass(elapsed: float):
    print(f"  [*] Thời gian            : {elapsed:.6f} giây")
    print(f"  [+] Trạng thái          : ✅ PASS")
    print()

def print_fail(elapsed: float, reason: str):
    print(f"  [*] Thời gian            : {elapsed:.6f} giây")
    print(f"  [-] Trạng thái          : ❌ FAIL — {reason}")
    print()

def assert_pass(condition: bool, label: str, elapsed: float, reason: str = ""):
    if condition:
        print_pass(elapsed)
        return True
    else:
        print_fail(elapsed, reason or f"Điều kiện '{label}' không thỏa mãn")
        return False


# ─────────────────────────────────────────────
#  Helper
# ─────────────────────────────────────────────

def make_temp_csv(rows: list[dict], fieldnames: list[str] | None = None) -> str:
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
    )
    if fieldnames is None and rows:
        fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(tmp, fieldnames=fieldnames or [])
    writer.writeheader()
    writer.writerows(rows)
    tmp.close()
    return tmp.name

def cleanup(*paths):
    for p in paths:
        try:
            os.unlink(p)
        except OSError:
            pass

def setup_exam(answers: list[str], student_answers_list: list[list[str]],
               exam_id: str = "EXAM001") -> tuple:
    """
    Tạo answer_key và students từ dữ liệu thô.
    answers         : đáp án đúng theo thứ tự câu ["A","B","C",...]
    student_answers_list: [[đáp án sv1], [đáp án sv2], ...]
    Trả về (answer_key, students, ans_path, stu_path)
    """
    n = len(answers)
    ans_rows = [
        {"exam_id": exam_id, "question_id": str(i + 1), "correct_answer": answers[i]}
        for i in range(n)
    ]
    ans_path = make_temp_csv(ans_rows)

    q_cols = [f"q{i + 1}" for i in range(n)]
    stu_rows = []
    for idx, sv_ans in enumerate(student_answers_list, start=1):
        row = {"exam_id": exam_id, "mssv": f"SV{idx:03d}",
               "ho_ten": f"Sinh vien {idx}"}
        for col, ans in zip(q_cols, sv_ans):
            row[col] = ans
        # Điền cột còn thiếu bằng rỗng nếu sv_ans ngắn hơn n
        for col in q_cols[len(sv_ans):]:
            row[col] = ""
        stu_rows.append(row)

    stu_path = make_temp_csv(stu_rows)
    answer_key = load_answer_key(ans_path)
    students   = load_students(stu_path)
    return answer_key, students, ans_path, stu_path


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_01: Sinh viên làm đúng 100% — điểm 10.0
# ═══════════════════════════════════════════════════════════

def test_perfect_score():
    print_header("TC_GRADE_01: Sinh viên làm đúng 100% — điểm 10.0")
    print("Mục tiêu: Tất cả câu đúng → score=10.0, correct_count=tổng câu, wrong_questions=[].")
    print_separator("-")

    correct_answers = ["A", "B", "C", "D", "A"]
    answer_key, students, p1, p2 = setup_exam(correct_answers, [correct_answers])

    t0 = time.perf_counter()
    result = grade_student(students.get(0), answer_key)
    elapsed = time.perf_counter() - t0
    cleanup(p1, p2)

    print_result("Số câu hỏi", 5)
    print_result("Đáp án sinh viên", "Đúng hết")
    print_result("score", result.score, 10.0)
    print_result("correct_count", result.correct_count, 5)
    print_result("total_questions", result.total_questions, 5)
    print_result("wrong_questions", result.wrong_questions, [])
    print_result("accuracy_percent", result.accuracy_percent, 100.0)

    ok = (result.score == 10.0 and result.correct_count == 5
          and result.wrong_questions == [] and result.accuracy_percent == 100.0)
    return assert_pass(ok, "điểm tuyệt đối chính xác", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_02: Sinh viên làm sai một phần — điểm tính đúng công thức
# ═══════════════════════════════════════════════════════════

def test_partial_score():
    print_header("TC_GRADE_02: Làm sai một phần — điểm theo công thức đúng/tổng*10")
    print("Mục tiêu: Điểm = correct/total*10, làm tròn 2 chữ số thập phân.")
    print_separator("-")

    correct_answers = ["A", "B", "C", "D", "A", "B", "C", "D", "A", "B"]  # 10 câu

    cases = [
        # (sv đáp án, đúng/tổng, điểm kỳ vọng)
        (["A","B","C","D","A","B","C","D","A","B"], 10, 10.0),  # 10/10
        (["A","B","C","D","A","X","X","X","X","X"],  5, 5.0),   # 5/10
        (["X","X","X","X","X","X","X","X","X","X"],  0, 0.0),   # 0/10
        (["A","B","C","X","X","X","X","X","X","X"],  3, 3.0),   # 3/10
    ]

    ans_rows = [{"exam_id": "EXAM001", "question_id": str(i+1),
                 "correct_answer": correct_answers[i]} for i in range(10)]
    ans_path = make_temp_csv(ans_rows)
    answer_key = load_answer_key(ans_path)

    all_ok = True
    t0 = time.perf_counter()
    for sv_ans, expected_correct, expected_score in cases:
        stu_rows = [{"exam_id": "EXAM001", "mssv": "SV001", "ho_ten": "Test"}
                    | {f"q{i+1}": sv_ans[i] for i in range(10)}]
        stu_path = make_temp_csv(stu_rows)
        students = load_students(stu_path)
        result = grade_student(students.get(0), answer_key)
        cleanup(stu_path)

        mark = "✓" if result.score == expected_score and result.correct_count == expected_correct else "✗"
        print(f"    {mark}  {expected_correct}/10 đúng"
              f"  →  score={result.score:<6}  correct={result.correct_count}"
              f"  (kỳ vọng score={expected_score})")
        if result.score != expected_score or result.correct_count != expected_correct:
            all_ok = False

    elapsed = time.perf_counter() - t0
    cleanup(ans_path)
    print()
    return assert_pass(all_ok, "công thức điểm đúng ở mọi trường hợp", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_03: Câu bỏ trống bị tính là sai
# ═══════════════════════════════════════════════════════════

def test_blank_answer_counted_as_wrong():
    print_header("TC_GRADE_03: Câu bỏ trống — bị tính là sai (không có loại riêng)")
    print("Mục tiêu: Câu trả lời '' không khớp đáp án → vào wrong_questions.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_exam(
        ["A", "B", "C"],
        [["A", "", ""]],   # câu 1 đúng, câu 2 và 3 bỏ trống
    )

    t0 = time.perf_counter()
    result = grade_student(students.get(0), answer_key)
    elapsed = time.perf_counter() - t0
    cleanup(p1, p2)

    print_result("Đáp án sinh viên", "q1='A' (đúng), q2='' (trống), q3='' (trống)")
    print_result("correct_count", result.correct_count, 1)
    print_result("score", result.score, round(1/3*10, 2))
    print_result("Số câu sai+trống", len(result.wrong_questions), 2)
    print_result("Câu sai", sorted(result.wrong_questions))

    ok = (result.correct_count == 1
          and len(result.wrong_questions) == 2
          and result.score == round(1/3*10, 2))
    return assert_pass(ok, "câu trống được gộp vào câu sai", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_04: Câu thiếu (cột q không có trong file)
# ═══════════════════════════════════════════════════════════

def test_missing_answer_columns():
    print_header("TC_GRADE_04: Sinh viên thiếu cột đáp án — câu thiếu tính là sai")
    print("Mục tiêu: get_answer() trả '' khi cột không tồn tại → tính là sai.")
    print_separator("-")

    # Đáp án: 5 câu; sinh viên chỉ có q1, q2, q3 trong file
    ans_rows = [{"exam_id": "EXAM001", "question_id": str(i), "correct_answer": "A"}
                for i in range(1, 6)]
    ans_path = make_temp_csv(ans_rows)
    answer_key = load_answer_key(ans_path)

    stu_rows = [{"exam_id": "EXAM001", "mssv": "SV001", "ho_ten": "Test",
                 "q1": "A", "q2": "A", "q3": "A"}]  # thiếu q4, q5
    stu_path = make_temp_csv(stu_rows)
    students = load_students(stu_path)

    t0 = time.perf_counter()
    result = grade_student(students.get(0), answer_key)
    elapsed = time.perf_counter() - t0
    cleanup(ans_path, stu_path)

    print_result("Đề có", "5 câu (q1–q5)")
    print_result("File sinh viên có", "3 cột (q1–q3)")
    print_result("correct_count", result.correct_count, 3)
    print_result("total_questions", result.total_questions, 5)
    print_result("score", result.score, round(3/5*10, 2))
    print_result("Câu bị tính sai", sorted(result.wrong_questions))

    ok = (result.correct_count == 3
          and result.total_questions == 5
          and result.score == round(3/5*10, 2))
    return assert_pass(ok, "câu thiếu được tính là sai, không crash", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_05: Câu thừa trong bài làm — bị bỏ qua
# ═══════════════════════════════════════════════════════════

def test_extra_answer_columns_ignored():
    print_header("TC_GRADE_05: Sinh viên có cột đáp án thừa — bị bỏ qua")
    print("Mục tiêu: Chỉ chấm số câu trong đáp án, cột thừa không gây lỗi.")
    print_separator("-")

    # Đề 3 câu, sinh viên nộp 5 cột
    ans_rows = [{"exam_id": "EXAM001", "question_id": str(i), "correct_answer": "A"}
                for i in range(1, 4)]
    ans_path = make_temp_csv(ans_rows)
    answer_key = load_answer_key(ans_path)

    stu_rows = [{"exam_id": "EXAM001", "mssv": "SV001", "ho_ten": "Test",
                 "q1": "A", "q2": "A", "q3": "A", "q4": "X", "q5": "X"}]
    stu_path = make_temp_csv(stu_rows)
    students = load_students(stu_path)

    t0 = time.perf_counter()
    result = grade_student(students.get(0), answer_key)
    elapsed = time.perf_counter() - t0
    cleanup(ans_path, stu_path)

    print_result("Đề có", "3 câu (q1–q3)")
    print_result("File sinh viên có", "5 cột (q1–q5)")
    print_result("total_questions", result.total_questions, 3)
    print_result("correct_count", result.correct_count, 3)
    print_result("score", result.score, 10.0)
    print_result("Có crash không", "Không")

    ok = (result.total_questions == 3
          and result.correct_count == 3
          and result.score == 10.0)
    return assert_pass(ok, "cột thừa bị bỏ qua, chỉ chấm theo đáp án", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_06: Độ chính xác công thức điểm — các trường hợp đặc biệt
# ═══════════════════════════════════════════════════════════

def test_score_formula_precision():
    print_header("TC_GRADE_06: Độ chính xác công thức điểm — phân số không tròn")
    print("Mục tiêu: Điểm làm tròn đúng 2 chữ số theo round(x, 2).")
    print_separator("-")

    cases = [
        # (đúng, tổng, điểm kỳ vọng)
        (0,  40, 0.0),
        (40, 40, 10.0),
        (30, 40, 7.5),
        (1,   3, round(1/3*10, 2)),   # 3.33
        (2,   3, round(2/3*10, 2)),   # 6.67
        (33, 40, 8.25),
    ]

    all_ok = True
    t0 = time.perf_counter()

    for correct, total, expected in cases:
        # Dựng đáp án toàn "A", sinh viên đúng `correct` câu đầu
        answers  = ["A"] * total
        sv_ans   = ["A"] * correct + ["X"] * (total - correct)
        answer_key, students, p1, p2 = setup_exam(answers, [sv_ans])
        result = grade_student(students.get(0), answer_key)
        cleanup(p1, p2)

        mark = "✓" if result.score == expected else "✗"
        print(f"    {mark}  {correct}/{total} đúng"
              f"  →  score={result.score:<7}  (kỳ vọng: {expected})")
        if result.score != expected:
            all_ok = False

    elapsed = time.perf_counter() - t0
    print()
    return assert_pass(all_ok, "công thức làm tròn chính xác", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_07: grade_all() chấm toàn bộ — đủ số kết quả
# ═══════════════════════════════════════════════════════════

def test_grade_all_count():
    print_header("TC_GRADE_07: grade_all() chấm toàn bộ sinh viên")
    print("Mục tiêu: Số kết quả == số sinh viên, key đúng dạng 'exam_id|student_id'.")
    print_separator("-")

    n_students = 6
    answers = ["A", "B", "C"]
    answer_key, students, p1, p2 = setup_exam(
        answers,
        [["A", "B", "C"]] * n_students,
    )

    t0 = time.perf_counter()
    results = grade_all(students, answer_key)
    elapsed = time.perf_counter() - t0
    cleanup(p1, p2)

    sample_key = "EXAM001|SV001"
    sample_result = results.get(sample_key)

    print_result("Số sinh viên đầu vào", n_students)
    print_result("Số kết quả trả về", len(results), n_students)
    print_result("Kiểu trả về", type(results).__name__, "HashTable")
    print_result("Key mẫu", sample_key)
    print_result("Tìm được key mẫu", sample_result is not None, True)
    print_result("Điểm SV001", sample_result.score if sample_result else "—", 10.0)

    ok = len(results) == n_students and sample_result is not None and sample_result.score == 10.0
    return assert_pass(ok, "grade_all trả đúng số kết quả và key đúng dạng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_08: grade_all() — nhiều kỳ thi cùng lúc
# ═══════════════════════════════════════════════════════════

def test_grade_all_multiple_exams():
    print_header("TC_GRADE_08: grade_all() — nhiều kỳ thi trong cùng một lần chạy")
    print("Mục tiêu: Sinh viên từ 2 kỳ thi khác nhau đều được chấm đúng đáp án của kỳ thi đó.")
    print_separator("-")

    ans_rows = (
        [{"exam_id": "EXAM001", "question_id": "1", "correct_answer": "A"},
         {"exam_id": "EXAM001", "question_id": "2", "correct_answer": "B"}]
        + [{"exam_id": "EXAM002", "question_id": "1", "correct_answer": "D"},
           {"exam_id": "EXAM002", "question_id": "2", "correct_answer": "C"}]
    )
    ans_path = make_temp_csv(ans_rows)
    answer_key = load_answer_key(ans_path)

    stu_rows = [
        {"exam_id": "EXAM001", "mssv": "SV001", "ho_ten": "A", "q1": "A", "q2": "B"},  # 10đ
        {"exam_id": "EXAM002", "mssv": "SV002", "ho_ten": "B", "q1": "D", "q2": "X"},  # 5đ
    ]
    stu_path = make_temp_csv(stu_rows)
    students = load_students(stu_path)

    t0 = time.perf_counter()
    results = grade_all(students, answer_key)
    elapsed = time.perf_counter() - t0
    cleanup(ans_path, stu_path)

    r1 = results.get("EXAM001|SV001")
    r2 = results.get("EXAM002|SV002")

    print_result("Số kết quả", len(results), 2)
    print_result("SV001 (EXAM001) score", r1.score if r1 else "—", 10.0)
    print_result("SV002 (EXAM002) score", r2.score if r2 else "—", 5.0)
    print_result("SV001 correct_count", r1.correct_count if r1 else "—", 2)
    print_result("SV002 correct_count", r2.correct_count if r2 else "—", 1)

    ok = (r1 is not None and r1.score == 10.0
          and r2 is not None and r2.score == 5.0)
    return assert_pass(ok, "mỗi sinh viên được chấm đúng đáp án kỳ thi của mình", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_09: Sắp xếp — Mặc định theo CSV
# ═══════════════════════════════════════════════════════════

def test_sort_csv_order():
    print_header("TC_GRADE_09: Sắp xếp kết quả — Mặc định theo CSV")
    print("Mục tiêu: sort_results(SORT_CSV_ORDER) giữ nguyên thứ tự file, không đổi vị trí.")
    print_separator("-")

    scores = [7.0, 3.0, 9.0, 5.0, 1.0]
    answer_key, students, p1, p2 = setup_exam(
        ["A"] * 10,
        [[("A" if j < round(s) else "X") for j in range(10)] for s in scores],
    )
    results = grade_all(students, answer_key)
    rows_in_order = build_result_rows_in_student_order(students, results)

    t0 = time.perf_counter()
    sorted_rows = sort_results(rows_in_order, SORT_CSV_ORDER)
    elapsed = time.perf_counter() - t0
    cleanup(p1, p2)

    actual_ids = [r.student_id for r in sorted_rows]
    expected_ids = [r.student_id for r in rows_in_order]

    print_result("Thứ tự MSSV gốc", expected_ids)
    print_result("Thứ tự sau sort", actual_ids)
    print_result("Giữ nguyên thứ tự", actual_ids == expected_ids, True)

    ok = actual_ids == expected_ids
    return assert_pass(ok, "SORT_CSV_ORDER không thay đổi thứ tự", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_10: Sắp xếp — Điểm cao đến thấp
# ═══════════════════════════════════════════════════════════

def test_sort_score_desc():
    print_header("TC_GRADE_10: Sắp xếp kết quả — Điểm cao đến thấp")
    print("Mục tiêu: sort_results(SORT_SCORE_DESC) → điểm giảm dần, ổn định.")
    print_separator("-")

    # Điểm có 2 sinh viên cùng điểm để test tính ổn định
    answer_key, students, p1, p2 = setup_exam(
        ["A"] * 10,
        [
            ["A"]*9 + ["X"],  # SV001: 9/10 = 9.0
            ["A"]*5 + ["X"]*5, # SV002: 5/10 = 5.0
            ["A"]*10,          # SV003: 10/10 = 10.0
            ["A"]*5 + ["X"]*5, # SV004: 5/10 = 5.0 (trùng SV002)
            ["A"]*1 + ["X"]*9, # SV005: 1/10 = 1.0
        ],
    )
    results = grade_all(students, answer_key)
    rows = build_result_rows_in_student_order(students, results)

    t0 = time.perf_counter()
    sorted_rows = sort_results(rows, SORT_SCORE_DESC)
    elapsed = time.perf_counter() - t0
    cleanup(p1, p2)

    scores_out = [r.score for r in sorted_rows]
    is_desc = all(scores_out[i] >= scores_out[i+1] for i in range(len(scores_out)-1))

    print_result("Đầu vào (điểm)", [r.score for r in rows])
    print_result("Sau sort (điểm)", scores_out)
    print_result("Giảm dần đúng", is_desc, True)
    print_result("Điểm cao nhất đầu", scores_out[0], 10.0)
    print_result("Điểm thấp nhất cuối", scores_out[-1], 1.0)

    ok = is_desc and scores_out[0] == 10.0 and scores_out[-1] == 1.0
    return assert_pass(ok, "kết quả sắp xếp giảm dần đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_11: Sắp xếp — Điểm thấp đến cao
# ═══════════════════════════════════════════════════════════

def test_sort_score_asc():
    print_header("TC_GRADE_11: Sắp xếp kết quả — Điểm thấp đến cao")
    print("Mục tiêu: sort_results(SORT_SCORE_ASC) → điểm tăng dần.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_exam(
        ["A"] * 10,
        [["A"]*k + ["X"]*(10-k) for k in [2, 8, 5, 0, 10]],
    )
    results = grade_all(students, answer_key)
    rows = build_result_rows_in_student_order(students, results)

    t0 = time.perf_counter()
    sorted_rows = sort_results(rows, SORT_SCORE_ASC)
    elapsed = time.perf_counter() - t0
    cleanup(p1, p2)

    scores_out = [r.score for r in sorted_rows]
    is_asc = all(scores_out[i] <= scores_out[i+1] for i in range(len(scores_out)-1))

    print_result("Đầu vào (điểm)", [r.score for r in rows])
    print_result("Sau sort (điểm)", scores_out)
    print_result("Tăng dần đúng", is_asc, True)
    print_result("Điểm thấp nhất đầu", scores_out[0], 0.0)
    print_result("Điểm cao nhất cuối", scores_out[-1], 10.0)

    ok = is_asc and scores_out[0] == 0.0 and scores_out[-1] == 10.0
    return assert_pass(ok, "kết quả sắp xếp tăng dần đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_12: sort_results() tùy chọn không hợp lệ — ném ValueError
# ═══════════════════════════════════════════════════════════

def test_sort_invalid_option():
    print_header("TC_GRADE_12: sort_results() — tùy chọn không hợp lệ")
    print("Mục tiêu: Tùy chọn ngoài 3 giá trị hợp lệ → ném ValueError, không crash im lặng.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_exam(["A"], [["A"]])
    results = grade_all(students, answer_key)
    rows = build_result_rows_in_student_order(students, results)
    cleanup(p1, p2)

    t0 = time.perf_counter()
    raised = False
    err_msg = ""
    try:
        sort_results(rows, "Tùy chọn không tồn tại")
    except ValueError as e:
        raised = True
        err_msg = str(e)
    elapsed = time.perf_counter() - t0

    print_result("Đầu vào sort_option", "'Tùy chọn không tồn tại'")
    print_result("Ném ValueError", raised, True)
    if err_msg:
        print_result("Thông báo", err_msg)

    ok = raised
    return assert_pass(ok, "tùy chọn không hợp lệ bị từ chối bằng ValueError", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_13: Lọc theo khoảng điểm — build_score_index + get_students_in_score_range
# ═══════════════════════════════════════════════════════════

def test_filter_score_range():
    print_header("TC_GRADE_13: Lọc kết quả theo khoảng điểm [low, high]")
    print("Mục tiêu: Chỉ trả về sinh viên có điểm trong khoảng, tìm kiếm nhị phân.")
    print_separator("-")

    # 10 sinh viên với điểm 1.0, 2.0, ..., 10.0
    answer_key, students, p1, p2 = setup_exam(
        ["A"] * 10,
        [["A"]*k + ["X"]*(10-k) for k in range(1, 11)],
    )
    results = grade_all(students, answer_key)
    cleanup(p1, p2)

    t0 = time.perf_counter()
    score_index = build_score_index(results)
    in_range    = get_students_in_score_range(score_index, 5.0, 8.0)
    elapsed     = time.perf_counter() - t0

    scores_found = sorted([r.score for r in in_range])
    expected_scores = [5.0, 6.0, 7.0, 8.0]

    print_result("Dải điểm lọc", "[5.0, 8.0]")
    print_result("Điểm tìm thấy", scores_found, expected_scores)
    print_result("Số sinh viên", len(in_range), 4)
    print_result("Nằm ngoài khoảng", any(r.score < 5.0 or r.score > 8.0 for r in in_range), False)

    ok = (scores_found == expected_scores and len(in_range) == 4
          and not any(r.score < 5.0 or r.score > 8.0 for r in in_range))
    return assert_pass(ok, "lọc khoảng điểm đúng và không lệch biên", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_GRADE_14: Lọc khoảng điểm biên — [0.0, 10.0] và khoảng không có ai
# ═══════════════════════════════════════════════════════════

def test_filter_score_range_edge():
    print_header("TC_GRADE_14: Lọc khoảng điểm biên — toàn bộ và khoảng trống")
    print("Mục tiêu: [0, 10] trả tất cả; khoảng không có ai trả danh sách rỗng.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_exam(
        ["A"] * 10,
        [["A"]*5 + ["X"]*5,  # SV001: 5.0
         ["A"]*8 + ["X"]*2,  # SV002: 8.0
         ["A"]*3 + ["X"]*7], # SV003: 3.0
    )
    results = grade_all(students, answer_key)
    score_index = build_score_index(results)
    cleanup(p1, p2)

    t0 = time.perf_counter()
    all_students = get_students_in_score_range(score_index, 0.0, 10.0)
    no_students  = get_students_in_score_range(score_index, 9.0, 9.9)
    elapsed = time.perf_counter() - t0

    print_subheader("Trường hợp A — lọc [0.0, 10.0]")
    print_result("Kết quả", len(all_students), 3)

    print_subheader("Trường hợp B — lọc [9.0, 9.9] (không ai trong khoảng)")
    print_result("Kết quả", len(no_students), 0)

    ok = len(all_students) == 3 and len(no_students) == 0
    return assert_pass(ok, "lọc biên chính xác", elapsed)


# ═══════════════════════════════════════════════════════════
#  Hàm main
# ═══════════════════════════════════════════════════════════

def run_all():
    tests = [
        test_perfect_score,
        test_partial_score,
        test_blank_answer_counted_as_wrong,
        test_missing_answer_columns,
        test_extra_answer_columns_ignored,
        test_score_formula_precision,
        test_grade_all_count,
        test_grade_all_multiple_exams,
        test_sort_csv_order,
        test_sort_score_desc,
        test_sort_score_asc,
        test_sort_invalid_option,
        test_filter_score_range,
        test_filter_score_range_edge,
    ]

    passed = 0
    failed = 0

    t_total_start = time.perf_counter()
    for test_fn in tests:
        try:
            is_success = test_fn()
            if is_success:
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"  [-] Trạng thái: ❌ FAIL (AssertionError: {e})\n")
            failed += 1
        except Exception as e:
            print(f"  [-] Trạng thái: ❌ ERROR — {type(e).__name__}: {e}\n")
            failed += 1
            
    t_total = time.perf_counter() - t_total_start

    print_separator("=")
    print(f"  KẾT QUẢ TỔNG HỢP — PHẦN 3: CHẤM ĐIỂM")
    print_separator("-")
    print(f"  Tổng số test case : {len(tests)}")
    print(f"  ✅ Passed          : {passed}")
    print(f"  ❌ Failed          : {failed}")
    print(f"  Tổng thời gian    : {t_total:.6f} giây")
    print_separator("=")


if __name__ == "__main__":
    run_all()