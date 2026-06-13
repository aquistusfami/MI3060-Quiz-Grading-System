# test_part4_business.py
# Kiểm thử nghiệp vụ Phần 4: Thống kê & Xuất Báo cáo
# Chạy: python test_part4_business.py

import csv
import os
import sys
import time
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_logic import (
    load_answer_key,
    load_students,
    grade_all,
    compute_question_stats,
    get_question_stats_items,
    get_hardest_questions,
    export_results_csv,
    export_question_stats_csv,
    build_class_summary,
    get_ranking,
    get_results_by_class,
    get_results_by_exam,
    get_exam_ids,
    get_class_names,
)


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
        print(f"  [*] {label:<26}: {value}  (kỳ vọng: {expected})")
    else:
        print(f"  [*] {label:<26}: {value}")

def print_pass(elapsed: float):
    print(f"  [*] Thời gian              : {elapsed:.6f} giây")
    print(f"  [+] Trạng thái            : ✅ PASS")
    print()

def print_fail(elapsed: float, reason: str):
    print(f"  [*] Thời gian              : {elapsed:.6f} giây")
    print(f"  [-] Trạng thái            : ❌ FAIL — {reason}")
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

def make_temp_path(suffix=".csv") -> str:
    """Tạo đường dẫn file tạm chưa tạo — dùng cho output."""
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.close()
    os.unlink(tmp.name)
    return tmp.name

def cleanup(*paths):
    for p in paths:
        try:
            os.unlink(p)
        except OSError:
            pass

def setup_full(
    n_questions: int,
    correct_answers: list[str],
    students_data: list[dict],   # [{mssv, ho_ten, class_id, class_name, answers:[...]}, ...]
    exam_id: str = "EXAM001",
):
    """
    Tạo answer_key và students đầy đủ (có class_id, class_name).
    Trả về (answer_key, students, ans_path, stu_path).
    """
    ans_rows = [
        {"exam_id": exam_id, "question_id": str(i + 1),
         "correct_answer": correct_answers[i]}
        for i in range(n_questions)
    ]
    ans_path = make_temp_csv(ans_rows)

    q_cols = [f"q{i + 1}" for i in range(n_questions)]
    stu_rows = []
    for sv in students_data:
        row = {
            "exam_id": exam_id,
            "mssv": sv["mssv"],
            "ho_ten": sv["ho_ten"],
            "id_lop_hp": sv.get("class_id", ""),
            "ten_lop": sv.get("class_name", ""),
        }
        for col, ans in zip(q_cols, sv["answers"]):
            row[col] = ans
        for col in q_cols[len(sv["answers"]):]:
            row[col] = ""
        stu_rows.append(row)

    stu_path = make_temp_csv(stu_rows)
    answer_key = load_answer_key(ans_path)
    students   = load_students(stu_path)
    return answer_key, students, ans_path, stu_path


# ═══════════════════════════════════════════════════════════
#  TC_STAT_01: compute_question_stats — đếm đúng/sai từng câu
# ═══════════════════════════════════════════════════════════

