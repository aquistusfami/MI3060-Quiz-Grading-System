# Multiple-Choice Exam Grading System

A desktop application for grading multiple-choice exams from CSV files. The project is written in Python with a CustomTkinter GUI and uses self-implemented data structures for storage, search, sorting, ranking, and question statistics.

## Features

- Load answer keys and student submissions from CSV files.
- Support multiple exams through `exam_id`.
- Grade every student on a 10-point scale.
- Show ranking by score, number of correct answers, exam, and student ID.
- Filter results by score range, exam, and class section.
- Search student results by student ID or name.
- View each student's selected answers beside the correct answers.
- Compute exam-level statistics: average score, highest score, lowest score, standard deviation, pass count, fail count, and pass rate.
- Compute class-level summaries by exam and class section.
- Compute question-level statistics, including correct count, wrong count, and correct percentage.
- Show the hardest questions using a custom min-heap.
- Edit an answer key inside the GUI and regrade with the updated answer.
- Export graded results and question statistics to CSV.

## Project Structure

```text
.
├── app_logic.py              # CSV loading, grading, statistics, search, export logic
├── custom_structures.py      # Custom HashTable, List, merge sort, MinHeap
├── main_gui.py               # CustomTkinter desktop interface
├── models.py                 # Question, ExamInfo, Student, ExamResult, ExamStatistics
├── requirements.txt          # Python dependencies
├── scripts/
│   └── generate_perf_data.py # Deterministic large CSV dataset generator
├── data/
│   ├── answer_key.csv        # Sample answer keys
│   ├── exams.csv             # Sample exam metadata
│   └── students.csv          # Sample student submissions
├── output/
    ├── results.csv           # Exported grading results
    └── question_stats.csv    # Exported question statistics

```

## Requirements

- Python 3.10 or newer
- `customtkinter`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
python main_gui.py
```

The application opens with default CSV paths:

- `data/answer_key.csv`
- `data/students.csv`
- `data/exams.csv`

You can choose other answer key and student files from the toolbar, then click `CHẤM ĐIỂM` to grade the exam.

## CSV Input Format

### Answer Key

File: `data/answer_key.csv`

Required columns:

| Column | Description | Example |
|---|---|---|
| `exam_id` | Exam or test identifier | `EXAM001` |
| `question_id` | Question number | `1` |
| `correct_answer` | Correct option | `A` |

Example:

```csv
exam_id,question_id,correct_answer
EXAM001,1,A
EXAM001,2,C
EXAM001,3,B
```

### Students

File: `data/students.csv`

Common columns:

| Column | Description | Example |
|---|---|---|
| `exam_id` | Exam or test identifier | `EXAM001` |
| `ma_hp` | Course code | `MI1111` |
| `hoc_ky` | Semester | `20251` |
| `id_lop_hp` | Course class ID | `163613` |
| `mssv` | Student ID | `20230001` |
| `ho_ten` | Student name | `Nguyen Van An` |
| `ma_lop` | Administrative class ID | `23D1` |
| `ten_lop` | Administrative class name | `Toan Tin K68 - Nhom 1` |
| `q1`, `q2`, ... | Student answers | `A`, `B`, `C`, `D` |

Example:

```csv
exam_id,ma_hp,hoc_ky,id_lop_hp,mssv,ho_ten,ma_lop,ten_lop,q1,q2,q3
EXAM001,MI1111,20251,163613,20230001,Nguyen Van An,23D1,Toan Tin K68 - Nhom 1,A,C,B
```

### Exam Metadata

File: `data/exams.csv`

Common columns:

| Column | Description | Example |
|---|---|---|
| `exam_id` | Exam or test identifier | `EXAM001` |
| `ma_hp` | Course code | `MI1111` |
| `ten_hp` | Course name | `Giai tich 1` |
| `hoc_ky` | Semester | `20251` |
| `ten_ky_thi` | Exam name | `Kiem tra trac nghiem MI1111 - dot 1` |
| `ngay_thi` | Exam date | `2025-10-15` |
| `thoi_luong_phut` | Duration in minutes | `45` |
| `ghi_chu` | Note | `Ap dung cho cac lop hoc phan 163613-163615` |

The app can still run if `exams.csv` is missing. In that case, it infers basic exam entries from the answer key and student data.
When selected answer/student files live beside an `exams.csv`, the GUI uses that metadata file automatically.

## Performance Dataset

Generate a larger deterministic dataset:

```bash
python scripts/generate_perf_data.py
```

Output files:

- `data/performance/exams.csv`: 5 exams
- `data/performance/answer_key.csv`: 500 answer-key rows, 100 questions per exam
- `data/performance/students.csv`: 10,000 students, 100 answers per student

The generated students are distributed across 5 courses and 40 course sections. Their answers are based on a mixed ability distribution, so score statistics are realistic enough for grading, filtering, top-k, question statistics, and export performance tests.

## Output Files

Click `Xuất CSV` after grading to export:

- `output/results.csv`: ranked student results
- `output/question_stats.csv`: per-question correct and wrong counts

The exported files use UTF-8 with BOM so spreadsheet applications can open Vietnamese text correctly.

## Main Screens

- `Kết quả & Xếp hạng`: ranking table, score range filter, top-k results, exam/class filters, and answer detail for selected students.
- `Thống kê tổng hợp`: overall statistics and class summaries.
- `Thông tin kỳ thi`: exam list and exam details.
- `Danh sách lớp HP`: class roster summaries and graded students by class section.
- `Thống kê câu hỏi`: correct rate by question, hardest questions, and answer key editing.
- `Tìm kiếm thí sinh`: lookup by student ID or name across exams.

## Algorithms and Data Structures

The project intentionally uses custom implementations instead of relying only on Python built-ins:

- `HashTable`: separate chaining hash table for answer keys, results, exam metadata, and grouped statistics.
- `List`: resizable array for loaded student records.
- `merge_sort`: stable sorting for rankings, exam lists, score indexes, and summaries.
- `MinHeap`: finds the hardest questions by lowest correct-answer rate.
- Binary-search-style score range lookup: uses a sorted score index to retrieve students in a score interval.
- Quick select: retrieves top-k results before sorting only the selected subset.

## Grading Formula

Each student receives:

```text
score = correct_answers / total_questions * 10
```

The displayed score is rounded to two decimal places.

## Notes

- Answer values are normalized to uppercase before comparison.
- Missing student answers are treated as empty and counted as wrong.
- If `exam_id` is missing, the default exam ID is `EXAM001`.
- The GUI labels are mainly Vietnamese because the sample data follows a HUST-style exam workflow.
