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
* `custom_structures.py`: Chứa các cấu trúc dữ liệu và giải thuật tự cài đặt, gồm `HashTable`, `List`, `MinHeap`, `PrefixTrie`, `merge_sort`.
* `ui/`: Chia nhỏ giao diện thành các module tab độc lập, gồm tab kết quả, quản lý đáp án, danh sách lớp học phần, thống kê câu hỏi, tìm kiếm thí sinh và widget dùng chung.
* `scripts/generate_perf_data.py`: Sinh bộ dữ liệu lớn để kiểm thử hiệu năng.
* `scripts/benchmark_algorithms.py`: Đo thời gian thực thi các thao tác chính trên dữ liệu lớn.
* `data/`: Chứa dữ liệu mẫu của đề thi, đáp án và bài làm sinh viên.
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
* **Thống kê câu hỏi**: Tính số người đúng, sai và tỷ lệ đúng của từng câu hỏi.
* **Phân tích câu hỏi khó**: Dùng heap để lấy các câu hỏi có tỷ lệ đúng thấp nhất.
* **Xuất dữ liệu**: Xuất bảng điểm và thống kê câu hỏi ra file CSV.

Dữ liệu của hệ thống được lưu trữ trong các tệp CSV như `answer_key.csv`, `students.csv`, `exams.csv`. Kết quả sau khi xử lý được xuất ra thư mục `output/`.

## 4. Cấu trúc dữ liệu và giải thuật sử dụng

| Thành phần | Cấu trúc dữ liệu / giải thuật | Mục đích | Độ phức tạp chính |
|---|---|---|---|
| Lưu đáp án và kết quả | `HashTable` | Tra cứu nhanh đáp án theo `exam_id` và `question_id`, tra cứu kết quả theo MSSV | Trung bình `O(1)` |
| Lưu danh sách sinh viên | `List` | Lưu dữ liệu bài làm theo thứ tự đọc từ CSV | Truy cập `O(1)`, thêm cuối trung bình `O(1)` |
| Đếm thống kê câu hỏi | `HashTable` | Gom nhóm số đúng và tổng lượt trả lời theo kỳ thi, câu hỏi | Trung bình `O(1)` mỗi cập nhật |
| Sắp xếp kết quả | `merge_sort` | Sắp xếp ổn định theo điểm và các tiêu chí phụ | `O(n log n)` |
| Gợi ý tìm kiếm | `PrefixTrie` | Gợi ý MSSV và họ tên theo tiền tố | `O(k + m)` |
| Câu hỏi khó nhất | `MinHeap` | Lấy các câu có tỷ lệ đúng thấp nhất | `O(q log q)` |
| Lọc khoảng điểm | Chỉ mục điểm + tìm kiếm nhị phân | Truy vấn sinh viên trong khoảng điểm | `O(log n + m)` |

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
| `question_id` | Số thứ tự câu hỏi, bắt đầu từ 1 | `1` |
| `correct_answer` | Đáp án đúng dạng chuỗi tùy chỉnh | `A, E`, `503`, `33.3` |

Ví dụ:

```csv
exam_id,question_id,correct_answer
EXAM001,1,"A, E"
EXAM001,2,503
EXAM001,3,33.3
```

### 5.2. File bài làm sinh viên

File mẫu: `data/students.csv`

Các cột thường dùng:

| Cột | Ý nghĩa | Ví dụ |
|---|---|---|
| `exam_id` | Mã kỳ thi hoặc mã đề | `EXAM001` |
| `ma_hp` | Mã học phần | `MI1111` |
| `hoc_ky` | Học kỳ | `20252` |
| `id_lop_hp` | ID lớp học phần | `163613` |
| `mssv` | Mã số sinh viên | `20230001` |
| `ho_ten` | Họ tên sinh viên | `Nguyen Van An` |
| `ma_lop` | Mã lớp hành chính | `23D1` |
| `ten_lop` | Tên lớp hành chính | `Toan Tin K69 - Nhom 1` |
| `q1`, `q2`, ... | Câu trả lời dạng chuỗi tùy chỉnh hoặc để trống | `A, E`, `503`, `33.3` |

Ví dụ:

```csv
exam_id,ma_hp,hoc_ky,id_lop_hp,mssv,ho_ten,ma_lop,ten_lop,q1,q2,q3
EXAM001,MI1111,20252,163613,20230001,Nguyen Van An,23D1,Toan Tin K69 - Nhom 1,A,C,B
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

### 6.1. Yêu cầu chung

* Python 3.10 trở lên. Khuyến nghị Python 3.11, 3.12 hoặc 3.13.
* `pip` và module tạo môi trường ảo `venv`.
* Tkinter/Tcl-Tk để hiển thị giao diện.
* Thư viện `customtkinter`, được khai báo trong `requirements.txt`.
* Môi trường có giao diện đồ họa. Máy chủ Linux không có desktop hoặc không có biến `DISPLAY` chỉ phù hợp để chạy test và benchmark.

Kiểm tra phiên bản Python:

```bash
python3 --version
```

Trên Windows có thể dùng:

```powershell
py --version
```

Kiểm tra Tkinter đã hoạt động:

```bash
python3 -m tkinter
```

Trên Windows:

```powershell
py -m tkinter
```

Nếu Tkinter được cài đúng, một cửa sổ kiểm tra nhỏ sẽ xuất hiện.

### 6.2. Tải mã nguồn

Người dùng Git có thể clone repository:

```bash
git clone https://github.com/aquistusfami/MI3060-Quiz-Grading-System.git
cd MI3060-Quiz-Grading-System
```

Người dùng không sử dụng Git có thể tải file ZIP từ GitHub, giải nén và mở terminal tại thư mục chứa `main_gui.py`.

### 6.3. Windows 10/11

1. Cài Python từ trang chính thức của Python. Khi dùng bộ cài truyền thống, nên bật tùy chọn thêm Python vào `PATH`.
2. Mở PowerShell tại thư mục project.
3. Tạo và kích hoạt môi trường ảo:

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Nếu dùng Command Prompt thay cho PowerShell:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
```

