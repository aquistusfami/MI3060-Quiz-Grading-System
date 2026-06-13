"""Kiểm thử tự động cho validation, chấm điểm và cấu trúc dữ liệu.

Test dùng thư mục tạm cho mọi file phát sinh và không thay đổi dữ liệu project.
Chạy bằng ``python3 -m unittest discover -s tests -p 'test_*.py' -v``.
"""

import csv
import os
import sys
import tempfile
import unittest


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app_logic import (  # noqa: E402
    AnswerKeyBook,
    build_class_summary,
    build_result_rows_in_student_order,
    build_score_index,
    build_student_search_index,
    compute_question_stats,
    export_results_csv,
    get_hardest_questions,
    get_student_id_suggestions,
    get_students_in_score_range,
    grade_all,
    grade_student,
    load_answer_key,
    load_students,
    parse_score_range,
    search_students_by_name_prefix,
    search_students_indexed,
    validate_answer_key_csv,
    validate_grading_inputs,
    validate_students_csv,
)
from custom_structures import HashTable, List, MinHeap, PrefixTrie, merge_sort  # noqa: E402
from models import ExamResult, Question, Student  # noqa: E402


def make_table(*pairs):
    """Tạo ``HashTable`` từ các cặp khóa-giá trị cho dữ liệu kiểm thử."""
    table = HashTable()
    for key, value in pairs:
        table.put(key, value)
    return table


class CsvTestCase(unittest.TestCase):
    """Cung cấp thư mục tạm và helper ghi CSV cho các test validation."""

    def setUp(self):
        """Tạo thư mục riêng trước mỗi test."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Xóa thư mục và file tạm sau mỗi test."""
        self.temp_dir.cleanup()

    def write_csv(self, name, rows):
        """Ghi ``rows`` vào file tạm và trả về đường dẫn file."""
        path = os.path.join(self.temp_dir.name, name)
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        return path


class AnswerKeyValidationTests(CsvTestCase):
    """Kiểm tra cấu trúc, giá trị biên và dữ liệu trùng của file đáp án."""

    def test_valid_answer_key(self):
        path = self.write_csv(
            "answers.csv",
            [
                ["exam_id", "question_id", "correct_answer"],
                ["E1", "1", "A"],
                ["E2", "1", "B"],
            ],
        )
        self.assertEqual(validate_answer_key_csv(path), [])
        self.assertEqual(len(load_answer_key(path)), 2)

    def test_missing_required_column(self):
        path = self.write_csv(
            "answers.csv",
            [["exam_id", "question_id"], ["E1", "1"]],
        )
        self.assertIn("correct_answer", validate_answer_key_csv(path)[0])

    def test_invalid_question_id_boundaries(self):
        for question_id in ("", "0", "-1", "01", "A"):
            with self.subTest(question_id=question_id):
                path = self.write_csv(
                    "answers.csv",
                    [
                        ["exam_id", "question_id", "correct_answer"],
                        ["E1", question_id, "A"],
                    ],
                )
                self.assertTrue(validate_answer_key_csv(path))

    def test_blank_answer_and_duplicate_question(self):
        blank_path = self.write_csv(
            "blank.csv",
            [
                ["exam_id", "question_id", "correct_answer"],
                ["E1", "1", "   "],
            ],
        )
        duplicate_path = self.write_csv(
            "duplicate.csv",
            [
                ["exam_id", "question_id", "correct_answer"],
                ["E1", "1", "A"],
                ["E1", "1", "B"],
            ],
        )
        self.assertIn("correct_answer", validate_answer_key_csv(blank_path)[0])
        self.assertTrue(
            any("trùng câu" in error for error in validate_answer_key_csv(duplicate_path))
        )


class StudentValidationTests(CsvTestCase):
    """Kiểm tra header, trường bắt buộc và file sinh viên rỗng."""

    def test_valid_student_file(self):
        path = self.write_csv(
            "students.csv",
            [
                ["exam_id", "mssv", "ho_ten", "q1"],
                ["E1", "20260001", "Nguyen Van An", "A"],
            ],
        )
        self.assertEqual(validate_students_csv(path), [])
        self.assertEqual(len(load_students(path)), 1)

    def test_missing_required_columns(self):
        cases = (
            (["ho_ten", "q1"], ["An", "A"], "thiếu cột MSSV"),
            (["mssv", "q1"], ["1", "A"], "thiếu cột họ tên"),
            (["mssv", "ho_ten"], ["1", "An"], "ít nhất một cột đáp án"),
        )
        for index, (header, row, expected) in enumerate(cases):
            with self.subTest(expected=expected):
                path = self.write_csv(f"students_{index}.csv", [header, row])
                self.assertTrue(
                    any(expected in error for error in validate_students_csv(path))
                )

    def test_blank_student_id_and_name(self):
        path = self.write_csv(
            "students.csv",
            [
                ["mssv", "ho_ten", "q1"],
                ["", "An", "A"],
                ["2", "", "B"],
            ],
        )
        errors = validate_students_csv(path)
        self.assertTrue(any("MSSV không được" in error for error in errors))
        self.assertTrue(any("họ tên không được" in error for error in errors))

    def test_header_only_file_is_rejected(self):
        path = self.write_csv(
            "students.csv",
            [["mssv", "ho_ten", "q1"]],
        )
        self.assertEqual(
            validate_students_csv(path),
            ["File thí sinh không có dữ liệu."],
        )


