import unittest

from app_logic import (
    AnswerKeyBook,
    build_score_index,
    compute_question_stats,
    get_hardest_questions,
    get_question_stats_items,
    get_students_in_score_range,
    get_top_k_results,
    grade_all,
)
from custom_structures import List
from models import Question, Student


def make_answer_key():
    answer_key = AnswerKeyBook()
    answer_key.put("EXAM001", Question("1", "A", "EXAM001"))
    answer_key.put("EXAM001", Question("2", "B", "EXAM001"))
    answer_key.put("EXAM001", Question("3", "C", "EXAM001"))
    answer_key.put("EXAM002", Question("1", "D", "EXAM002"))
    answer_key.put("EXAM002", Question("2", "C", "EXAM002"))
    return answer_key


def make_students():
    students = List()
    students.append(Student("S001", "Alpha", {"1": "A", "2": "B", "3": "C"}, exam_id="EXAM001"))
    students.append(Student("S002", "Beta", {"1": "A", "2": "", "3": "E"}, exam_id="EXAM001"))
    students.append(Student("S003", "Gamma", {"1": "D", "2": "A"}, exam_id="EXAM002"))
    students.append(Student("S004", "Delta", {"1": "D", "2": "C"}, exam_id="EXAM002"))
    return students


class AlgorithmHelperTests(unittest.TestCase):
    def setUp(self):
        self.answer_key = make_answer_key()
        self.students = make_students()
        self.results = grade_all(self.students, self.answer_key)

    def test_missing_and_invalid_answers_count_wrong(self):
        result = self.results.get("EXAM001|S002")

        self.assertEqual(result.correct_count, 1)
        self.assertEqual(result.total_questions, 3)
        self.assertEqual(result.wrong_questions, ["2", "3"])

    def test_multiple_exams_use_separate_answer_keys(self):
        exam_two_result = self.results.get("EXAM002|S004")

        self.assertEqual(exam_two_result.correct_count, 2)
        self.assertEqual(exam_two_result.score, 10.0)

    def test_score_range_uses_sorted_index(self):
        score_index = build_score_index(self.results)
        rows = get_students_in_score_range(score_index, 6.0, 10.0)

        self.assertEqual([row.student_id for row in rows], ["S004", "S001"])

    def test_top_k_uses_score_order(self):
        rows = get_top_k_results(self.results, 2)

        self.assertEqual([row.student_id for row in rows], ["S001", "S004"])

    def test_question_stats_and_hardest_questions(self):
        stats = compute_question_stats(self.students, self.answer_key)
        items = get_question_stats_items(stats)
        hardest = get_hardest_questions(stats, 2)

        self.assertEqual(
            [(item["exam_id"], item["question_id"], item["correct"], item["total"]) for item in items],
            [
                ("EXAM001", "1", 2, 2),
                ("EXAM001", "2", 1, 2),
                ("EXAM001", "3", 1, 2),
                ("EXAM002", "1", 2, 2),
                ("EXAM002", "2", 1, 2),
            ],
        )
        self.assertEqual(
            [(exam_id, qid, rate) for exam_id, qid, _correct, _total, rate in hardest],
            [("EXAM001", "2", 50.0), ("EXAM001", "3", 50.0)],
        )


if __name__ == "__main__":
    unittest.main()