4. Cài thư viện và chạy chương trình:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_gui.py
```

Nếu lệnh `py` không tồn tại nhưng `python` hoạt động, thay `py` bằng `python`.

### 6.4. macOS

#### Cách 1: Python từ python.org

Bộ cài Python chính thức thường đi kèm Tcl/Tk. Sau khi cài, mở Terminal tại thư mục project và chạy:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_gui.py
```

#### Cách 2: Homebrew

Ví dụ với Python 3.13:

```bash
brew install python@3.13 python-tk@3.13
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_gui.py
```

Phiên bản của `python-tk` phải tương ứng với phiên bản Python do Homebrew cài đặt.

### 6.5. Ubuntu và Debian

Cài Python, `venv`, `pip` và Tkinter:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-tk
```

Tạo môi trường và chạy ứng dụng:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_gui.py
```

### 6.6. Fedora Workstation

Cài các thành phần cần thiết:

```bash
sudo dnf install python3 python3-pip python3-tkinter
```

Tạo môi trường và chạy ứng dụng:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_gui.py
```

### 6.7. Arch Linux và Manjaro

Cài Python, pip và Tk:

```bash
sudo pacman -S python python-pip tk
```

Tạo môi trường và chạy ứng dụng:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_gui.py
```

### 6.8. Sử dụng giao diện

Sau khi chạy, chương trình mặc định đọc:

* `data/answer_key.csv`
* `data/students.csv`
* `data/exams.csv`

Quy trình sử dụng cơ bản:

1. Kiểm tra hoặc chọn file đáp án trên thanh công cụ.
2. Chọn file bài làm sinh viên.
3. Nhấn `CHẤM ĐIỂM`.
4. Xem kết quả, xếp hạng, thống kê lớp và thống kê câu hỏi ở các tab tương ứng.
5. Dùng chức năng xuất CSV để lưu bảng điểm hoặc thống kê vào thư mục mong muốn.

### 6.9. Chạy kiểm thử dành cho người phát triển

Kích hoạt môi trường ảo trước, sau đó chạy:

```bash
python -m unittest discover -s tests -v
```

Bộ kiểm thử chính nằm trong `tests/test_quiz_grading.py`. Các file `test_part1_business.py` đến `test_part4_business.py` là các điểm chạy tương thích và đều gọi lại bộ test hiện tại.

### 6.10. Chạy benchmark không cần giao diện

Benchmark có thể chạy trên máy không có desktop vì không khởi tạo cửa sổ Tkinter:

```bash
python scripts/generate_perf_data.py
python scripts/benchmark_algorithms.py
```

Lệnh sinh dữ liệu ghi đè các file trong `data/performance/`.

### 6.11. Lỗi thường gặp

#### `ModuleNotFoundError: No module named 'customtkinter'`

Môi trường ảo chưa được kích hoạt hoặc chưa cài thư viện:

```bash
python -m pip install -r requirements.txt
```

#### `ModuleNotFoundError: No module named 'tkinter'`

* Ubuntu/Debian: `sudo apt install python3-tk`
* Fedora: `sudo dnf install python3-tkinter`
* Arch/Manjaro: `sudo pacman -S tk`
* macOS Homebrew: cài `python-tk` đúng phiên bản Python.
* Windows/macOS dùng Python từ python.org: chạy lại bộ cài Python và bảo đảm thành phần Tcl/Tk được cài.

#### Linux báo `no display name and no $DISPLAY environment variable`

Ứng dụng GUI đang được chạy trong môi trường không có màn hình, ví dụ SSH hoặc container. Hãy chạy trên phiên desktop, cấu hình X11 forwarding, hoặc chỉ chạy test/benchmark.

#### PowerShell không cho kích hoạt môi trường ảo

Chỉ nới chính sách trong phiên PowerShell hiện tại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

#### Lỗi font của CustomTkinter trên Linux

Ứng dụng vẫn có thể chạy với phương thức vẽ thay thế. Nếu giao diện hiển thị kém, kiểm tra quyền ghi thư mục font người dùng và bảo đảm hệ thống có bộ font desktop thông thường.

## 7. Các màn hình chính

* **Kết quả & Xếp hạng**: Hiển thị bảng điểm, bộ lọc điểm, bộ lọc kỳ thi, bộ lọc lớp học phần và chi tiết đáp án của sinh viên được chọn.
* **Quản lý đáp án**: Thêm, sửa, xóa, nạp và lưu kho đáp án CSV.
* **Danh sách lớp HP**: Hiển thị thống kê theo lớp học phần và danh sách sinh viên sau khi chấm điểm.
* **Thống kê câu hỏi**: Hiển thị số người đúng, sai, tỷ lệ đúng và top câu hỏi khó.
* **Tìm kiếm thí sinh**: Tra cứu kết quả theo MSSV hoặc họ tên, hỗ trợ gợi ý bằng Trie.

## 8. Dữ liệu và đo hiệu năng

### 8.1. Sinh dữ liệu lớn

```bash
python scripts/generate_perf_data.py
```

Dữ liệu hiệu năng được tạo tại `data/performance/`, gồm:

* 5 kỳ thi.
* 100 câu hỏi cho mỗi kỳ thi.
* 10.000 sinh viên.

### 8.2. Chạy benchmark

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
