# HỆ THỐNG CHẤM ĐIỂM TRẮC NGHIỆM

Bài tập Lớn môn Cấu trúc Dữ liệu và Giải thuật - Đại học Bách Khoa Hà Nội.

169306 - MI3060

## 1. Thông tin nhóm sinh viên

* Phạm Huệ Chi - 202419036
* Nguyễn Đăng Hiếu - 202418900
* Lê Thanh Mai - 202418940
* Nguyễn Văn Thế - 202418988
* Phạm Thị Minh Thuý - 202418992

## 2. Cấu trúc mã nguồn

* `main_gui.py`: Điểm khởi đầu của chương trình, xây dựng cửa sổ CustomTkinter, điều phối thao tác người dùng và gọi các hàm xử lý nghiệp vụ.
* `app_logic.py`: Chứa logic chính của hệ thống: đọc dữ liệu CSV, kiểm tra dữ liệu đầu vào, chấm điểm, thống kê câu hỏi, xếp hạng, tìm kiếm, lọc kết quả và xuất file.
* `models.py`: Định nghĩa các lớp dữ liệu như `Question`, `ExamInfo`, `Student`, `ExamResult`.
* `custom_structures.py`: Chứa các cấu trúc dữ liệu và giải thuật tự cài đặt, gồm `HashTable`, `List`, `CounterArray`, `MinHeap`, `PrefixTrie`, `merge_sort`.
* `ui/`: Chia nhỏ giao diện thành các module tab độc lập, gồm tab kết quả, danh sách lớp học phần, thống kê câu hỏi, tìm kiếm thí sinh và widget dùng chung.
* `scripts/generate_perf_data.py`: Sinh bộ dữ liệu lớn để kiểm thử hiệu năng.
* `scripts/benchmark_algorithms.py`: Đo thời gian thực thi các thao tác chính trên dữ liệu lớn.
* `tests/`: Chứa các test cho logic chấm điểm, sắp xếp, tìm kiếm, kiểm tra dữ liệu đầu vào và cấu trúc dữ liệu.
* `data/`: Chứa dữ liệu mẫu của đề thi, đáp án và bài làm sinh viên.
* `output/`: Chứa kết quả xuất ra sau khi chấm điểm.
* `requirements.txt`: Danh sách thư viện cần thiết để chạy chương trình.

## 3. Mô tả tổng quan

Chương trình mô phỏng hệ thống chấm điểm trắc nghiệm tự động từ file CSV. Hệ thống phù hợp với bài toán xử lý dữ liệu điểm thi, trong đó dữ liệu đầu vào gồm danh sách đáp án, thông tin kỳ thi và bài làm của sinh viên.

Các chức năng chính:

* **Quản lý dữ liệu kỳ thi và đáp án**: Đọc đáp án theo từng `exam_id`, hỗ trợ nhiều đề thi hoặc nhiều lớp học phần trong cùng hệ thống.
* **Quản lý bài làm sinh viên**: Đọc danh sách sinh viên, mã lớp học phần, lớp hành chính và câu trả lời từ CSV.
* **Kiểm tra dữ liệu đầu vào**: Phát hiện thiếu cột bắt buộc, thiếu cột đáp án, trùng MSSV trong cùng kỳ thi, hoặc bài làm không có đáp án tương ứng.
* **Chấm điểm tự động**: So sánh bài làm với đáp án, tính số câu đúng, câu sai và điểm trên thang 10.
* **Hiển thị kết quả và xếp hạng**: Giữ thứ tự mặc định theo CSV hoặc sắp xếp theo điểm từ cao xuống thấp, thấp lên cao.
* **Lọc kết quả**: Lọc theo khoảng điểm, kỳ thi và lớp học phần.
* **Tra cứu thí sinh**: Tìm kiếm theo MSSV hoặc họ tên, có gợi ý tiền tố bằng cấu trúc Trie.
* **Thống kê lớp học phần**: Tổng hợp số sinh viên, điểm trung bình và tỷ lệ đạt theo từng lớp học phần.
* **Thống kê câu hỏi**: Tính số người đúng, sai, bỏ trống và tỷ lệ đúng của từng câu hỏi.
* **Phân tích câu hỏi khó**: Dùng heap để lấy các câu hỏi có tỷ lệ đúng thấp nhất.
* **Xuất dữ liệu**: Xuất bảng điểm và thống kê câu hỏi ra file CSV.