class GradingTests(unittest.TestCase):
    """Kiểm tra công thức điểm, liên kết kỳ thi và thống kê kết quả."""

    def setUp(self):
        self.answer_key = AnswerKeyBook()
        self.answer_key.put("E1", Question("1", "A", "E1"))
        self.answer_key.put("E1", Question("2", "B", "E1"))

    def student(self, student_id, answers, exam_id="E1", name="Student"):
        """Tạo thí sinh tối thiểu dùng chung cho các ca chấm điểm."""
        answer_table = HashTable()
        for question_id, answer in answers:
            answer_table.put(question_id, answer)
        return Student(student_id, name, answer_table, class_id="C1", exam_id=exam_id)

    def test_score_boundaries_and_missing_answer(self):
        perfect = grade_student(self.student("1", (("1", "A"), ("2", "B"))), self.answer_key)
        half = grade_student(self.student("2", (("1", "A"),)), self.answer_key)
        zero = grade_student(self.student("3", ()), self.answer_key)

        self.assertEqual((perfect.score, perfect.accuracy_percent), (10.0, 100.0))
        self.assertEqual((half.score, half.wrong_questions), (5.0, ["2"]))
        self.assertEqual(zero.score, 0.0)

    def test_answers_are_compared_exactly(self):
        result = grade_student(
            self.student("1", (("1", "a"), ("2", " B "))),
            self.answer_key,
        )
        self.assertEqual(result.score, 0.0)

    def test_missing_exam_answer_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Không có đáp án"):
            grade_student(self.student("1", (), exam_id="E2"), self.answer_key)

    def test_duplicate_student_in_same_exam_is_rejected(self):
        students = List()
        students.append(self.student("1", ()))
        students.append(self.student("1", ()))
        errors = validate_grading_inputs(self.answer_key, students)
        self.assertTrue(any("Trùng MSSV" in error for error in errors))

    def test_same_student_id_in_different_exams_is_allowed(self):
        self.answer_key.put("E2", Question("1", "A", "E2"))
        students = List()
        students.append(self.student("1", (("1", "A"),), exam_id="E1"))
        students.append(self.student("1", (("1", "A"),), exam_id="E2"))
        self.assertEqual(validate_grading_inputs(self.answer_key, students), [])
        self.assertEqual(len(grade_all(students, self.answer_key)), 2)

    def test_grading_statistics_and_csv_order(self):
        students = List()
        students.append(self.student("2", (("1", "A"), ("2", "B"))))
        students.append(self.student("1", (("1", "A"), ("2", "X"))))
        results = grade_all(students, self.answer_key)
        rows = build_result_rows_in_student_order(students, results)
        stats = compute_question_stats(students, self.answer_key)

        self.assertEqual([row.student_id for row in rows], ["2", "1"])
        self.assertEqual(stats.get("E1|1")["correct"], 2)
        self.assertEqual(stats.get("E1|2")["correct"], 1)

    def test_class_summary_uses_five_as_passing_boundary(self):
        students = List()
        students.append(self.student("1", (("1", "A"),)))
        students.append(self.student("2", ()))
        summary = build_class_summary(grade_all(students, self.answer_key))[0]

        self.assertEqual(summary["average"], 2.5)
        self.assertEqual(summary["passing_rate"], 50.0)