def test_question_stats_correct_wrong_count():
    print_header("TC_STAT_01: compute_question_stats() — đếm đúng/sai từng câu")
    print("Mục tiêu: Số người đúng và tổng lượt trả lời khớp dữ liệu thực tế.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_full(
        3, ["A", "B", "C"],
        [
            {"mssv": "SV001", "ho_ten": "A", "answers": ["A", "B", "X"]},
            {"mssv": "SV002", "ho_ten": "B", "answers": ["A", "X", "C"]},
            {"mssv": "SV003", "ho_ten": "C", "answers": ["X", "X", "X"]},
        ],
    )

    t0 = time.perf_counter()
    stats = compute_question_stats(students, answer_key)
    elapsed = time.perf_counter() - t0
    cleanup(p1, p2)

    items = get_question_stats_items(stats)
    q1 = next((x for x in items if x["question_id"] == "1"), None)
    q2 = next((x for x in items if x["question_id"] == "2"), None)
    q3 = next((x for x in items if x["question_id"] == "3"), None)

    print_result("Số câu trong thống kê", len(items), 3)
    print_result("Câu 1 — đúng / tổng", f"{q1['correct']} / {q1['total']}" if q1 else "—", "2 / 3")
    print_result("Câu 2 — đúng / tổng", f"{q2['correct']} / {q2['total']}" if q2 else "—", "1 / 3")
    print_result("Câu 3 — đúng / tổng", f"{q3['correct']} / {q3['total']}" if q3 else "—", "1 / 3")

    ok = (
        len(items) == 3
        and q1 and q1["correct"] == 2 and q1["total"] == 3
        and q2 and q2["correct"] == 1 and q2["total"] == 3
        and q3 and q3["correct"] == 1 and q3["total"] == 3
    )
    return assert_pass(ok, "đếm đúng/sai từng câu chính xác", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STAT_02: Tỷ lệ đúng từng câu tính đúng
# ═══════════════════════════════════════════════════════════

def test_question_stats_accuracy_rate():
    print_header("TC_STAT_02: Tỷ lệ đúng từng câu — tính đúng và làm tròn 1 chữ số")
    print("Mục tiêu: rate = round(correct/total*100, 1) cho từng câu hỏi.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_full(
        3, ["A", "B", "C"],
        [
            {"mssv": "SV001", "ho_ten": "A", "answers": ["A", "B", "X"]},
            {"mssv": "SV002", "ho_ten": "B", "answers": ["A", "B", "X"]},
            {"mssv": "SV003", "ho_ten": "C", "answers": ["A", "X", "X"]},
            {"mssv": "SV004", "ho_ten": "D", "answers": ["X", "X", "X"]},
        ],
    )

    t0 = time.perf_counter()
    stats = compute_question_stats(students, answer_key)
    elapsed = time.perf_counter() - t0
    cleanup(p1, p2)

    items = get_question_stats_items(stats)
    q1 = next((x for x in items if x["question_id"] == "1"), None)
    q2 = next((x for x in items if x["question_id"] == "2"), None)
    q3 = next((x for x in items if x["question_id"] == "3"), None)

    rate1 = round(q1["correct"] / q1["total"] * 100, 1) if q1 and q1["total"] else None
    rate2 = round(q2["correct"] / q2["total"] * 100, 1) if q2 and q2["total"] else None
    rate3 = round(q3["correct"] / q3["total"] * 100, 1) if q3 and q3["total"] else None

    print_result("Câu 1 — tỷ lệ đúng", f"{rate1}%", "75.0%")
    print_result("Câu 2 — tỷ lệ đúng", f"{rate2}%", "50.0%")
    print_result("Câu 3 — tỷ lệ đúng", f"{rate3}%", "0.0%")

    ok = rate1 == 75.0 and rate2 == 50.0 and rate3 == 0.0
    return assert_pass(ok, "tỷ lệ đúng tính chính xác", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STAT_03: get_hardest_questions() — câu khó nhất đầu tiên
# ═══════════════════════════════════════════════════════════

def test_hardest_questions():
    print_header("TC_STAT_03: get_hardest_questions() — top câu có tỷ lệ đúng thấp nhất")
    print("Mục tiêu: Dùng MinHeap, trả về n câu khó nhất theo tỷ lệ đúng tăng dần.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_full(
        4, ["A", "A", "A", "A"],
        [
            {"mssv": "SV001", "ho_ten": "A", "answers": ["A", "A", "A", "X"]},
            {"mssv": "SV002", "ho_ten": "B", "answers": ["A", "A", "X", "X"]},
            {"mssv": "SV003", "ho_ten": "C", "answers": ["A", "X", "X", "X"]},
            {"mssv": "SV004", "ho_ten": "D", "answers": ["A", "X", "X", "X"]},
        ],
    )
    stats = compute_question_stats(students, answer_key)
    cleanup(p1, p2)

    t0 = time.perf_counter()
    hardest3 = get_hardest_questions(stats, n=3)
    elapsed  = time.perf_counter() - t0

    rates = [h[4] for h in hardest3]
    qids  = [h[1] for h in hardest3]

    print_result("Số câu yêu cầu (n=3)", 3)
    print_result("Số câu trả về", len(hardest3), 3)
    print_result("Tỷ lệ đúng câu khó nhất", f"{rates[0]}%", "0.0%")
    print_result("Tỷ lệ đúng câu thứ 2", f"{rates[1]}%", "25.0%")
    print_result("Tỷ lệ đúng câu thứ 3", f"{rates[2]}%", "50.0%")
    print_result("Câu khó nhất ID", qids[0], "4")
    is_asc = all(rates[i] <= rates[i + 1] for i in range(len(rates) - 1))
    print_result("Sắp xếp tỷ lệ tăng dần", is_asc, True)

    ok = (
        len(hardest3) == 3
        and rates[0] == 0.0
        and rates[1] == 25.0
        and rates[2] == 50.0
        and is_asc
    )
    return assert_pass(ok, "top câu khó được xếp theo tỷ lệ đúng tăng dần", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STAT_04: get_hardest_questions() — n lớn hơn số câu hỏi
# ═══════════════════════════════════════════════════════════

def test_hardest_questions_n_exceeds():
    print_header("TC_STAT_04: get_hardest_questions(n) khi n > số câu — trả hết")
    print("Mục tiêu: Không crash khi yêu cầu top-10 nhưng chỉ có 3 câu hỏi.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_full(
        3, ["A", "B", "C"],
        [{"mssv": "SV001", "ho_ten": "A", "answers": ["A", "X", "X"]}],
    )
    stats = compute_question_stats(students, answer_key)
    cleanup(p1, p2)

    t0 = time.perf_counter()
    result = get_hardest_questions(stats, n=10)
    elapsed = time.perf_counter() - t0

    print_result("Số câu hỏi thực tế", 3)
    print_result("n yêu cầu", 10)
    print_result("Số câu trả về", len(result), 3)
    print_result("Có crash không", "Không")

    ok = len(result) == 3
    return assert_pass(ok, "n > số câu không crash, trả về tất cả câu", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STAT_05: export_results_csv() — file tạo được, đủ cột, đúng dữ liệu
# ═══════════════════════════════════════════════════════════

def test_export_results_csv():
    print_header("TC_STAT_05: export_results_csv() — tạo file CSV đúng chuẩn")
    print("Mục tiêu: File tồn tại, đủ 11 cột, dữ liệu khớp kết quả chấm điểm.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_full(
        3, ["A", "B", "C"],
        [
            {"mssv": "SV001", "ho_ten": "Nguyen Van A",
             "class_id": "163613", "class_name": "Lop 1", "answers": ["A", "B", "C"]},
            {"mssv": "SV002", "ho_ten": "Tran Thi B",
             "class_id": "163613", "class_name": "Lop 1", "answers": ["A", "X", "X"]},
        ],
    )
    results  = grade_all(students, answer_key)
    out_path = make_temp_path(".csv")
    cleanup(p1, p2)

    t0 = time.perf_counter()
    export_results_csv(results, out_path)
    elapsed = time.perf_counter() - t0

    file_exists = os.path.exists(out_path)
    rows = []
    header = []
    if file_exists:
        with open(out_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows   = list(reader)
    cleanup(out_path)

    expected_cols = ["Hạng", "Kỳ thi", "MSSV", "Họ tên", "ID lớp HP",
                     "Mã lớp SV", "Tên lớp SV", "Điểm", "Số câu đúng",
                     "Tổng số câu", "Tỷ lệ (%)"]

    print_result("File tồn tại", file_exists, True)
    print_result("Số cột header", len(header), 11)
    print_result("Tên cột đúng", header == expected_cols, True)
    print_result("Số dòng dữ liệu", len(rows), 2)

    if rows:
        rank_col  = header.index("Hạng")
        score_col = header.index("Điểm")
        mssv_col  = header.index("MSSV")
        print_result("Hạng 1 MSSV", rows[0][mssv_col], "SV001")
        print_result("Hạng 1 Điểm", rows[0][score_col], "10.0")
        print_result("Hạng 2 MSSV", rows[1][mssv_col], "SV002")

    ok = (
        file_exists
        and header == expected_cols
        and len(rows) == 2
        and rows[0][mssv_col] == "SV001"
        and rows[0][score_col] == "10.0"
    )
    return assert_pass(ok, "file xuất đúng định dạng và nội dung", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STAT_06: export_results_csv() — sắp xếp theo điểm giảm dần
# ═══════════════════════════════════════════════════════════

def test_export_results_sorted_by_score():
    print_header("TC_STAT_06: export_results_csv() — file được sắp xếp theo điểm giảm dần")
    print("Mục tiêu: Hạng 1 là người điểm cao nhất, hàng cuối là người thấp nhất.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_full(
        10, ["A"] * 10,
        [
            {"mssv": "SV001", "ho_ten": "A", "answers": ["A"]*3 + ["X"]*7},
            {"mssv": "SV002", "ho_ten": "B", "answers": ["A"]*9 + ["X"]*1},
            {"mssv": "SV003", "ho_ten": "C", "answers": ["A"]*6 + ["X"]*4},
        ],
    )
    results  = grade_all(students, answer_key)
    out_path = make_temp_path(".csv")
    cleanup(p1, p2)

    t0 = time.perf_counter()
    export_results_csv(results, out_path)
    elapsed = time.perf_counter() - t0

    with open(out_path, encoding="utf-8-sig", newline="") as f:
        reader  = csv.reader(f)
        header  = next(reader)
        rows    = list(reader)
    cleanup(out_path)

    mssv_col  = header.index("MSSV")
    score_col = header.index("Điểm")
    scores    = [float(r[score_col]) for r in rows]
    is_desc   = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))

    print_result("Thứ tự MSSV trong file", [r[mssv_col] for r in rows])
    print_result("Điểm trong file", scores)
    print_result("Sắp xếp giảm dần", is_desc, True)
    print_result("MSSV hạng 1", rows[0][mssv_col], "SV002")

    ok = is_desc and rows[0][mssv_col] == "SV002"
    return assert_pass(ok, "file xuất sắp xếp đúng thứ hạng", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STAT_07: export_results_csv() — encoding utf-8-sig
# ═══════════════════════════════════════════════════════════

def test_export_results_encoding():
    print_header("TC_STAT_07: export_results_csv() — encoding UTF-8 with BOM")
    print("Mục tiêu: File dùng utf-8-sig, đọc lại bằng utf-8-sig không bị lỗi font.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_full(
        2, ["A", "B"],
        [{"mssv": "SV001", "ho_ten": "Nguyễn Văn Ánh", "answers": ["A", "B"]}],
    )
    results  = grade_all(students, answer_key)
    out_path = make_temp_path(".csv")
    cleanup(p1, p2)

    t0 = time.perf_counter()
    export_results_csv(results, out_path)
    elapsed = time.perf_counter() - t0

    with open(out_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows   = list(reader)

    name_col = header.index("Họ tên")
    name_val = rows[0][name_col] if rows else ""
    cleanup(out_path)

    print_result("Cột đầu header", header[0], "Hạng")
    print_result("Họ tên đọc lại", name_val, "Nguyễn Văn Ánh")
    print_result("BOM gây lỗi cột đầu", header[0] != "Hạng", False)

    ok = header[0] == "Hạng" and name_val == "Nguyễn Văn Ánh"
    return assert_pass(ok, "encoding utf-8-sig đọc lại đúng tiếng Việt", elapsed)

# ═══════════════════════════════════════════════════════════
#  TC_STAT_08: export_question_stats_csv() — đủ cột, đúng dữ liệu
# ═══════════════════════════════════════════════════════════

def test_export_question_stats_csv():
    print_header("TC_STAT_08: export_question_stats_csv() — đúng cột và dữ liệu")
    print("Mục tiêu: File có 5 cột, tỷ lệ đúng tính đúng, câu sai = tổng - đúng.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_full(
        2, ["A", "B"],
        [
            {"mssv": "SV001", "ho_ten": "A", "answers": ["A", "B"]},
            {"mssv": "SV002", "ho_ten": "B", "answers": ["A", "X"]},
            {"mssv": "SV003", "ho_ten": "C", "answers": ["A", "X"]},
        ],
    )
    stats    = compute_question_stats(students, answer_key)
    out_path = make_temp_path(".csv")
    cleanup(p1, p2)

    t0 = time.perf_counter()
    export_question_stats_csv(stats, out_path)
    elapsed = time.perf_counter() - t0

    with open(out_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows   = list(reader)
    cleanup(out_path)

    expected_cols = ["Kỳ thi", "Câu hỏi", "Số người đúng", "Số người sai", "Tỷ lệ đúng (%)"]

    print_result("Số cột", len(header), 5)
    print_result("Tên cột đúng", header == expected_cols, True)
    print_result("Số dòng dữ liệu", len(rows), 2)

    row_q1 = next((r for r in rows if r[1] == "Cau 1"), None)
    row_q2 = next((r for r in rows if r[1] == "Cau 2"), None)
    if row_q1:
        print_result("Câu 1 — đúng/sai/tỷ lệ",
                     f"{row_q1[2]} / {row_q1[3]} / {row_q1[4]}%", "3 / 0 / 100.0%")
    if row_q2:
        print_result("Câu 2 — đúng/sai/tỷ lệ",
                     f"{row_q2[2]} / {row_q2[3]} / {row_q2[4]}%", "1 / 2 / 33.3%")

    ok = (
        header == expected_cols
        and len(rows) == 2
        and row_q1 is not None and row_q1[2] == "3" and row_q1[3] == "0"
        and row_q2 is not None and row_q2[2] == "1" and row_q2[3] == "2"
    )
    return assert_pass(ok, "file thống kê câu hỏi đúng dữ liệu", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STAT_09: build_class_summary() — thống kê theo lớp học phần
# ═══════════════════════════════════════════════════════════

def test_build_class_summary():
    print_header("TC_STAT_09: build_class_summary() — tổng hợp theo lớp học phần")
    print("Mục tiêu: Điểm TB, tỷ lệ đạt, số SV tính đúng theo từng class_id.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_full(
        10, ["A"] * 10,
        [
            {"mssv": "SV001", "class_id": "163613", "class_name": "Lop A",
             "ho_ten": "A", "answers": ["A"]*10},           # 10.0
            {"mssv": "SV002", "class_id": "163613", "class_name": "Lop A",
             "ho_ten": "B", "answers": ["A"]*4 + ["X"]*6},  # 4.0
            {"mssv": "SV003", "class_id": "163614", "class_name": "Lop B",
             "ho_ten": "C", "answers": ["A"]*6 + ["X"]*4},  # 6.0
            {"mssv": "SV004", "class_id": "163614", "class_name": "Lop B",
             "ho_ten": "D", "answers": ["A"]*8 + ["X"]*2},  # 8.0
        ],
    )
    results = grade_all(students, answer_key)
    cleanup(p1, p2)

    t0 = time.perf_counter()
    summary = build_class_summary(results)
    elapsed = time.perf_counter() - t0

    cls_a = next((s for s in summary if s["class_id"] == "163613"), None)
    cls_b = next((s for s in summary if s["class_id"] == "163614"), None)

    print_subheader("Lớp 163613 (Lop A) — SV001=10.0, SV002=4.0")
    print_result("Số SV", cls_a["count"] if cls_a else "—", 2)
    print_result("Điểm TB", cls_a["average"] if cls_a else "—", 7.0)
    print_result("Tỷ lệ đạt (%)", cls_a["passing_rate"] if cls_a else "—", 50.0)

    print_subheader("Lớp 163614 (Lop B) — SV003=6.0, SV004=8.0")
    print_result("Số SV", cls_b["count"] if cls_b else "—", 2)
    print_result("Điểm TB", cls_b["average"] if cls_b else "—", 7.0)
    print_result("Tỷ lệ đạt (%)", cls_b["passing_rate"] if cls_b else "—", 100.0)

    ok = (
        cls_a is not None and cls_a["count"] == 2
        and cls_a["average"] == 7.0 and cls_a["passing_rate"] == 50.0
        and cls_b is not None and cls_b["count"] == 2
        and cls_b["average"] == 7.0 and cls_b["passing_rate"] == 100.0
    )
    return assert_pass(ok, "thống kê lớp học phần đúng số liệu", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STAT_10: get_results_by_class() — lọc đúng lớp, không ảnh hưởng lớp khác
# ═══════════════════════════════════════════════════════════

def test_filter_by_class():
    print_header("TC_STAT_10: get_results_by_class() — lọc kết quả theo lớp học phần")
    print("Mục tiêu: Chỉ trả sinh viên đúng class_id, class khác không bị lẫn.")
    print_separator("-")

    answer_key, students, p1, p2 = setup_full(
        3, ["A", "B", "C"],
        [
            {"mssv": "SV001", "class_id": "163613", "class_name": "LA",
             "ho_ten": "A", "answers": ["A", "B", "C"]},
            {"mssv": "SV002", "class_id": "163613", "class_name": "LA",
             "ho_ten": "B", "answers": ["A", "B", "C"]},
            {"mssv": "SV003", "class_id": "163614", "class_name": "LB",
             "ho_ten": "C", "answers": ["A", "B", "C"]},
        ],
    )
    results = grade_all(students, answer_key)
    ranking = get_ranking(results)
    cleanup(p1, p2)

    t0 = time.perf_counter()
    filtered    = get_results_by_class(ranking, "163613")
    all_results = get_results_by_class(ranking, "Tất cả")
    elapsed     = time.perf_counter() - t0

    ids_filtered = [r.student_id for r in filtered]

    print_result("Lọc lớp '163613'", ids_filtered)
    print_result("Số SV lớp 163613", len(filtered), 2)
    print_result("SV003 (163614) bị loại", "SV003" not in ids_filtered, True)
    print_result("Lọc 'Tất cả' — số SV", len(all_results), 3)

    ok = (
        len(filtered) == 2
        and "SV003" not in ids_filtered
        and len(all_results) == 3
    )
    return assert_pass(ok, "lọc lớp học phần không lẫn lớp khác", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STAT_11: get_results_by_exam() — lọc đúng kỳ thi
# ═══════════════════════════════════════════════════════════

def test_filter_by_exam():
    print_header("TC_STAT_11: get_results_by_exam() — lọc kết quả theo kỳ thi")
    print("Mục tiêu: Chỉ trả kết quả của exam_id được chọn, kỳ khác bị loại.")
    print_separator("-")

    ans_rows = (
        [{"exam_id": "EXAM001", "question_id": "1", "correct_answer": "A"}]
        + [{"exam_id": "EXAM002", "question_id": "1", "correct_answer": "B"}]
    )
    ans_path = make_temp_csv(ans_rows)
    answer_key = load_answer_key(ans_path)

    stu_rows = [
        {"exam_id": "EXAM001", "mssv": "SV001", "ho_ten": "A", "q1": "A"},
        {"exam_id": "EXAM001", "mssv": "SV002", "ho_ten": "B", "q1": "A"},
        {"exam_id": "EXAM002", "mssv": "SV003", "ho_ten": "C", "q1": "B"},
    ]
    stu_path = make_temp_csv(stu_rows)
    students = load_students(stu_path)
    results  = grade_all(students, answer_key)
    ranking  = get_ranking(results)
    cleanup(ans_path, stu_path)

    t0 = time.perf_counter()
    exam1_results = get_results_by_exam(ranking, "EXAM001")
    exam2_results = get_results_by_exam(ranking, "EXAM002")
    all_results   = get_results_by_exam(ranking, "Tất cả")
    elapsed       = time.perf_counter() - t0

    print_result("Lọc EXAM001 — số SV", len(exam1_results), 2)
    print_result("Lọc EXAM002 — số SV", len(exam2_results), 1)
    print_result("Lọc 'Tất cả' — số SV", len(all_results), 3)
    print_result("EXAM002 không lẫn vào EXAM001",
                 all(r.exam_id == "EXAM001" for r in exam1_results), True)

    ok = (
        len(exam1_results) == 2
        and len(exam2_results) == 1
        and len(all_results) == 3
        and all(r.exam_id == "EXAM001" for r in exam1_results)
    )
    return assert_pass(ok, "lọc kỳ thi chính xác", elapsed)


# ═══════════════════════════════════════════════════════════
#  TC_STAT_12: get_exam_ids() và get_class_names() — danh sách duy nhất đã sắp xếp
# ═══════════════════════════════════════════════════════════

def test_get_exam_ids_and_class_names():
    print_header("TC_STAT_12: get_exam_ids() và get_class_names() — duy nhất, đã sắp xếp")
    print("Mục tiêu: Không trùng lặp, sắp xếp tăng dần, dùng cho Combobox giao diện.")
    print_separator("-")

    ans_rows = [
        {"exam_id": "EXAM002", "question_id": "1", "correct_answer": "A"},
        {"exam_id": "EXAM001", "question_id": "1", "correct_answer": "B"},
    ]
    ans_path = make_temp_csv(ans_rows)
    answer_key = load_answer_key(ans_path)

    stu_rows = [
        {"exam_id": "EXAM001", "mssv": "SV001", "id_lop_hp": "163614",
         "ho_ten": "A", "q1": "B"},
        {"exam_id": "EXAM001", "mssv": "SV002", "id_lop_hp": "163613",
         "ho_ten": "B", "q1": "A"},
        {"exam_id": "EXAM002", "mssv": "SV003", "id_lop_hp": "163613",
         "ho_ten": "C", "q1": "A"},
        {"exam_id": "EXAM002", "mssv": "SV004", "id_lop_hp": "163613",
         "ho_ten": "D", "q1": "A"},
    ]
    stu_path = make_temp_csv(stu_rows)
    students = load_students(stu_path)
    results  = grade_all(students, answer_key)
    cleanup(ans_path, stu_path)

    t0 = time.perf_counter()
    exam_ids    = get_exam_ids(results)
    class_names = get_class_names(results)
    elapsed     = time.perf_counter() - t0

    print_result("exam_ids", exam_ids, ["EXAM001", "EXAM002"])
    print_result("Duy nhất", len(exam_ids) == len(set(exam_ids)), True)
    print_result("Sắp xếp tăng dần", exam_ids == sorted(exam_ids), True)
    print_result("class_names", class_names, ["163613", "163614"])
    print_result("class_names duy nhất", len(class_names) == len(set(class_names)), True)

    ok = (
        exam_ids == ["EXAM001", "EXAM002"]
        and class_names == ["163613", "163614"]
    )
    return assert_pass(ok, "danh sách kỳ thi và lớp duy nhất, sắp xếp đúng", elapsed)


# ═══════════════════════════════════════════════════════════
#  Hàm main
# ═══════════════════════════════════════════════════════════

def run_all():
    tests = [
        test_question_stats_correct_wrong_count,
        test_question_stats_accuracy_rate,
        test_hardest_questions,
        test_hardest_questions_n_exceeds,
        test_export_results_csv,
        test_export_results_sorted_by_score,
        test_export_results_encoding,
        test_export_question_stats_csv,
        test_build_class_summary,
        test_filter_by_class,
        test_filter_by_exam,
        test_get_exam_ids_and_class_names,
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
    print(f"  KẾT QUẢ TỔNG HỢP — PHẦN 4: THỐNG KÊ & XUẤT BÁO CÁO")
    print_separator("-")
    print(f"  Tổng số test case : {len(tests)}")
    print(f"  ✅ Passed          : {passed}")
    print(f"  ❌ Failed          : {failed}")
    print(f"  Tổng thời gian    : {t_total:.6f} giây")
    print_separator("=")


if __name__ == "__main__":
    run_all()