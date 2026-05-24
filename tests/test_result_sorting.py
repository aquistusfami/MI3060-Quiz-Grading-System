import unittest

from app_logic import (
    AnswerKeyBook,
    SORT_CORRECT_DESC,
    SORT_CSV_ORDER,
    SORT_EXAM_ID,
    SORT_SCORE_ASC,
    SORT_SCORE_DESC,
    SORT_STUDENT_ID,
    build_result_rows_in_student_order,
    get_ranking,
    grade_all,
    sort_results,
)
from custom_structures import List
from models import Question, Student


def make_answer_key():
    answer_key = AnswerKeyBook()
    answer_key.put("EXAM001", Question("1", "A", "EXAM001"))
    answer_key.put("EXAM001", Question("2", "B", "EXAM001"))
    answer_key.put("EXAM002", Question("1", "C", "EXAM002"))
    answer_key.put("EXAM002", Question("2", "D", "EXAM002"))
    return answer_key


def make_students():
    students = List()
    students.append(Student("S002", "Beta Student", {"1": "A", "2": "D"}, exam_id="EXAM001"))
    students.append(Student("S001", "Alpha Student", {"1": "A", "2": "B"}, exam_id="EXAM001"))
    students.append(Student("S003", "Gamma Student", {"1": "A", "2": "B"}, exam_id="EXAM001"))
    students.append(Student("S004", "Delta Student", {"1": "C", "2": "D"}, exam_id="EXAM002"))
    return students


class ResultSortingTests(unittest.TestCase):
    def setUp(self):
        self.students = make_students()
        self.results = grade_all(self.students, make_answer_key())
        self.rows = build_result_rows_in_student_order(self.students, self.results)

    def assert_ids(self, rows, expected_ids):
        self.assertEqual([row.student_id for row in rows], expected_ids)

    def test_build_result_rows_preserves_student_csv_order(self):
        self.assert_ids(self.rows, ["S002", "S001", "S003", "S004"])

    def test_build_result_rows_raises_when_result_missing(self):
        self.results.remove("EXAM001|S002")

        with self.assertRaisesRegex(ValueError, "Thiếu kết quả chấm"):
            build_result_rows_in_student_order(self.students, self.results)

    def test_grade_all_rejects_duplicate_student_in_same_exam(self):
        students = List()
        students.append(Student("S001", "First Submission", {"1": "A", "2": "B"}, exam_id="EXAM001"))
        students.append(Student("S001", "Second Submission", {"1": "A", "2": "D"}, exam_id="EXAM001"))

        with self.assertRaisesRegex(ValueError, "Trùng kết quả"):
            grade_all(students, make_answer_key())

    def test_csv_order_sort_returns_copy_in_same_order(self):
        sorted_rows = sort_results(self.rows, SORT_CSV_ORDER)

        self.assertIsNot(sorted_rows, self.rows)
        self.assert_ids(sorted_rows, ["S002", "S001", "S003", "S004"])

    def test_score_desc_sort_matches_existing_ranking(self):
        sorted_rows = sort_results(self.rows, SORT_SCORE_DESC)
        ranking = get_ranking(self.results)

        self.assert_ids(sorted_rows, [row.student_id for row in ranking])

    def test_score_asc_sort_orders_low_scores_first(self):
        sorted_rows = sort_results(self.rows, SORT_SCORE_ASC)

        self.assert_ids(sorted_rows, ["S002", "S001", "S003", "S004"])

    def test_correct_desc_sort_uses_score_tiebreakers(self):
        sorted_rows = sort_results(self.rows, SORT_CORRECT_DESC)

        self.assert_ids(sorted_rows, ["S004", "S003", "S001", "S002"])

    def test_student_id_sort_orders_by_student_id(self):
        sorted_rows = sort_results(self.rows, SORT_STUDENT_ID)

        self.assert_ids(sorted_rows, ["S001", "S002", "S003", "S004"])

    def test_exam_id_sort_groups_by_exam_then_student(self):
        sorted_rows = sort_results(self.rows, SORT_EXAM_ID)

        self.assert_ids(sorted_rows, ["S001", "S002", "S003", "S004"])

    def test_unknown_sort_option_raises_clear_error(self):
        with self.assertRaisesRegex(ValueError, "Tùy chọn sắp xếp kết quả"):
            sort_results(self.rows, "not a sort option")

    def test_results_table_uses_sequence_label_not_rank_label(self):
        with open("main_gui.py", encoding="utf-8") as source:
            gui_source = source.read()

        self.assertIn('cols = ("STT", "Kỳ thi", "MSSV"', gui_source)

    def test_question_tab_has_empty_data_guard(self):
        with open("main_gui.py", encoding="utf-8") as source:
            gui_source = source.read()

        self.assertIn("if self.question_stats is None or self.answer_key is None:", gui_source)


if __name__ == "__main__":
    unittest.main()