class ScoreRangeAndSearchTests(unittest.TestCase):
    """Kiểm tra biên lọc điểm và các chỉ mục tìm kiếm sinh viên."""

    @staticmethod
    def result(student_id, score, name="Student", exam_id="E1"):
        """Tạo kết quả tối thiểu dùng cho kiểm thử lọc và tìm kiếm."""
        student = Student(student_id, name, HashTable(), exam_id=exam_id)
        return ExamResult(student, score, int(score), 10, List())

    def setUp(self):
        self.results = HashTable()
        for student_id, score in (("0", 0), ("499", 4.99), ("5", 5), ("10", 10)):
            self.results.put(f"E1|{student_id}", self.result(student_id, score))

    def test_parse_finite_score_range(self):
        self.assertEqual(parse_score_range("5", "10"), (5.0, 10.0))
        self.assertEqual(parse_score_range("10", "5"), (10.0, 5.0))

    def test_parse_score_range_rejects_invalid_values(self):
        for value in ("", "abc", None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Điểm lọc phải là số"):
                    parse_score_range(value, "10")

        for value in ("nan", "NaN", "inf", "+inf", "-inf", "Infinity"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "số hữu hạn"):
                    parse_score_range(value, "10")

    def test_score_range_is_inclusive_and_accepts_reversed_bounds(self):
        index = build_score_index(self.results)
        expected = [10.0, 5.0]
        self.assertEqual(
            [row.score for row in get_students_in_score_range(index, 5, 10)],
            expected,
        )
        self.assertEqual(
            [row.score for row in get_students_in_score_range(index, 10, 5)],
            expected,
        )

    def test_indexed_search_and_prefix_suggestions(self):
        results = HashTable()
        results.put("E1|1", self.result("1", 10, "Nguyen Van An", "E1"))
        results.put("E2|1", self.result("1", 8, "Nguyen Van An", "E2"))
        results.put("E1|2", self.result("2", 6, "Tran Thi Bich", "E1"))
        index = build_student_search_index(results)

        self.assertEqual(len(search_students_indexed(index, "1")), 2)
        self.assertEqual(len(search_students_indexed(index, "1", "E1")), 1)
        self.assertEqual(len(search_students_by_name_prefix(index, "nguyen")), 2)
        self.assertEqual(get_student_id_suggestions(index.student_id_trie, "1"), ["1"])


class ExportAndStructureTests(CsvTestCase):
    """Kiểm tra xuất file và hành vi biên của cấu trúc dữ liệu tự cài đặt."""

    def test_export_results_creates_parent_directory(self):
        student = Student("1", "An", HashTable(), exam_id="E1")
        result = ExamResult(student, 10, 1, 1, List())
        results = HashTable()
        results.put("E1|1", result)
        output_path = os.path.join(self.temp_dir.name, "nested", "results.csv")

        export_results_csv(results, output_path)

        self.assertTrue(os.path.exists(output_path))
        with open(output_path, newline="", encoding="utf-8-sig") as file:
            rows = list(csv.reader(file))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][2], "1")

    def test_hash_table_resizes_without_losing_values(self):
        table = HashTable(capacity=4)
        for value in range(4):
            table.put(str(value), value)

        self.assertEqual(table.capacity, 8)
        self.assertEqual([table.get(str(value)) for value in range(4)], list(range(4)))

    def test_hash_table_supports_iteration_and_none_values(self):
        table = HashTable()
        table.put("empty", None)
        table.put("value", 10)

        self.assertIn("empty", table)
        self.assertIsNone(table["empty"])
        iterated_keys = List()
        iterated_keys.extend(table)
        self.assertEqual(len(iterated_keys), 2)
        self.assertIn("empty", iterated_keys)
        self.assertIn("value", iterated_keys)
        with self.assertRaises(KeyError):
            _ = table["missing"]

    def test_dynamic_list_grows_shrinks_and_checks_empty_pop(self):
        values = List()
        for value in range(9):
            values.append(value)
        self.assertEqual(values._capacity, 16)

        for _ in range(6):
            values.pop()
        self.assertEqual(values._capacity, 8)

        empty = List()
        with self.assertRaises(IndexError):
            empty.pop()

    def test_heap_trie_and_stable_merge_sort_boundaries(self):
        heap = MinHeap()
        with self.assertRaises(IndexError):
            heap.pop()

        trie = PrefixTrie()
        for value in ("An", "Anh", "An"):
            trie.insert(value)
        self.assertEqual(len(trie.autocomplete("an", limit=1)), 1)
        self.assertEqual(len(trie.autocomplete("an", limit=8)), 2)

        values = [(1, "first"), (1, "second")]
        self.assertEqual(merge_sort(values, key=lambda item: item[0]), values)

    def test_hardest_questions_returns_lowest_rate_first(self):
        stats = HashTable()
        stats.put("E1|1", make_table(("exam_id", "E1"), ("question_id", "1"), ("correct", 2), ("total", 2)))
        stats.put("E1|2", make_table(("exam_id", "E1"), ("question_id", "2"), ("correct", 0), ("total", 2)))
        stats.put("E1|3", make_table(("exam_id", "E1"), ("question_id", "3"), ("correct", 1), ("total", 2)))

        hardest = get_hardest_questions(stats, 2)
        self.assertEqual([item[1] for item in hardest], ["2", "3"])


class SampleDataIntegrationTests(unittest.TestCase):
    """Kiểm tra luồng chấm hoàn chỉnh trên bộ dữ liệu mẫu của project."""

    def test_sample_data_grading_flow(self):
        answer_path = os.path.join(BASE_DIR, "data", "answer_key.csv")
        student_path = os.path.join(BASE_DIR, "data", "students.csv")

        self.assertEqual(validate_answer_key_csv(answer_path), [])
        self.assertEqual(validate_students_csv(student_path), [])

        answer_key = load_answer_key(answer_path)
        students = load_students(student_path)
        self.assertEqual(validate_grading_inputs(answer_key, students), [])

        results = grade_all(students, answer_key)
        first_result = build_result_rows_in_student_order(students, results)[0]
        self.assertEqual(len(answer_key), 40)
        self.assertEqual(len(students), 25)
        self.assertEqual(len(results), 25)
        self.assertEqual(len(compute_question_stats(students, answer_key)), 40)
        self.assertIsInstance(first_result.student.answers, HashTable)
        self.assertIsInstance(first_result.wrong_questions, List)
        self.assertIsInstance(answer_key.question_ids(first_result.exam_id), List)


if __name__ == "__main__":
    unittest.main(verbosity=2)
