#custom_structures.py

# ---Cấu trúc mảng
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
    """Mảng cộng dồn, hỗ trợ tính tổng đoạn nhanh O(1)."""

    def __init__(self, input_array):
        if input_array is None:
            raise ValueError("Input array không hợp lệ.")

        self.n = len(input_array)
        self.prefix_array = Array(self.n)

        if self.n == 0:
            return

        # phần tử đầu
        self.prefix_array.set(0, input_array[0])

        # xây dựng prefix sum
        for i in range(1, self.n):
            value = self.prefix_array.get(i - 1) + input_array[i]
            self.prefix_array.set(i, value)

    def range_sum(self, left, right):
        """Tính tổng đoạn từ left → right (bao gồm)."""
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
        values = []
        for i in range(self.n):
            values.append(str(self.prefix_array.get(i)))
        return "PrefixSumArray:[" + ", ".join(values) + "]"

# --- HashTable (Bảng băm với giải quyết xung đột bằng chaining) ---
class HashNode:
      """Nút trong bucket của bảng băm."""
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next_node = None

class HashTable:
    """Bảng băm, giải quyết xung đột bằng chaining."""
    def __init__(self, initial_table_size=100):
        if initial_table_size <= 0:
            raise ValueError("Kích thước mảng băm phải dương.")

        self.table_size = initial_table_size
        self.buckets_array = Array(self.table_size)  # dùng Array tự cài
        self.item_count = 0

    def hash_index(self, key):
        # Tính chỉ mục bucket cho khóa.
        return hash(key) % self.table_size

    def put_item(self, key, value):
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

    def get_item(self, key):
        index = self.hash_index(key)
        current_hash_node = self.buckets_array.get(index)

        while current_hash_node:
            if current_hash_node.key == key:
                return current_hash_node.value
            current_hash_node = current_hash_node.next_node

        return None

    def delete_item(self, key):
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

    def get_all_values_as_list(self):
        values_custom_list = []

        for i in range(self.table_size):
            current_hash_node = self.buckets_array.get(i)
            while current_hash_node:
                values_custom_list.append(current_hash_node.value)
                current_hash_node = current_hash_node.next_node

        return values_custom_list

    def get_all_key_value_pairs_as_list(self):
        pairs_custom_list = []

        for i in range(self.table_size):
            current_hash_node = self.buckets_array.get(i)
            while current_hash_node:
                pairs_custom_list.append(
                    (current_hash_node.key, current_hash_node.value)
                )
                current_hash_node = current_hash_node.next_node

        return pairs_custom_list

    def items(self):
        for i in range(self.table_size):
            current = self.buckets_array.get(i)
            while current:
                yield (current.key, current.value)
                current = current.next_node

# --- Tệp tin tuần tự ---
class SequentialFile:
    """Tệp tin lưu dữ liệu theo thứ tự tuần tự."""
    def __init__(self):
        self.data = []  # mô phỏng file lưu trữ tuần tự
        self.size = 0

    # ===== GHI (append vào cuối file) =====
    def write(self, value):
        self.data.append(value)
        self.size += 1

    # ===== ĐỌC THEO INDEX =====
    def read(self, index):
        if not (0 <= index < self.size):
            raise IndexError("Chỉ mục ngoài phạm vi")
        return self.data[index]

    # ===== DUYỆT TOÀN BỘ FILE =====
    def read_all(self):
        result = []
        for i in range(self.size):
            result.append(self.data[i])
        return result

    # ===== TÌM KIẾM TUẦN TỰ =====
    def find(self, value):
        for i in range(self.size):
            if self.data[i] == value:
                return i
        return -1

    # ===== XÓA (phải dịch trái) =====
    def delete(self, value):
        for i in range(self.size):
            if self.data[i] == value:
                for j in range(i, self.size - 1):
                    self.data[j] = self.data[j + 1]

                self.data.pop()
                self.size -= 1
                return True
        return False

    def __len__(self):
        return self.size

    def is_empty(self):
        return self.size == 0

    def __str__(self):
        return "SequentialFile:" + str(self.data)