Dữ liệu của hệ thống được lưu trữ trong các tệp CSV như `answer_key.csv`, `students.csv`, `exams.csv`. Kết quả sau khi xử lý được xuất ra thư mục `output/`.

## 4. Cấu trúc dữ liệu và giải thuật sử dụng

Dự án ưu tiên tự cài đặt các cấu trúc dữ liệu cốt lõi thay vì chỉ dùng cấu trúc có sẵn của Python.

| Thành phần | Cấu trúc dữ liệu / giải thuật | Mục đích | Độ phức tạp chính |
|---|---|---|---|
| Lưu đáp án và kết quả | `HashTable` | Tra cứu nhanh đáp án theo `exam_id` và `question_id`, tra cứu kết quả theo MSSV | Trung bình `O(1)` |
| Lưu danh sách sinh viên | `List` | Lưu dữ liệu bài làm theo thứ tự đọc từ CSV | Truy cập `O(1)`, thêm cuối trung bình `O(1)` |
| Đếm thống kê câu hỏi | `CounterArray` | Đếm số đúng, tổng số lượt trả lời và số câu bỏ trống theo chỉ số câu hỏi | Cập nhật `O(1)` |
| Sắp xếp kết quả | `merge_sort` | Sắp xếp ổn định theo điểm và các tiêu chí phụ | `O(n log n)` |
| Gợi ý tìm kiếm | `PrefixTrie` | Gợi ý MSSV và họ tên theo tiền tố | `O(k + m)` |
| Câu hỏi khó nhất | `MinHeap` | Lấy các câu có tỷ lệ đúng thấp nhất | `O(q log q)` |
| Lọc khoảng điểm | Chỉ mục điểm + tìm kiếm nhị phân | Truy vấn sinh viên trong khoảng điểm | `O(log n + m)` |
| Top-k trong benchmark | Quickselect | Lấy k kết quả cao nhất phục vụ đo hiệu năng | Trung bình `O(n)` |

Trong đó:

* `n` là số sinh viên.
* `q` là số câu hỏi.
* `k` là độ dài tiền tố tìm kiếm.
* `m` là số kết quả trả về.

## 5. Định dạng dữ liệu đầu vào

### 5.1. File đáp án

File mẫu: `data/answer_key.csv`

Các cột bắt buộc:

| Cột | Ý nghĩa | Ví dụ |
|---|---|---|
| `exam_id` | Mã kỳ thi hoặc mã đề | `EXAM001` |
| `question_id` | Mã câu hỏi | `1` |
| `correct_answer` | Đáp án đúng | `A` |

Ví dụ:

```csv
exam_id,question_id,correct_answer
EXAM001,1,A
EXAM001,2,C
EXAM001,3,B
```

### 5.2. File bài làm sinh viên

File mẫu: `data/students.csv`

Các cột thường dùng:

| Cột | Ý nghĩa | Ví dụ |
|---|---|---|
| `exam_id` | Mã kỳ thi hoặc mã đề | `EXAM001` |
| `ma_hp` | Mã học phần | `MI1111` |
| `hoc_ky` | Học kỳ | `20251` |
| `id_lop_hp` | ID lớp học phần | `163613` |
| `mssv` | Mã số sinh viên | `20230001` |
| `ho_ten` | Họ tên sinh viên | `Nguyen Van An` |
| `ma_lop` | Mã lớp hành chính | `23D1` |
| `ten_lop` | Tên lớp hành chính | `Toan Tin K68 - Nhom 1` |
| `q1`, `q2`, ... | Câu trả lời của sinh viên | `A`, `B`, `C`, `D` |

Ví dụ:

```csv
exam_id,ma_hp,hoc_ky,id_lop_hp,mssv,ho_ten,ma_lop,ten_lop,q1,q2,q3
EXAM001,MI1111,20251,163613,20230001,Nguyen Van An,23D1,Toan Tin K68 - Nhom 1,A,C,B
```

