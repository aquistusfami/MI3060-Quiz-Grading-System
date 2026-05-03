import os
import csv
from sys_logics import Exam, StudentSubmission

DATA_DIR = "data"
EXAMS_FILE = os.path.join(DATA_DIR, "exams.csv")
SUBMISSIONS_FILE = os.path.join(DATA_DIR, "submissions.csv")

def serialize_answers(answers_array):
    """Chuyển mảng các tập hợp (sets) thành chuỗi. Định dạng: A|B;C;;D"""
    parts = []
    for i in range(len(answers_array)):
        ans_set = answers_array.get(i)
        parts.append("|".join(sorted(list(ans_set))))
    return ";".join(parts)

def deserialize_answers(answers_str, answers_array):
    """Phân tích chuỗi và gán vào answers_array"""
    parts = answers_str.split(";")
    for i in range(min(len(answers_array), len(parts))):
        ans_str = parts[i]
        if ans_str:
            answers_array.set(i, set(ans_str.split("|")))

def save_exams(exams_db):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    with open(EXAMS_FILE, "w", newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["exam_code", "num_questions", "answers", "is_deleted"])
        for _, exam in exams_db.items():
            ans_str = serialize_answers(exam.answers)
            writer.writerow([exam.exam_code, exam.num_questions, ans_str, str(exam.is_deleted)])

def load_exams(exams_db):
    if not os.path.exists(EXAMS_FILE):
        return
    
    with open(EXAMS_FILE, "r", encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exam = Exam(row["exam_code"], int(row["num_questions"]))
            deserialize_answers(row["answers"], exam.answers)
            exam.is_deleted = row["is_deleted"].lower() == "true"
            exams_db.put_item(exam.exam_code, exam)

def save_submissions(submissions_db):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    with open(SUBMISSIONS_FILE, "w", newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["student_id", "name", "student_class", "exam_code", "num_questions", "answers", "score"])
        for _, sub in submissions_db.items():
            ans_str = serialize_answers(sub.answers)
            writer.writerow([sub.student_id, sub.name, sub.student_class, sub.exam_code, len(sub.answers), ans_str, sub.score])

def load_submissions(submissions_db):
    if not os.path.exists(SUBMISSIONS_FILE):
        return
        
    with open(SUBMISSIONS_FILE, "r", encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub = StudentSubmission(
                row["student_id"], 
                row["name"], 
                row["student_class"], 
                row["exam_code"], 
                int(row["num_questions"])
            )
            deserialize_answers(row["answers"], sub.answers)
            sub.score = float(row["score"])
            submissions_db.put_item(sub.student_id, sub)
