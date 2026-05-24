import unittest

from app_logic import (
    AnswerKeyBook,
    build_student_search_index,
    get_student_id_suggestions,
    get_student_name_suggestions,
    grade_all,
    search_students_by_name_prefix,
    search_students_indexed,
)
from custom_structures import List
from models import Question, Student


def make_answer_key():
    answer_key = AnswerKeyBook()
    answer_key.put("EXAM001", Question("1", "A", "EXAM001"))
    answer_key.put("EXAM002", Question("1", "B", "EXAM002"))
    return answer_key


def make_students():
    students = List()
    students.append(Student("20230002", "Tran Binh", {"1": "A"}, exam_id="EXAM001"))
    students.append(Student("20230001", "Nguyen An", {"1": "A"}, exam_id="EXAM001"))
    students.append(Student("20230001", "Nguyen An", {"1": "B"}, exam_id="EXAM002"))
    students.append(Student("20240001", "Nguyen Anh", {"1": "B"}, exam_id="EXAM002"))
    return students


class StudentSearchIndexTests(unittest.TestCase):
    def setUp(self):
        self.results = grade_all(make_students(), make_answer_key())
        self.index = build_student_search_index(self.results)

    def test_exact_student_id_search_returns_all_exams_sorted(self):
        rows = search_students_indexed(self.index, "20230001")

        self.assertEqual([(row.exam_id, row.student_id) for row in rows], [
            ("EXAM001", "20230001"),
            ("EXAM002", "20230001"),
        ])

    def test_exact_student_id_search_can_filter_exam(self):
        rows = search_students_indexed(self.index, "20230001", exam_id="EXAM002")

        self.assertEqual([(row.exam_id, row.student_id) for row in rows], [("EXAM002", "20230001")])

    def test_student_id_suggestions_use_trie(self):
        suggestions = get_student_id_suggestions(self.index.student_id_trie, "2023", limit=5)

        self.assertEqual(suggestions, ["20230001", "20230002"])

    def test_name_suggestions_use_trie(self):
        suggestions = get_student_name_suggestions(self.index, "nguyen", limit=5)

        self.assertEqual(suggestions, ["Nguyen An", "Nguyen Anh"])

    def test_name_prefix_search_returns_matching_results(self):
        rows = search_students_by_name_prefix(self.index, "nguyen a")

        self.assertEqual(
            [(row.student_name, row.exam_id, row.student_id) for row in rows],
            [
                ("Nguyen An", "EXAM001", "20230001"),
                ("Nguyen An", "EXAM002", "20230001"),
                ("Nguyen Anh", "EXAM002", "20240001"),
            ],
        )

    def test_name_prefix_search_respects_limit_and_exam_filter(self):
        rows = search_students_by_name_prefix(self.index, "nguyen", exam_id="EXAM002", limit=1)

        self.assertEqual([(row.student_name, row.exam_id) for row in rows], [("Nguyen An", "EXAM002")])

    def test_name_prefix_search_filters_exam_before_result_limit(self):
        students = List()
        students.append(Student("20250001", "Alpha One", {"1": "A"}, exam_id="EXAM001"))
        students.append(Student("20250002", "Alpha Two", {"1": "B"}, exam_id="EXAM002"))
        results = grade_all(students, make_answer_key())
        index = build_student_search_index(results)

        rows = search_students_by_name_prefix(index, "alpha", exam_id="EXAM002", limit=1)

        self.assertEqual([(row.student_name, row.exam_id) for row in rows], [("Alpha Two", "EXAM002")])


if __name__ == "__main__":
    unittest.main()