### 5.3. File thông tin kỳ thi

File mẫu: `data/exams.csv`

Các cột thường dùng:

| Cột | Ý nghĩa | Ví dụ |
|---|---|---|
| `exam_id` | Mã kỳ thi hoặc mã đề | `EXAM001` |
| `ma_hp` | Mã học phần | `MI1111` |
| `ten_hp` | Tên học phần | `Giai tich 1` |
| `hoc_ky` | Học kỳ | `20251` |
| `ten_ky_thi` | Tên kỳ thi | `Kiem tra trac nghiem MI1111 - dot 1` |
| `ngay_thi` | Ngày thi | `2025-10-15` |
| `thoi_luong_phut` | Thời lượng thi | `45` |
| `ghi_chu` | Ghi chú | `Ap dung cho cac lop hoc phan 163613-163615` |

Nếu thiếu `exams.csv`, chương trình vẫn có thể chạy và tự suy luận thông tin kỳ thi cơ bản từ file đáp án và file bài làm.

## 6. Hướng dẫn cài đặt và chạy chương trình

### 6.1. Yêu cầu hệ thống

* Python 3.10 trở lên.
* Thư viện `customtkinter`.

### 6.2. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 6.3. Chạy ứng dụng

```bash
python main_gui.py
```

Sau khi chạy, chương trình mặc định sử dụng các file:

* `data/answer_key.csv`
* `data/students.csv`
* `data/exams.csv`

Người dùng có thể chọn file khác trên thanh công cụ, sau đó bấm `CHẤM ĐIỂM` để xử lý.

## 7. Các màn hình chính

* **Kết quả & Xếp hạng**: Hiển thị bảng điểm, bộ lọc điểm, bộ lọc kỳ thi, bộ lọc lớp học phần và chi tiết đáp án của sinh viên được chọn.
* **Danh sách lớp HP**: Hiển thị thống kê theo lớp học phần và danh sách sinh viên sau khi chấm điểm.
* **Thống kê câu hỏi**: Hiển thị số người đúng, sai, bỏ trống, tỷ lệ đúng và top câu hỏi khó.
* **Tìm kiếm thí sinh**: Tra cứu kết quả theo MSSV hoặc họ tên, hỗ trợ gợi ý bằng Trie.

## 8. Kiểm thử và đo hiệu năng

### 8.1. Chạy bộ kiểm thử

```bash
python -m unittest discover -s tests
```

Bộ test kiểm tra các phần chính:

* Cấu trúc dữ liệu `CounterArray`.
* Tùy chọn sắp xếp kết quả.
* Tìm kiếm theo tên và MSSV.
* Kiểm tra dữ liệu đầu vào.
* Các giao diện đã được tách khỏi `main_gui.py`.
* Các helper dư thừa đã được loại bỏ.

### 8.2. Sinh dữ liệu lớn

```bash
python scripts/generate_perf_data.py
```

Dữ liệu hiệu năng được tạo tại `data/performance/`, gồm:

* 5 kỳ thi.
* 100 câu hỏi cho mỗi kỳ thi.
* 10.000 sinh viên.

### 8.3. Chạy benchmark

```bash
python scripts/benchmark_algorithms.py
```

Benchmark đo thời gian cho các thao tác như tải dữ liệu, chấm điểm, tạo chỉ mục điểm, sắp xếp xếp hạng, lọc khoảng điểm, thống kê câu hỏi, tìm câu hỏi khó và tìm kiếm sinh viên.

## 9. Công thức chấm điểm

Mỗi sinh viên được chấm theo công thức:

```text
điểm = số_câu_đúng / tổng_số_câu * 10
```

Điểm hiển thị được làm tròn đến hai chữ số thập phân.

## 10. Ghi chú

* Đáp án được chuẩn hóa về chữ in hoa trước khi so sánh.
* Câu trả lời bị bỏ trống được tính là sai và được thống kê riêng ở phần câu hỏi.
* Nếu thiếu `exam_id`, hệ thống dùng giá trị mặc định `EXAM001`.
* File CSV xuất ra dùng mã hóa UTF-8 with BOM để dễ mở bằng các phần mềm bảng tính.
