# Result Sorting Design

## Goal

After grading, the result table should show students in the same sequence as the input `students.csv` file. The app should sort test results only when the user explicitly chooses a sort option.

## Current Behavior

`main_gui.py` grades all students into `self.results`, then immediately computes `self.ranking = get_ranking(self.results)`. The results table, exam/class filters, and "show all" action use that sorted ranking list, so users see score-ranked output from the beginning.

## Proposed Behavior

The app will keep two separate result views:

- `self.results`: the existing `HashTable` for fast lookup by `exam_id|student_id`.
- `self.result_rows`: a list of `ExamResult` objects in the original CSV order.

Immediately after grading, the table displays `self.result_rows`. No ranking sort is applied by default.

The results tab will add an explicit sort control. The initial sort option is `CSV order`. The supported options are:

- Score high to low
- Score low to high
- Correct answers high to low
- Student ID
- Student name
- Exam ID

When the user changes the sort option, the app sorts the currently relevant result list for display. The underlying `HashTable` and CSV-order list remain unchanged.

## Data Flow

1. Load students from CSV into the existing custom `List`, preserving file order.
2. Grade students into the existing `HashTable`.
3. Build `self.result_rows` by iterating `self.students` in order and retrieving each matching result from `self.results`.
4. Display `self.result_rows` in the results table.
5. Apply exam/class/score filters to the current base list.
6. Apply the selected sort option only for display.

## Ranking and Top-K

The existing ranking behavior remains available when the user chooses a ranking-style sort, such as score high to low. Top-k will continue to use the optimized quick-select path when no exam/class filter is active. When filters are active, top-k will operate on the filtered display list after applying score high-to-low ranking order.

## Export

CSV export will keep the current ranked export. This keeps output behavior stable while changing only the interactive table default.

## Error Handling

If a student from the CSV does not have a matching graded result, the ordered-list builder will fail with a clear error. A missing result indicates an invalid grading state.

## Tests

Add focused tests for:

- Building result rows in the same order as the student CSV.
- Default display order using CSV order after grading.
- Score descending sort matching the existing ranking order.
- Exam/class filtering preserving CSV order unless a sort option is selected.
- Score-range filtering still returning the correct students.
