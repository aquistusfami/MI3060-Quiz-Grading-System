# test_part1_business.py
# Kiểm thử nghiệp vụ Phần 1: Quản lý & Nạp Đề thi (Từ File CSV)
# Chạy: python test_part1_business.py

import csv
import os
import sys
import time
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_logic import (
    AnswerKeyBook,
    load_answer_key,
    validate_answer_key_csv,
    validate_grading_inputs,
    load_students,
    grade_student,
)
from models import normalize_question_id, normalize_answer


# ─────────────────────────────────────────────
#  Tiện ích in kết quả
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
        print(f"  [*] {label:<18}: {value}  (kỳ vọng: {expected})")
    else:
        print(f"  [*] {label:<18}: {value}")

def print_pass(elapsed: float):
    print(f"  [*] Thời gian       : {elapsed:.6f} giây")
    print(f"  [+] Trạng thái     : ✅ PASS")
    print()

def print_fail(elapsed: float, reason: str):
    print(f"  [*] Thời gian       : {elapsed:.6f} giây")
    print(f"  [-] Trạng thái     : ❌ FAIL — {reason}")
    print()

def assert_pass(condition: bool, label: str, elapsed: float, reason: str = ""):
    if condition:
        print_pass(elapsed)
        return True
    else:
        print_fail(elapsed, reason or f"Điều kiện '{label}' không thỏa mãn")
        return False


# ─────────────────────────────────────────────
#  Helper: tạo file CSV tạm thời
# ─────────────────────────────────────────────

def make_temp_csv(rows: list[dict], fieldnames: list[str] | None = None) -> str:
    """Tạo file CSV tạm, trả về đường dẫn."""
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


# ═══════════════════════════════════════════════════════════
#  TC_LOAD_01: Nạp file đáp án hợp lệ, kiểm tra cấu trúc lưu trữ
# ═══════════════════════════════════════════════════════════

