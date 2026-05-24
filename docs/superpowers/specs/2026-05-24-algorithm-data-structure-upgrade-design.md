# Algorithm/Data-Structure Upgrade Design

## Goal

Improve the quiz grading project's data-structure and algorithm strength without doing GUI architecture cleanup. The upgrade makes existing structures more meaningful, reduces avoidable linear scans, adds stronger edge-case coverage, and provides concrete benchmark evidence.

## Scope

This pass is limited to algorithm and data-structure improvements in the root quiz grading project.

In scope:

- Indexed search over graded results.
- More meaningful `PrefixTrie` usage.
- Tests for custom structures and algorithmic edge cases.
- Benchmark script for the performance dataset.
- Minimal GUI wiring only when needed to use new logic.

Out of scope:

- GUI redesign.
- Large module restructuring.
- Changes to the nested medical-management project.
- Replacing custom structures with Python built-ins.

## Search Index

Add a `StudentSearchIndex` in `app_logic.py`.

The index will be built from the graded `HashTable` results and will contain:

- `by_student_id`: `HashTable` mapping each MSSV to a list of `ExamResult` objects.
- `student_id_trie`: `PrefixTrie` for MSSV suggestions.
- `name_trie`: `PrefixTrie` for normalized student-name prefix suggestions.
- `all_rows`: deterministic list of result rows sorted by `(student_name, exam_id, student_id)` for name search output.

Exact MSSV lookup will use `by_student_id` instead of scanning `results.values()`. MSSV suggestions will use `student_id_trie`. Name-prefix suggestions will use `name_trie`. Existing substring name search remains available for compatibility, and new prefix-based name search demonstrates trie usage.

## Existing Search Helpers

Keep the existing public search helpers and add index-aware helpers:

- `build_student_search_index(results) -> StudentSearchIndex`
- `search_students_indexed(index, student_id, exam_id=None) -> list`
- `search_students_by_name_prefix(index, prefix, exam_id=None, limit=20) -> list`
- `get_student_name_suggestions(index, prefix, limit=8) -> list`

The GUI will build `StudentSearchIndex` after grading and use index-backed exact MSSV search and suggestions. Existing substring name search remains available.

## Tests

Add focused `unittest` coverage for:

- `HashTable`: insert, update, remove, resize, collision retrieval.
- `List`: append, insert, pop, negative indexing, resize shrink behavior.
- `MinHeap`: priority order and empty-pop error.
- `PrefixTrie`: insertion, duplicate handling, autocomplete limit, sorted traversal.
- Search index: exact MSSV lookup across multiple exams, name-prefix lookup, MSSV suggestions, name suggestions.
- Grading edge cases: missing answers count wrong, invalid answers count wrong, duplicate submissions raise, multiple exams do not mix answer keys.
- Algorithm helpers: score range lookup, top-k results, question statistics, hardest questions.

## Benchmarks

Add `scripts/benchmark_algorithms.py`.

The benchmark will load `data/performance/answer_key.csv`, `data/performance/students.csv`, and `data/performance/exams.csv` if present. It will measure:

- answer-key loading
- student loading
- grading
- building score index
- ranking
- top-k
- score-range filtering
- question statistics
- hardest-question extraction
- building search index
- exact indexed MSSV search
- trie suggestions for MSSV and names

The script will print row counts and elapsed time in milliseconds. It will not require external packages.

## Error Handling

Duplicate submissions for the same `(exam_id, student_id)` remain invalid and raise a clear `ValueError`.

Invalid or missing answers remain valid input rows but count as wrong during grading.

If the performance dataset is missing, the benchmark prints a clear message telling the user to run `python scripts/generate_perf_data.py`.

## Documentation

Update `README.md` to mention:

- indexed student search
- name-prefix trie suggestions
- benchmark script and how to run it
- expanded edge-case tests

## Success Criteria

- Existing tests pass.
- New structure/index tests pass.
- Benchmark script runs on `data/performance` and prints timings.
- Exact MSSV search no longer requires scanning all result values when using the new index.
- `PrefixTrie` is used for both MSSV and name suggestions.
