# custom_structures.py

# --- Cấu trúc mảng ---
class Array:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self.data = [None] * capacity

    def get(self, index):
        self._check_index(index)
        return self.data[index]

    def set(self, index, value):
        self._check_index(index)
        self.data[index] = value

    def __len__(self):
        return self.capacity

    def _check_index(self, index):
        if index < 0 or index >= self.capacity:
            raise IndexError("Chỉ mục vượt quá phạm vi.")


# --- Prefix Sum (Mảng cộng dồn) ---
class PrefixSumArray:
    """
    Mảng cộng dồn, hỗ trợ tính tổng đoạn nhanh O(1).
    Lưu ý: Cấu trúc này là bất biến (immutable) sau khi khởi tạo.
    Nếu mảng gốc thay đổi, cần khởi tạo lại PrefixSumArray.
    """

    def __init__(self, input_array):
        if input_array is None:
            raise ValueError("Input array không hợp lệ.")

        self.n = len(input_array)
        self.prefix_array = Array(self.n) if self.n > 0 else None

        if self.n == 0:
            return

        # Phần tử đầu
        self.prefix_array.set(0, input_array[0])

        # Xây dựng prefix sum
        for i in range(1, self.n):
            value = self.prefix_array.get(i - 1) + input_array[i]
            self.prefix_array.set(i, value)

    def range_sum(self, left, right):
        """
        Tính tổng đoạn từ left → right (bao gồm hai đầu mút).
        Độ phức tạp: O(1).
        """
        if self.n == 0:
            raise IndexError("Mảng rỗng, không thể tính tổng.")
        if not (0 <= left <= right < self.n):
            raise IndexError("Index out of bounds")

        if left == 0:
            return self.prefix_array.get(right)

        return self.prefix_array.get(right) - self.prefix_array.get(left - 1)

    def get_prefix_array(self):
        """Trả về toàn bộ mảng cộng dồn dưới dạng list thường."""
        result = []
        for i in range(self.n):
            result.append(self.prefix_array.get(i))
        return result

    def __len__(self):
        return self.n

    def __str__(self):
        if self.n == 0:
            return "PrefixSumArray:[]"
        values = [str(self.prefix_array.get(i)) for i in range(self.n)]
        return "PrefixSumArray:[" + ", ".join(values) + "]"


# --- HashTable (Bảng băm với chaining) ---
class HashNode:
    """Nút trong bucket của bảng băm."""
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next_node = None


