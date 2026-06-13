# test_part2_business.py
# Kiểm thử nghiệp vụ Phần 2: Quản lý Bài làm Sinh viên
# Chạy: python test_part2_business.py

import csv
import os
import sys
import time
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_logic import (
    load_students,
    load_answer_key,
    validate_students_csv,
    validate_grading_inputs,
    grade_all,
    STUDENT_ID_COLUMNS,
    STUDENT_NAME_COLUMNS,
)
from custom_structures import List


# ─────────────────────────────────────────────
#  Tiện ích in kết quả (giữ nguyên format phần 1)
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
        print(f"  [*] {label:<22}: {value}  (kỳ vọng: {expected})")
    else:
        print(f"  [*] {label:<22}: {value}")

def print_pass(elapsed: float):
    print(f"  [*] Thời gian          : {elapsed:.6f} giây")
    print(f"  [+] Trạng thái        : ✅ PASS")
    print()

def print_fail(elapsed: float, reason: str):
    print(f"  [*] Thời gian          : {elapsed:.6f} giây")
    print(f"  [-] Trạng thái        : ❌ FAIL — {reason}")
    print()

def assert_pass(condition: bool, label: str, elapsed: float, reason: str = ""):
    if condition:
        print_pass(elapsed)
        return True
    else:
        print_fail(elapsed, reason or f"Điều kiện '{label}' không thỏa mãn")
        return False


# ─────────────────────────────────────────────
#  Helper: tạo / dọn file CSV tạm
# ─────────────────────────────────────────────

def make_temp_csv(rows: list, fieldnames: list | None = None) -> str:
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

def make_answer_key(exam_id="EXAM001", n_questions=3):
    """Tạo AnswerKeyBook nhanh trong bộ nhớ."""
    rows = [
        {"exam_id": exam_id, "question_id": str(i), "correct_answer": "A"}
        for i in range(1, n_questions + 1)
    ]
    path = make_temp_csv(rows)
    ak = load_answer_key(path)
    cleanup(path)
    return ak


# ═══════════════════════════════════════════════════════════
#  TC_STU_01: Nạp file bài làm chuẩn — số lượng và thứ tự đúng
# ═══════════════════════════════════════════════════════════

