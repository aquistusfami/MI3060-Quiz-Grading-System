# custom_structures.py

# --- Cấu trúc mảng ---
class Array:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("Capacity phải dương")

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
        self.item_count = 0  # reset để put_item đếm lại chính xác khi rehash

        for i in range(old_size):
            current = old_buckets.get(i)
            while current:
                self.put_item(current.key, current.value)
                current = current.next_node

    def put_item(self, key, value):
        """Thêm hoặc cập nhật một cặp key-value."""
        index = self.hash_index(key)
        current_hash_node = self.buckets_array.get(index)

        while current_hash_node:
            if current_hash_node.key == key:
                current_hash_node.value = value
                return
            current_hash_node = current_hash_node.next_node

        new_hash_node = HashNode(key, value)
        new_hash_node.next_node = self.buckets_array.get(index)
        self.buckets_array.set(index, new_hash_node)
        self.item_count += 1

        if self._should_resize():
            self._resize()

    def get_item(self, key):
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


# --- CounterArray (Mảng đếm) ---
class CounterArray:
    def __init__(self, size):
        if size <= 0:
            raise ValueError("Kích thước mảng đếm phải dương.")
        self.size = size
        self._data = Array(size)
        for i in range(size):
            self._data.set(i, 0)

    def increment(self, index):
        """Tăng giá trị tại vị trí index lên 1. Độ phức tạp: O(1)."""
        self._data.set(index, self._data.get(index) + 1)

    def get(self, index):
        """Lấy giá trị tại vị trí index. Độ phức tạp: O(1)."""
        return self._data.get(index)

    def __len__(self):
        return self.size

    def __str__(self):
        values = [str(self._data.get(i)) for i in range(self.size)]
        return "CounterArray:[" + ", ".join(values) + "]"


# --- Tệp tin tuần tự ---
class SequentialFile:
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
        for i in range(self.size):
            if self.data[i] == value:
                return i
        return -1

    def find_all(self, value):
        return [i for i in range(self.size) if self.data[i] == value]

    def delete(self, value):
        for i in range(self.size):
            if self.data[i] == value:
                self.data.pop(i)
                self.size -= 1
                return True
        return False

    def delete_all(self, value):
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
