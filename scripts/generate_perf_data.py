import csv
import os
import random


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "performance")

RANDOM_SEED = 20260520
EXAM_COUNT = 5
QUESTION_COUNT = 100
STUDENT_COUNT = 10000

OPTIONS = ("A", "B", "C", "D")
FIRST_NAMES = (
    "An", "Binh", "Chi", "Dung", "Giang", "Ha", "Hieu", "Khanh", "Linh",
    "Long", "Mai", "Minh", "Nam", "Ngoc", "Phong", "Quang", "Son", "Thao",
    "Trang", "Tuan", "Vy",
)
MIDDLE_NAMES = ("Van", "Thi", "Hoang", "Duc", "Gia", "Thanh", "Quoc", "Bao")
LAST_NAMES = (
    "Nguyen", "Tran", "Le", "Pham", "Hoang", "Phan", "Vu", "Dang", "Bui",
    "Do", "Ho", "Ngo", "Duong", "Ly",
)

COURSES = [
    ("PERF001", "MI1111", "Giai tich 1", "Kiem tra trac nghiem Giai tich 1"),
    ("PERF002", "MI1141", "Dai so tuyen tinh", "Kiem tra trac nghiem Dai so tuyen tinh"),
    ("PERF003", "IT1110", "Tin hoc dai cuong", "Kiem tra trac nghiem Tin hoc dai cuong"),
    ("PERF004", "PH1120", "Vat ly dai cuong", "Kiem tra trac nghiem Vat ly dai cuong"),
    ("PERF005", "EM1010", "Kinh te hoc dai cuong", "Kiem tra trac nghiem Kinh te hoc dai cuong"),
]


def main():
    random.seed(RANDOM_SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    exam_rows = build_exams()
    answer_keys = build_answer_keys(exam_rows)
    student_rows = build_students(exam_rows, answer_keys)

    write_csv(
        os.path.join(OUTPUT_DIR, "exams.csv"),
        ["exam_id", "ma_hp", "ten_hp", "hoc_ky", "ten_ky_thi", "ngay_thi", "thoi_luong_phut", "ghi_chu"],
        exam_rows,
    )
    write_csv(
        os.path.join(OUTPUT_DIR, "answer_key.csv"),
        ["exam_id", "question_id", "correct_answer"],
        [
            {
                "exam_id": exam["exam_id"],
                "question_id": qid,
                "correct_answer": answer,
            }
            for exam in exam_rows
            for qid, answer in answer_keys[exam["exam_id"]].items()
        ],
    )
    write_csv(
        os.path.join(OUTPUT_DIR, "students.csv"),
        [
            "exam_id", "ma_hp", "hoc_ky", "id_lop_hp", "mssv", "ho_ten",
            "ma_lop", "ten_lop",
        ] + [f"q{i}" for i in range(1, QUESTION_COUNT + 1)],
        student_rows,
    )

    print(f"Generated {len(exam_rows)} exams")
    print(f"Generated {EXAM_COUNT * QUESTION_COUNT} answer-key rows")
    print(f"Generated {len(student_rows)} students")
    print(f"Output directory: {OUTPUT_DIR}")


def build_exams():
    exams = []
    for idx, (exam_id, course_code, course_name, exam_name) in enumerate(COURSES[:EXAM_COUNT], start=1):
        exams.append({
            "exam_id": exam_id,
            "ma_hp": course_code,
            "ten_hp": course_name,
            "hoc_ky": "20252",
            "ten_ky_thi": exam_name,
            "ngay_thi": f"2026-05-{10 + idx:02d}",
            "thoi_luong_phut": "60",
            "ghi_chu": f"Bo du lieu hieu nang, {QUESTION_COUNT} cau, nhieu lop hoc phan",
        })
    return exams


def build_answer_keys(exams):
    keys = {}
    for exam_index, exam in enumerate(exams):
        exam_key = {}
        for qid in range(1, QUESTION_COUNT + 1):
            exam_key[str(qid)] = OPTIONS[(qid + exam_index * 2) % len(OPTIONS)]
        keys[exam["exam_id"]] = exam_key
    return keys


def build_students(exams, answer_keys):
    rows = []
    classes_by_exam = build_classes(exams)

    for index in range(STUDENT_COUNT):
        exam = exams[index % len(exams)]
        class_info = classes_by_exam[exam["exam_id"]][(index // len(exams)) % len(classes_by_exam[exam["exam_id"]])]
        ability = clipped_gauss(0.72, 0.14, 0.32, 0.98)
        if index % 17 == 0:
            ability = clipped_gauss(0.48, 0.10, 0.20, 0.72)
        elif index % 23 == 0:
            ability = clipped_gauss(0.88, 0.06, 0.70, 0.99)

        row = {
            "exam_id": exam["exam_id"],
            "ma_hp": exam["ma_hp"],
            "hoc_ky": exam["hoc_ky"],
            "id_lop_hp": class_info["id_lop_hp"],
            "mssv": f"2026{index + 1:05d}",
            "ho_ten": make_student_name(index),
            "ma_lop": class_info["ma_lop"],
            "ten_lop": class_info["ten_lop"],
        }

        for qid in range(1, QUESTION_COUNT + 1):
            correct_answer = answer_keys[exam["exam_id"]][str(qid)]
            row[f"q{qid}"] = choose_student_answer(correct_answer, ability, qid)

        rows.append(row)

    return rows


def build_classes(exams):
    classes = {}
    for exam_index, exam in enumerate(exams):
        exam_classes = []
        for class_index in range(8):
            class_id = str(170000 + exam_index * 100 + class_index)
            admin_class = f"K{68 + class_index % 3}{chr(65 + class_index % 4)}"
            exam_classes.append({
                "id_lop_hp": class_id,
                "ma_lop": admin_class,
                "ten_lop": f"{exam['ten_hp']} - Nhom {class_index + 1}",
            })
        classes[exam["exam_id"]] = exam_classes
    return classes


def choose_student_answer(correct_answer, ability, qid):
    question_difficulty = 0.08 * ((qid % 10) - 4.5) / 4.5
    probability_correct = min(0.98, max(0.18, ability - question_difficulty))
    if random.random() <= probability_correct:
        return correct_answer

    wrong_options = [option for option in OPTIONS if option != correct_answer]
    return wrong_options[(qid + random.randint(0, 2)) % len(wrong_options)]


def make_student_name(index):
    last_name = LAST_NAMES[index % len(LAST_NAMES)]
    middle_name = MIDDLE_NAMES[(index // len(LAST_NAMES)) % len(MIDDLE_NAMES)]
    first_name = FIRST_NAMES[(index // (len(LAST_NAMES) * len(MIDDLE_NAMES))) % len(FIRST_NAMES)]
    return f"{last_name} {middle_name} {first_name}"


def clipped_gauss(mean, std_dev, low, high):
    return min(high, max(low, random.gauss(mean, std_dev)))


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