def test_load_valid_students():
    print_header("TC_STU_01: Nạp file bài làm hợp lệ — số lượng và thứ tự")
    print("Mục tiêu: Số bản ghi đọc về khớp số dòng, thứ tự giữ nguyên theo CSV.")
    print_separator("-")

    rows = [
        {"exam_id": "EXAM001", "mssv": "20230001", "ho_ten": "Nguyen Van A",
         "id_lop_hp": "163613", "ma_lop": "23D1", "ten_lop": "Toan Tin K68 - Nhom 1",
         "q1": "A", "q2": "C", "q3": "B"},
        {"exam_id": "EXAM001", "mssv": "20230002", "ho_ten": "Tran Thi B",
         "id_lop_hp": "163613", "ma_lop": "23D1", "ten_lop": "Toan Tin K68 - Nhom 1",
         "q1": "B", "q2": "A", "q3": "D"},
        {"exam_id": "EXAM001", "mssv": "20230003", "ho_ten": "Le Van C",
         "id_lop_hp": "163614", "ma_lop": "23D2", "ten_lop": "Toan Tin K68 - Nhom 2",
         "q1": "C", "q2": "B", "q3": "A"},
    ]
    path = make_temp_csv(rows)

    t0 = time.perf_counter()
    students = load_students(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    print_result("Đầu vào", "3 sinh viên, 2 lớp học phần, 3 câu hỏi")
    print_result("Kiểu trả về", type(students).__name__, "List")
    print_result("Số bản ghi", len(students), 3)
    print_result("SV đầu tiên MSSV", students.get(0).student_id, "20230001")
    print_result("SV cuối MSSV", students.get(2).student_id, "20230003")
    print_result("Thứ tự giữ nguyên", students.get(1).student_id, "20230002")
    print_result("class_id SV1", students.get(0).class_id, "163613")
    print_result("admin_class SV3", students.get(2).admin_class_id, "23D2")

    ok = (
        isinstance(students, List)
        and len(students) == 3
        and students.get(0).student_id == "20230001"
        and students.get(1).student_id == "20230002"
        and students.get(2).student_id == "20230003"
        and students.get(0).class_id == "163613"
        and students.get(2).admin_class_id == "23D2"
    )
    return assert_pass(ok, "nạp đúng số lượng và thứ tự", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_02: Đọc đáp án từ các cột q1, q2, ... đúng khóa
# ═══════════════════════════════════════════════════════════

def test_load_answers_mapping():
    print_header("TC_STU_02: Ánh xạ cột q1/q2/q3 sang khóa '1'/'2'/'3'")
    print("Mục tiêu: Cột 'q1' được ánh xạ thành key '1' trong student.answers.")
    print_separator("-")

    rows = [{"exam_id": "EXAM001", "mssv": "SV001", "ho_ten": "Test",
             "q1": "A", "q2": "C", "q3": "B"}]
    path = make_temp_csv(rows)

    t0 = time.perf_counter()
    students = load_students(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    sv = students.get(0)
    print_result("Đầu vào", "q1=A, q2=C, q3=B")
    print_result("get_answer('1')", sv.get_answer("1"), "A")
    print_result("get_answer('2')", sv.get_answer("2"), "C")
    print_result("get_answer('3')", sv.get_answer("3"), "B")
    print_result("get_answer('99')", sv.get_answer("99"), "'' (rỗng)")
    print_result("Cột không phải q*", "không bị đọc nhầm")

    ok = (
        sv.get_answer("1") == "A"
        and sv.get_answer("2") == "C"
        and sv.get_answer("3") == "B"
        and sv.get_answer("99") == ""
    )
    return assert_pass(ok, "ánh xạ cột qN → key N đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_03: File bài làm rỗng (chỉ có header)
# ═══════════════════════════════════════════════════════════

def test_load_empty_students_file():
    print_header("TC_STU_03: File bài làm rỗng (chỉ có header)")
    print("Mục tiêu: Trả về List rỗng, không crash, không ném ngoại lệ.")
    print_separator("-")

    path = make_temp_csv(
        [],
        fieldnames=["exam_id", "mssv", "ho_ten", "q1", "q2"]
    )

    t0 = time.perf_counter()
    students = load_students(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    print_result("Đầu vào", "File CSV không có dòng dữ liệu")
    print_result("Kiểu trả về", type(students).__name__, "List")
    print_result("Số bản ghi", len(students), 0)
    print_result("is_empty()", students.is_empty(), True)
    print_result("Có crash không", "Không")

    ok = isinstance(students, List) and len(students) == 0 and students.is_empty()
    return assert_pass(ok, "file rỗng trả về List rỗng an toàn", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_04: validate_students_csv — thiếu cột MSSV
# ═══════════════════════════════════════════════════════════

def test_validate_missing_id_column():
    print_header("TC_STU_04: validate_students_csv() — thiếu cột MSSV")
    print("Mục tiêu: Phát hiện thiếu cột MSSV, liệt kê đúng các tên cột hợp lệ.")
    print_separator("-")

    path = make_temp_csv(
        [{"ho_ten": "Test", "q1": "A"}],
        fieldnames=["ho_ten", "q1"]
    )

    t0 = time.perf_counter()
    errors = validate_students_csv(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    mssv_error = next((e for e in errors if "MSSV" in e or "mssv" in e.lower()), None)
    cols_mentioned = all(col in (mssv_error or "") for col in STUDENT_ID_COLUMNS)

    print_result("Đầu vào", "File chỉ có: ho_ten, q1")
    print_result("Số lỗi phát hiện", len(errors), ">= 1")
    print_result("Có lỗi MSSV", mssv_error is not None, True)
    print_result("Liệt kê cột hợp lệ", cols_mentioned, True)
    if mssv_error:
        print_result("Nội dung lỗi", mssv_error)

    ok = len(errors) >= 1 and mssv_error is not None and cols_mentioned
    return assert_pass(ok, "phát hiện thiếu cột MSSV đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_05: validate_students_csv — thiếu cột họ tên
# ═══════════════════════════════════════════════════════════

def test_validate_missing_name_column():
    print_header("TC_STU_05: validate_students_csv() — thiếu cột họ tên")
    print("Mục tiêu: Phát hiện thiếu cột họ tên, liệt kê đúng các tên cột hợp lệ.")
    print_separator("-")

    path = make_temp_csv(
        [{"mssv": "SV001", "q1": "A"}],
        fieldnames=["mssv", "q1"]
    )

    t0 = time.perf_counter()
    errors = validate_students_csv(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    name_error = next((e for e in errors if "họ tên" in e or "ho_ten" in e.lower()), None)
    cols_mentioned = all(col in (name_error or "") for col in STUDENT_NAME_COLUMNS)

    print_result("Đầu vào", "File chỉ có: mssv, q1")
    print_result("Số lỗi phát hiện", len(errors), ">= 1")
    print_result("Có lỗi họ tên", name_error is not None, True)
    print_result("Liệt kê cột hợp lệ", cols_mentioned, True)
    if name_error:
        print_result("Nội dung lỗi", name_error)

    ok = len(errors) >= 1 and name_error is not None and cols_mentioned
    return assert_pass(ok, "phát hiện thiếu cột họ tên đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_06: validate_students_csv — thiếu cột đáp án
# ═══════════════════════════════════════════════════════════

def test_validate_missing_answer_columns():
    print_header("TC_STU_06: validate_students_csv() — thiếu cột đáp án q*")
    print("Mục tiêu: Phát hiện không có cột nào dạng q1, q2, ...")
    print_separator("-")

    path = make_temp_csv(
        [{"mssv": "SV001", "ho_ten": "Test", "diem": "8"}],
        fieldnames=["mssv", "ho_ten", "diem"]
    )

    t0 = time.perf_counter()
    errors = validate_students_csv(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    answer_error = next((e for e in errors if "q1" in e or "đáp án" in e), None)

    print_result("Đầu vào", "File chỉ có: mssv, ho_ten, diem")
    print_result("Số lỗi phát hiện", len(errors), ">= 1")
    print_result("Có lỗi cột đáp án", answer_error is not None, True)
    if answer_error:
        print_result("Nội dung lỗi", answer_error)

    ok = len(errors) >= 1 and answer_error is not None
    return assert_pass(ok, "phát hiện thiếu cột đáp án đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_07: validate_students_csv — thiếu cả 3 loại cột
# ═══════════════════════════════════════════════════════════

def test_validate_missing_all_columns():
    print_header("TC_STU_07: validate_students_csv() — thiếu cả 3 loại cột")
    print("Mục tiêu: Trả về đủ 3 lỗi riêng biệt, không dừng ở lỗi đầu tiên.")
    print_separator("-")

    path = make_temp_csv(
        [{"ngay_thi": "2025-01-01", "phong_thi": "A101"}],
        fieldnames=["ngay_thi", "phong_thi"]
    )

    t0 = time.perf_counter()
    errors = validate_students_csv(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    has_mssv_err  = any("MSSV" in e or "mssv" in e.lower() for e in errors)
    has_name_err  = any("họ tên" in e or "ho_ten" in e.lower() for e in errors)
    has_ans_err   = any("q1" in e or "đáp án" in e for e in errors)

    print_result("Đầu vào", "File chỉ có: ngay_thi, phong_thi")
    print_result("Tổng số lỗi", len(errors), 3)
    print_result("Có lỗi MSSV", has_mssv_err, True)
    print_result("Có lỗi họ tên", has_name_err, True)
    print_result("Có lỗi đáp án", has_ans_err, True)
    print()
    for i, e in enumerate(errors, 1):
        print(f"    Lỗi {i}: {e}")
    print()

    ok = len(errors) == 3 and has_mssv_err and has_name_err and has_ans_err
    return assert_pass(ok, "phát hiện đủ 3 lỗi độc lập", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_08: Thiếu giá trị trong dòng — vẫn nạp, trường để rỗng
# ═══════════════════════════════════════════════════════════

def test_load_students_missing_values_in_row():
    print_header("TC_STU_08: Dòng thiếu giá trị — nạp được, trường để rỗng")
    print("Mục tiêu: validate_students_csv chỉ kiểm tra cột, không kiểm tra nội dung.")
    print_separator("-")

    # Dòng 1: thiếu họ tên (cột tồn tại nhưng giá trị rỗng)
    # Dòng 2: thiếu q2 (cột tồn tại nhưng rỗng)
    rows = [
        {"mssv": "SV001", "ho_ten": "",    "q1": "A", "q2": "B"},
        {"mssv": "SV002", "ho_ten": "Test", "q1": "C", "q2": ""},
    ]
    path = make_temp_csv(rows)

    t0 = time.perf_counter()
    validate_errors = validate_students_csv(path)
    students = load_students(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    sv1 = students.get(0)
    sv2 = students.get(1)

    print_result("Đầu vào", "Dòng 1: ho_ten rỗng; Dòng 2: q2 rỗng")
    print_result("Lỗi validate_csv", len(validate_errors), 0)
    print_result("Số SV nạp được", len(students), 2)
    print_result("SV1 student_name", repr(sv1.student_name), "'' hoặc fallback")
    print_result("SV2 get_answer('2')", repr(sv2.get_answer("2")), "''")
    print_result("SV2 get_answer('1')", sv2.get_answer("1"), "C")

    ok = (
        len(validate_errors) == 0
        and len(students) == 2
        and sv2.get_answer("2") == ""
        and sv2.get_answer("1") == "C"
    )
    return assert_pass(ok, "dòng thiếu giá trị được nạp, trường để rỗng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_09: Bài làm chứa mã đề không có đáp án
# ═══════════════════════════════════════════════════════════

def test_student_with_unknown_exam_id():
    print_header("TC_STU_09: Bài làm chứa mã đề không có đáp án tương ứng")
    print("Mục tiêu: validate_grading_inputs() báo lỗi từng sinh viên bị ảnh hưởng.")
    print_separator("-")

    answer_key = make_answer_key("EXAM001", n_questions=3)

    rows = [
        {"exam_id": "EXAM001",  "mssv": "SV001", "ho_ten": "Nguyen A", "q1": "A", "q2": "B", "q3": "C"},
        {"exam_id": "EXAM_RAC", "mssv": "SV002", "ho_ten": "Tran B",   "q1": "A", "q2": "B", "q3": "C"},
        {"exam_id": "EXAM_RAC", "mssv": "SV003", "ho_ten": "Le C",     "q1": "D", "q2": "A", "q3": "B"},
    ]
    path = make_temp_csv(rows)

    t0 = time.perf_counter()
    students = load_students(path)
    errors = validate_grading_inputs(answer_key, students)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    sv002_err = any("SV002" in e for e in errors)
    sv003_err = any("SV003" in e for e in errors)
    sv001_ok  = not any("SV001" in e for e in errors)

    print_result("Đầu vào", "SV001: EXAM001 (hợp lệ), SV002+SV003: EXAM_RAC (không có đáp án)")
    print_result("Tổng số lỗi", len(errors), 2)
    print_result("Có lỗi cho SV002", sv002_err, True)
    print_result("Có lỗi cho SV003", sv003_err, True)
    print_result("SV001 không bị lỗi", sv001_ok, True)
    for e in errors:
        print(f"    → {e}")
    print()

    ok = len(errors) == 2 and sv002_err and sv003_err and sv001_ok
    return assert_pass(ok, "báo lỗi đúng từng sinh viên có mã đề rác", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_10: Trùng MSSV trong cùng kỳ thi — bị từ chối
# ═══════════════════════════════════════════════════════════

def test_duplicate_student_id_same_exam():
    print_header("TC_STU_10: Trùng MSSV trong cùng kỳ thi — bị từ chối")
    print("Mục tiêu: validate_grading_inputs() báo lỗi; grade_all() ném ValueError.")
    print_separator("-")

    answer_key = make_answer_key("EXAM001", n_questions=2)

    rows = [
        {"exam_id": "EXAM001", "mssv": "20210000", "ho_ten": "Nguyen A", "q1": "A", "q2": "B"},
        {"exam_id": "EXAM001", "mssv": "20210000", "ho_ten": "Nguyen A", "q1": "C", "q2": "D"},
    ]
    path = make_temp_csv(rows)

    t0 = time.perf_counter()
    students = load_students(path)
    validate_errors = validate_grading_inputs(answer_key, students)
    elapsed_validate = time.perf_counter() - t0
    cleanup(path)

    has_dup_error = any("20210000" in e and "Trùng" in e for e in validate_errors)

    # grade_all() phải ném ValueError khi gọi thẳng
    grade_all_error = None
    t1 = time.perf_counter()
    try:
        grade_all(students, answer_key)
    except ValueError as e:
        grade_all_error = str(e)
    elapsed_grade = time.perf_counter() - t1

    print_result("Đầu vào", "2 dòng cùng MSSV 20210000, cùng EXAM001")
    print_subheader("Kiểm tra validate_grading_inputs()")
    print_result("Số lỗi validate", len(validate_errors), ">= 1")
    print_result("Lỗi đề cập MSSV", has_dup_error, True)
    if validate_errors:
        print_result("Nội dung lỗi", validate_errors[0])

    print_subheader("Kiểm tra grade_all() gọi trực tiếp")
    print_result("Ném ValueError", grade_all_error is not None, True)
    if grade_all_error:
        print_result("Nội dung lỗi", grade_all_error[:60] + "...")

    elapsed = elapsed_validate + elapsed_grade
    ok = has_dup_error and grade_all_error is not None
    return assert_pass(ok, "trùng MSSV bị từ chối ở cả validate và grade_all", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_11: Cùng MSSV ở hai kỳ thi khác nhau — hợp lệ
# ═══════════════════════════════════════════════════════════

def test_same_student_id_different_exams():
    print_header("TC_STU_11: Cùng MSSV ở hai kỳ thi khác nhau — hợp lệ")
    print("Mục tiêu: Key lưu là 'exam_id|student_id' nên khác kỳ thi là không trùng.")
    print_separator("-")

    rows_ak = [
        {"exam_id": "EXAM001", "question_id": "1", "correct_answer": "A"},
        {"exam_id": "EXAM002", "question_id": "1", "correct_answer": "B"},
    ]
    ak_path = make_temp_csv(rows_ak)
    answer_key = load_answer_key(ak_path)
    cleanup(ak_path)

    rows = [
        {"exam_id": "EXAM001", "mssv": "SV001", "ho_ten": "Nguyen A", "q1": "A"},
        {"exam_id": "EXAM002", "mssv": "SV001", "ho_ten": "Nguyen A", "q1": "B"},
    ]
    path = make_temp_csv(rows)

    t0 = time.perf_counter()
    students = load_students(path)
    errors = validate_grading_inputs(answer_key, students)
    results = grade_all(students, answer_key) if not errors else None
    elapsed = time.perf_counter() - t0
    cleanup(path)

    print_result("Đầu vào", "SV001 tham gia EXAM001 và EXAM002")
    print_result("Số lỗi validate", len(errors), 0)
    print_result("grade_all thành công", results is not None, True)
    if results:
        print_result("Số kết quả", len(results), 2)

    ok = len(errors) == 0 and results is not None and len(results) == 2
    return assert_pass(ok, "cùng MSSV khác kỳ thi được chấm bình thường", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_12: Nhận diện cột MSSV / họ tên theo alias
# ═══════════════════════════════════════════════════════════

def test_column_alias_recognition():
    print_header("TC_STU_12: Nhận diện cột MSSV và họ tên theo các tên cột thay thế")
    print("Mục tiêu: student_id / full_name / name được đọc đúng như mssv / ho_ten.")
    print_separator("-")

    cases = [
        ("student_id + student_name", {"student_id": "SV001", "student_name": "Test A", "q1": "A"}),
        ("student_code + name",       {"student_code": "SV002", "name": "Test B", "q1": "B"}),
        ("student_id + full_name",    {"student_id": "SV003", "full_name": "Test C", "q1": "C"}),
    ]

    all_ok = True
    t0 = time.perf_counter()

    for label, row_data in cases:
        path = make_temp_csv([row_data])
        validate_errors = validate_students_csv(path)
        students = load_students(path)
        cleanup(path)

        sv = students.get(0) if len(students) > 0 else None
        id_ok   = sv is not None and sv.student_id != ""
        name_ok = sv is not None and sv.student_name != ""
        val_ok  = len(validate_errors) == 0

        status = "✓" if (id_ok and name_ok and val_ok) else "✗"
        print(f"    {status}  {label:<30} | id={sv.student_id!r}, name={sv.student_name!r}")
        if not (id_ok and name_ok and val_ok):
            all_ok = False

    elapsed = time.perf_counter() - t0
    print()
    return assert_pass(all_ok, "tất cả alias cột được nhận diện đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STU_13: Giá trị đáp án được chuẩn hóa khi nạp
# ═══════════════════════════════════════════════════════════

def test_student_answers_normalized():
    print_header("TC_STU_13: Đáp án sinh viên được chuẩn hóa strip() + upper()")
    print("Mục tiêu: Đáp án 'a', '  B  ', 'c' đều được chuẩn hóa trước khi so sánh.")
    print_separator("-")

    rows = [{"exam_id": "EXAM001", "mssv": "SV001", "ho_ten": "Test",
             "q1": "  a  ", "q2": "b", "q3": "  C"}]
    path = make_temp_csv(rows)

    t0 = time.perf_counter()
    students = load_students(path)
    elapsed = time.perf_counter() - t0
    cleanup(path)

    sv = students.get(0)
    print_result("Đầu vào q1", "'  a  '  →", sv.get_answer("1"))
    print_result("Đầu vào q2", "'b'       →", sv.get_answer("2"))
    print_result("Đầu vào q3", "'  C'     →", sv.get_answer("3"))

    ok = (
        sv.get_answer("1") == "A"
        and sv.get_answer("2") == "B"
        and sv.get_answer("3") == "C"
    )
    return assert_pass(ok, "đáp án sinh viên được chuẩn hóa đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  Hàm main
# ═══════════════════════════════════════════════════════════

def run_all():
    tests = [
        test_load_valid_students,
        test_load_answers_mapping,
        test_load_empty_students_file,
        test_validate_missing_id_column,
        test_validate_missing_name_column,
        test_validate_missing_answer_columns,
        test_validate_missing_all_columns,
        test_load_students_missing_values_in_row,
        test_student_with_unknown_exam_id,
        test_duplicate_student_id_same_exam,
        test_same_student_id_different_exams,
        test_column_alias_recognition,
        test_student_answers_normalized,
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
            import traceback
            print(f"  [-] Trạng thái: ❌ ERROR — {type(e).__name__}: {e}")
            traceback.print_exc()
            print()
            failed += 1
    t_total = time.perf_counter() - t_total_start

    print_separator("=")
    print(f"  KẾT QUẢ TỔNG HỢP — PHẦN 2: QUẢN LÝ BÀI LÀM SINH VIÊN")
    print_separator("-")
    print(f"  Tổng số test case : {len(tests)}")
    print(f"  ✅ Passed          : {passed}")
    print(f"  ❌ Failed          : {failed}")
    print(f"  Tổng thời gian    : {t_total:.6f} giây")
    print_separator("=")


if __name__ == "__main__":
    run_all()