def test_load_valid_answer_key():
    print_header("TC_LOAD_01: Nạp file đáp án hợp lệ và kiểm tra cấu trúc lưu trữ")
    print("Mục tiêu: Dữ liệu được lưu đúng vào AnswerKeyBook → HashTable → Question.")
    print_separator("-")

    rows = [
        {"exam_id": "EXAM001", "question_id": "1", "correct_answer": "A"},
        {"exam_id": "EXAM001", "question_id": "2", "correct_answer": "C"},
        {"exam_id": "EXAM001", "question_id": "3", "correct_answer": "B"},
        {"exam_id": "EXAM002", "question_id": "1", "correct_answer": "D"},
    ]
    path = make_temp_csv(rows)

    t0 = time.perf_counter()
    answer_key = load_answer_key(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    exam1_key = answer_key.get_exam_key("EXAM001")
    exam2_key = answer_key.get_exam_key("EXAM002")
    q1 = exam1_key.get("1") if exam1_key else None

    print_result("Đầu vào", "4 câu hỏi, 2 kỳ thi (EXAM001: 3 câu, EXAM002: 1 câu)")
    print_result("Tổng câu (len)", len(answer_key), 4)
    print_result("EXAM001 key type", type(exam1_key).__name__, "HashTable")
    print_result("EXAM002 key type", type(exam2_key).__name__, "HashTable")
    print_result("Câu 1 EXAM001", q1.correct_answer if q1 else None, "A")
    print_result("Kỳ thi trong EXAM002", len(exam2_key) if exam2_key else 0, 1)

    ok = (
        len(answer_key) == 4
        and exam1_key is not None
        and exam2_key is not None
        and q1 is not None
        and q1.correct_answer == "A"
        and len(exam2_key) == 1
    )
    return assert_pass(ok, "cấu trúc lưu trữ đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_LOAD_02: Chuẩn hóa đáp án (strip + upper)
# ═══════════════════════════════════════════════════════════

def test_normalize_answer():
    print_header("TC_LOAD_02: Chuẩn hóa đáp án — strip() và upper()")
    print("Mục tiêu: Đáp án chữ thường hoặc có khoảng trắng phải được chuẩn hóa.")
    print_separator("-")

    rows = [
        {"exam_id": "EXAM001", "question_id": "1", "correct_answer": "  a  "},
        {"exam_id": "EXAM001", "question_id": "2", "correct_answer": "b"},
        {"exam_id": "EXAM001", "question_id": "3", "correct_answer": "  C  "},
    ]
    path = make_temp_csv(rows)

    t0 = time.perf_counter()
    answer_key = load_answer_key(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    exam_key = answer_key.get_exam_key("EXAM001")
    q1 = exam_key.get("1") if exam_key else None
    q2 = exam_key.get("2") if exam_key else None
    q3 = exam_key.get("3") if exam_key else None

    print_result("Đầu vào câu 1", "'  a  '  →", f"'{q1.correct_answer if q1 else '?'}'")
    print_result("Kỳ vọng câu 1", "A", "A")
    print_result("Đầu vào câu 2", "'b'       →", f"'{q2.correct_answer if q2 else '?'}'")
    print_result("Kỳ vọng câu 2", "B", "B")
    print_result("Đầu vào câu 3", "'  C  '  →", f"'{q3.correct_answer if q3 else '?'}'")
    print_result("Kỳ vọng câu 3", "C", "C")

    ok = (
        q1 is not None and q1.correct_answer == "A"
        and q2 is not None and q2.correct_answer == "B"
        and q3 is not None and q3.correct_answer == "C"
    )
    return assert_pass(ok, "normalize_answer đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_LOAD_03: Chuẩn hóa mã câu hỏi (normalize_question_id)
# ═══════════════════════════════════════════════════════════

def test_normalize_question_id():
    print_header("TC_LOAD_03: Chuẩn hóa mã câu hỏi — normalize_question_id()")
    print("Mục tiêu: Các dạng mã câu hỏi khác nhau đều về cùng dạng chuẩn.")
    print_separator("-")

    cases = [
        ("câu 1",  "1"),
        ("Câu 10", "10"),
        ("q1",     "1"),
        ("Q03",    "3"),
        ("01",     "1"),
        ("10",     "10"),
        ("A1",     "A1"),
    ]

    t0 = time.perf_counter()
    results = [(inp, normalize_question_id(inp)) for inp, _ in cases]
    elapsed = time.perf_counter() - t0

    all_ok = True
    print_result("Đầu vào", "→ Kết quả thực tế  (kỳ vọng)")
    print("  " + "-" * 45)
    for (inp, expected), (_, actual) in zip(cases, results):
        status = "✓" if actual == expected else "✗"
        print(f"    {status}  {inp!r:<14} → {actual!r:<10}  (kỳ vọng: {expected!r})")
        if actual != expected:
            all_ok = False

    print()
    return assert_pass(all_ok, "tất cả mã câu hỏi được chuẩn hóa đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_LOAD_04: Truy xuất O(1) theo exam_id
# ═══════════════════════════════════════════════════════════

def test_get_exam_key_o1():
    print_header("TC_LOAD_04: Truy xuất bảng đáp án O(1) theo exam_id")
    print("Mục tiêu: get_exam_key() trả về đúng HashTable, không duyệt tuyến tính.")
    print_separator("-")

    rows = [{"exam_id": "EXAM001", "question_id": str(i), "correct_answer": "A"}
            for i in range(1, 21)]
    rows += [{"exam_id": "EXAM002", "question_id": str(i), "correct_answer": "B"}
             for i in range(1, 11)]
    path = make_temp_csv(rows)
    answer_key = load_answer_key(path)
    cleanup(path)

    t0 = time.perf_counter()
    exam1_key = answer_key.get_exam_key("EXAM001")
    exam2_key = answer_key.get_exam_key("EXAM002")
    q5 = exam1_key.get("5") if exam1_key else None
    elapsed = time.perf_counter() - t0

    print_result("Đầu vào", "EXAM001: 20 câu, EXAM002: 10 câu")
    print_result("EXAM001 key type", type(exam1_key).__name__, "HashTable")
    print_result("EXAM002 key type", type(exam2_key).__name__, "HashTable")
    print_result("Câu 5 EXAM001", q5.correct_answer if q5 else None, "A")
    print_result("Câu không tồn tại", exam1_key.get("99") if exam1_key else "—", None)

    ok = (
        exam1_key is not None
        and exam2_key is not None
        and q5 is not None and q5.correct_answer == "A"
        and (exam1_key.get("99") is None)
    )
    return assert_pass(ok, "get_exam_key trả về đúng HashTable", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_LOAD_05: Truy xuất mã đề không tồn tại — trả về None an toàn
# ═══════════════════════════════════════════════════════════

def test_get_nonexistent_exam_key():
    print_header("TC_LOAD_05: Truy xuất mã đề không tồn tại")
    print("Mục tiêu: get_exam_key() trả về None, không crash chương trình.")
    print_separator("-")

    rows = [{"exam_id": "EXAM001", "question_id": "1", "correct_answer": "A"}]
    path = make_temp_csv(rows)
    answer_key = load_answer_key(path)
    cleanup(path)

    t0 = time.perf_counter()
    result = answer_key.get_exam_key("EXAM999")
    elapsed = time.perf_counter() - t0

    print_result("Đầu vào", "Truy xuất 'EXAM999' — không có trong hệ thống")
    print_result("Kết quả trả về", result, None)
    print_result("Có crash không", "Không")

    # Thử gọi grade_student với exam_id không tồn tại
    student_rows = [{"exam_id": "EXAM999", "mssv": "SV001", "ho_ten": "Test", "q1": "A"}]
    student_path = make_temp_csv(student_rows)
    students = load_students(student_path)
    cleanup(student_path)

    caught_error = False
    error_msg = ""
    try:
        grade_student(students.get(0), answer_key)
    except ValueError as e:
        caught_error = True
        error_msg = str(e)

    print_result("grade_student bắt lỗi", caught_error, True)
    print_result("Thông báo lỗi", error_msg[:55] + "..." if len(error_msg) > 55 else error_msg)

    ok = result is None and caught_error
    return assert_pass(ok, "xử lý mã đề không tồn tại an toàn", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_LOAD_06: File đáp án rỗng (chỉ có header)
# ═══════════════════════════════════════════════════════════

def test_empty_answer_key_file():
    print_header("TC_LOAD_06: File đáp án rỗng (chỉ có header)")
    print("Mục tiêu: Hệ thống không crash, validate_grading_inputs() báo lỗi rõ ràng.")
    print_separator("-")

    path = make_temp_csv([], fieldnames=["exam_id", "question_id", "correct_answer"])

    t0 = time.perf_counter()
    answer_key = load_answer_key(path)
    cleanup(path)

    student_rows = [{"exam_id": "EXAM001", "mssv": "SV001", "ho_ten": "Test", "q1": "A"}]
    student_path = make_temp_csv(student_rows)
    students = load_students(student_path)
    cleanup(student_path)

    errors = validate_grading_inputs(answer_key, students)
    elapsed = time.perf_counter() - t0

    print_result("Đầu vào", "File đáp án không có dòng dữ liệu")
    print_result("len(answer_key)", len(answer_key), 0)
    print_result("Số lỗi validate", len(errors), ">= 1")
    print_result("Lỗi đầu tiên", errors[0] if errors else "—")

    ok = len(answer_key) == 0 and len(errors) >= 1 and "câu hỏi" in errors[0].lower()
    return assert_pass(ok, "file rỗng được phát hiện và báo lỗi", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_LOAD_07: File đáp án thiếu cột bắt buộc
# ═══════════════════════════════════════════════════════════

def test_validate_answer_key_missing_columns():
    print_header("TC_LOAD_07: File đáp án thiếu cột bắt buộc")
    print("Mục tiêu: validate_answer_key_csv() phát hiện thiếu cột và báo lỗi.")
    print_separator("-")

    # Chỉ có exam_id, thiếu question_id và correct_answer
    path = make_temp_csv(
        [{"exam_id": "EXAM001", "ten_mon": "Giai tich"}],
        fieldnames=["exam_id", "ten_mon"]
    )

    t0 = time.perf_counter()
    errors = validate_answer_key_csv(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    print_result("Đầu vào", "File chỉ có cột: exam_id, ten_mon")
    print_result("Số lỗi", len(errors), ">= 1")
    if errors:
        print_result("Nội dung lỗi", errors[0])

    ok = len(errors) >= 1 and any(
        "question_id" in e or "correct_answer" in e for e in errors
    )
    return assert_pass(ok, "phát hiện thiếu cột bắt buộc", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_LOAD_08: Suy luận exam_id từ các cột ma_hp / hoc_ky / id_lop_hp
# ═══════════════════════════════════════════════════════════

def test_infer_exam_id_from_columns():
    print_header("TC_LOAD_08: Suy luận exam_id từ cột ma_hp + hoc_ky + id_lop_hp")
    print("Mục tiêu: Khi không có cột exam_id, hệ thống tự ghép exam_id từ các cột phụ.")
    print_separator("-")

    # Trường hợp A: Đủ 3 cột
    rows_a = [{"ma_hp": "MI3060", "hoc_ky": "20251", "id_lop_hp": "163613",
               "question_id": "1", "correct_answer": "A"}]
    path_a = make_temp_csv(rows_a)

    t0 = time.perf_counter()
    answer_key_a = load_answer_key(path_a)
    elapsed_a = time.perf_counter() - t0
    cleanup(path_a)

    expected_a = "MI3060-20251-163613"
    exam_ids_a = answer_key_a.exam_ids()

    print_subheader("Trường hợp A — Đủ 3 cột: ma_hp + hoc_ky + id_lop_hp")
    print_result("Đầu vào", "ma_hp=MI3060, hoc_ky=20251, id_lop_hp=163613")
    print_result("exam_id sinh ra", exam_ids_a[0] if exam_ids_a else "—", expected_a)
    ok_a = exam_ids_a and exam_ids_a[0] == expected_a

    # Trường hợp B: Chỉ có ma_hp + hoc_ky
    rows_b = [{"ma_hp": "MI3060", "hoc_ky": "20251",
               "question_id": "1", "correct_answer": "B"}]
    path_b = make_temp_csv(rows_b)

    t1 = time.perf_counter()
    answer_key_b = load_answer_key(path_b)
    elapsed_b = time.perf_counter() - t1
    cleanup(path_b)

    expected_b = "MI3060-20251"
    exam_ids_b = answer_key_b.exam_ids()

    print_subheader("Trường hợp B — Chỉ có: ma_hp + hoc_ky")
    print_result("Đầu vào", "ma_hp=MI3060, hoc_ky=20251")
    print_result("exam_id sinh ra", exam_ids_b[0] if exam_ids_b else "—", expected_b)
    ok_b = exam_ids_b and exam_ids_b[0] == expected_b

    elapsed = elapsed_a + elapsed_b
    ok = ok_a and ok_b
    return assert_pass(ok, "suy luận exam_id đúng theo từng trường hợp", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_LOAD_09: exam_id phân biệt chữ hoa / chữ thường
# ═══════════════════════════════════════════════════════════

def test_exam_id_case_sensitive():
    print_header("TC_LOAD_09: exam_id phân biệt chữ hoa/chữ thường")
    print("Mục tiêu: Hệ thống KHÔNG tự upper() exam_id — 'EXAM_A' ≠ 'exam_a'.")
    print_separator("-")

    rows = [{"exam_id": "EXAM_A", "question_id": "1", "correct_answer": "A"}]
    path = make_temp_csv(rows)
    answer_key = load_answer_key(path)
    cleanup(path)

    t0 = time.perf_counter()
    result_upper = answer_key.get_exam_key("EXAM_A")   # phải tìm thấy
    result_lower = answer_key.get_exam_key("exam_a")   # phải None
    elapsed = time.perf_counter() - t0

    # Kiểm tra validate phát hiện lỗi khi sinh viên dùng exam_a
    student_rows = [{"exam_id": "exam_a", "mssv": "SV001", "ho_ten": "Test", "q1": "A"}]
    student_path = make_temp_csv(student_rows)
    students = load_students(student_path)
    cleanup(student_path)

    errors = validate_grading_inputs(answer_key, students)

    print_result("Đầu vào đáp án", "exam_id = 'EXAM_A'")
    print_result("Sinh viên dùng", "exam_id = 'exam_a'")
    print_result("get('EXAM_A')", "Tìm thấy" if result_upper else "Không tìm thấy", "Tìm thấy")
    print_result("get('exam_a')", "Tìm thấy" if result_lower else "Không tìm thấy", "Không tìm thấy")
    print_result("validate lỗi", len(errors), ">= 1")
    if errors:
        print_result("Nội dung lỗi", errors[0][:60] + "..." if len(errors[0]) > 60 else errors[0])

    ok = result_upper is not None and result_lower is None and len(errors) >= 1
    return assert_pass(ok, "exam_id phân biệt hoa/thường, validate phát hiện lỗi", elapsed)


# ═══════════════════════════════════════════════════════════
#  Hàm main: chạy toàn bộ và tổng hợp kết quả
# ═══════════════════════════════════════════════════════════

def run_all():
    tests = [
        test_load_valid_answer_key,
        test_normalize_answer,
        test_normalize_question_id,
        test_get_exam_key_o1,
        test_get_nonexistent_exam_key,
        test_empty_answer_key_file,
        test_validate_answer_key_missing_columns,
        test_infer_exam_id_from_columns,
        test_exam_id_case_sensitive,
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
    print(f"  KẾT QUẢ TỔNG HỢP — PHẦN 1: QUẢN LÝ & NẠP ĐỀ THI")
    print_separator("-")
    print(f"  Tổng số test case : {len(tests)}")
    print(f"  ✅ Passed          : {passed}")
    print(f"  ❌ Failed          : {failed}")
    print(f"  Tổng thời gian    : {t_total:.6f} giây")
    print_separator("=")


if __name__ == "__main__":
    run_all()