class HashTable:
    """
    Bảng băm, giải quyết xung đột bằng chaining.
    Tự động resize khi load factor vượt ngưỡng LOAD_FACTOR_THRESHOLD.
    """

    LOAD_FACTOR_THRESHOLD = 0.75

    def __init__(self, initial_table_size=100):
        if initial_table_size <= 0:
            raise ValueError("Kích thước mảng băm phải dương.")

        self.table_size = initial_table_size
        self.buckets_array = Array(self.table_size)
        self.item_count = 0

    def hash_index(self, key):
        return hash(key) % self.table_size

    def _should_resize(self):
        return self.item_count / self.table_size > self.LOAD_FACTOR_THRESHOLD

    def _resize(self):
        """Tăng gấp đôi kích thước bảng băm và rehash toàn bộ phần tử."""
        old_buckets = self.buckets_array
        old_size = self.table_size

        self.table_size *= 2
        self.buckets_array = Array(self.table_size)
        self.item_count = 0

        for i in range(old_size):
            current = old_buckets.get(i)
            while current:
                self.put_item(current.key, current.value)
                current = current.next_node

    def put_item(self, key, value):
        """Thêm hoặc cập nhật một cặp key-value."""
        index = self.hash_index(key)
        current_hash_node = self.buckets_array.get(index)

        # Nếu key đã tồn tại → cập nhật value
        while current_hash_node:
            if current_hash_node.key == key:
                current_hash_node.value = value
                return
            current_hash_node = current_hash_node.next_node

        # Thêm node mới vào đầu bucket (prepend)
        new_hash_node = HashNode(key, value)
        new_hash_node.next_node = self.buckets_array.get(index)
        self.buckets_array.set(index, new_hash_node)
        self.item_count += 1

        # Kiểm tra và resize nếu cần
        if self._should_resize():
            self._resize()

    def get_item(self, key):
        """
        Lấy value theo key.
        Raise KeyError nếu key không tồn tại.
        Dùng contains_key() trước nếu không chắc key có tồn tại không.
        """
        index = self.hash_index(key)
        current_hash_node = self.buckets_array.get(index)

        while current_hash_node:
            if current_hash_node.key == key:
                return current_hash_node.value
            current_hash_node = current_hash_node.next_node

        raise KeyError(f"Key '{key}' không tồn tại.")

    def delete_item(self, key):
        """Xóa key khỏi bảng băm. Trả về True nếu thành công, False nếu không tìm thấy."""
        index = self.hash_index(key)
        current_hash_node = self.buckets_array.get(index)
        prev_hash_node = None

        while current_hash_node:
            if current_hash_node.key == key:
                if prev_hash_node:
                    prev_hash_node.next_node = current_hash_node.next_node
                else:
                    self.buckets_array.set(index, current_hash_node.next_node)

                self.item_count -= 1
                return True

            prev_hash_node = current_hash_node
            current_hash_node = current_hash_node.next_node

        return False

    def contains_key(self, key):
        """Kiểm tra key có tồn tại trong bảng băm không."""
        index = self.hash_index(key)
        current_hash_node = self.buckets_array.get(index)

        while current_hash_node:
            if current_hash_node.key == key:
                return True
            current_hash_node = current_hash_node.next_node

        return False

    def __len__(self):
        return self.item_count

    def is_empty(self):
        return self.item_count == 0

    def items(self):
        """Duyệt toàn bộ cặp (key, value) trong bảng băm."""
        for i in range(self.table_size):
            current = self.buckets_array.get(i)
            while current:
                yield (current.key, current.value)
                current = current.next_node


# --- Tệp tin tuần tự ---
class SequentialFile:
    """
    Tệp tin lưu dữ liệu theo thứ tự tuần tự.
    Lưu ý: find() và delete() chỉ xử lý lần xuất hiện ĐẦU TIÊN của value.
    Dùng find_all() và delete_all() nếu cần xử lý toàn bộ.
    """

    def __init__(self):
        self.data = []
        self.size = 0

    def write(self, value):
        """Ghi một giá trị vào cuối tệp."""
        self.data.append(value)
        self.size += 1

    def read(self, index):
        """Đọc giá trị tại vị trí index."""
        if not (0 <= index < self.size):
            raise IndexError("Chỉ mục ngoài phạm vi")
        return self.data[index]

    def read_all(self):
        """Trả về toàn bộ dữ liệu dưới dạng list."""
        return list(self.data)

    def find(self, value):
        """
        Tìm vị trí đầu tiên của value.
        Trả về index nếu tìm thấy, -1 nếu không có.
        """
        for i in range(self.size):
            if self.data[i] == value:
                return i
        return -1

    def find_all(self, value):
        """
        Tìm tất cả vị trí xuất hiện của value.
        Trả về list các index (rỗng nếu không tìm thấy).
        """
        return [i for i in range(self.size) if self.data[i] == value]

    def delete(self, value):
        """
        Xóa lần xuất hiện ĐẦU TIÊN của value.
        Trả về True nếu xóa thành công, False nếu không tìm thấy.
        Dùng delete_all() để xóa tất cả.
        """
        for i in range(self.size):
            if self.data[i] == value:
                for j in range(i, self.size - 1):
                    self.data[j] = self.data[j + 1]
                self.data.pop()
                self.size -= 1
                return True
        return False

    def delete_all(self, value):
        """
        Xóa TẤT CẢ các lần xuất hiện của value.
        Trả về số phần tử đã xóa.
        """
        original_size = self.size
        self.data = [x for x in self.data if x != value]
        self.size = len(self.data)
        return original_size - self.size

    def __len__(self):
        return self.size

    def is_empty(self):
        return self.size == 0

    def __str__(self):
        return "SequentialFile:" + str(self.data)
