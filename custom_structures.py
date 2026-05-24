# custom_structures.py
# Các cấu trúc dữ liệu tự cài đặt.


# --- Node danh sách liên kết cho bảng băm ---

class HashNode:
    """Node trong chuỗi liên kết của bảng băm."""

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None  # Node tiếp theo trong cùng bucket.

    def __repr__(self):
        return f"HashNode({self.key!r}: {self.value!r})"


# --- HashTable (Bảng băm với giải quyết xung đột bằng chaining) ---

class HashTable:
    """
    Bảng băm tự cài đặt với cơ chế chuỗi riêng.
    """

    DEFAULT_CAPACITY = 64
    LOAD_FACTOR_THRESHOLD = 0.75  # Ngưỡng mở rộng bảng.

    def __init__(self, capacity: int = DEFAULT_CAPACITY):
        self.capacity = capacity
        self.size = 0                          # Số cặp key-value đang lưu.
        self.buckets = [None] * self.capacity  # Mảng bucket.

    # Hàm băm chính.

    def _hash(self, key) -> int:
        """Tính hash bằng polynomial rolling hash."""
        h = 0
        for ch in str(key):
            h = (h * 31 + ord(ch)) % self.capacity
        return h

    # Các thao tác chính.

    def put(self, key, value) -> None:
        """Thêm hoặc cập nhật một cặp key-value."""
        # Mở rộng bảng trước khi vượt ngưỡng tải.
        if self.size / self.capacity >= self.LOAD_FACTOR_THRESHOLD:
            self._resize()

        idx = self._hash(key)
        node = self.buckets[idx]

        # Cập nhật nếu key đã tồn tại.
        while node:
            if node.key == key:
                node.value = value
                return
            node = node.next

        # Thêm node mới vào đầu chuỗi.
        new_node = HashNode(key, value)
        new_node.next = self.buckets[idx]
        self.buckets[idx] = new_node
        self.size += 1

    def get(self, key, default=None):
        """Trả về giá trị theo key, hoặc default nếu không tìm thấy."""
        idx = self._hash(key)
        node = self.buckets[idx]
        while node:
            if node.key == key:
                return node.value
            node = node.next
        return default

    def remove(self, key) -> bool:
        """Xóa một cặp key-value."""
        idx = self._hash(key)
        node = self.buckets[idx]
        prev = None

        while node:
            if node.key == key:
                if prev:
                    prev.next = node.next
                else:
                    self.buckets[idx] = node.next
                self.size -= 1
                return True
            prev = node
            node = node.next
        return False

    def contains(self, key) -> bool:
        """Kiểm tra key có tồn tại hay không."""
        return self.get(key) is not None

    # Duyệt toàn bộ bảng băm.

    def keys(self) -> list:
        """Trả về tất cả key."""
        result = []
        for bucket in self.buckets:
            node = bucket
            while node:
                result.append(node.key)
                node = node.next
        return result

    def values(self) -> list:
        """Trả về tất cả value."""
        result = []
        for bucket in self.buckets:
            node = bucket
            while node:
                result.append(node.value)
                node = node.next
        return result

    def items(self) -> list:
        """Trả về tất cả cặp (key, value)."""
        result = []
        for bucket in self.buckets:
            node = bucket
            while node:
                result.append((node.key, node.value))
                node = node.next
        return result

    # Mở rộng khi vượt ngưỡng tải.

    def _resize(self) -> None:
        """Tăng gấp đôi dung lượng và hash lại dữ liệu."""
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [None] * self.capacity
        self.size = 0

        for bucket in old_buckets:
            node = bucket
            while node:
                self.put(node.key, node.value)
                node = node.next

    def __len__(self):
        return self.size

    def __repr__(self):
        return f"HashTable(size={self.size}, capacity={self.capacity})"


# --- List (Danh sách - Mảng động tùy chỉnh) ---

class List:
    """Mảng động tùy chỉnh, tự mở rộng khi hết chỗ."""

    _MIN_CAPACITY = 8

    def __init__(self, initial_capacity: int = _MIN_CAPACITY):
        self._capacity = max(int(initial_capacity), self._MIN_CAPACITY)
        self._size = 0
        self._elements = [None] * self._capacity

    def append(self, item) -> None:
        """Thêm phần tử vào cuối danh sách."""
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._elements[self._size] = item
        self._size += 1

    def get(self, index):
        """Lấy phần tử tại chỉ mục, hỗ trợ chỉ mục âm."""
        index = self._normalize_existing_index(index)
        return self._elements[index]

    def set(self, index, item) -> None:
        """Đặt giá trị phần tử tại chỉ mục, hỗ trợ chỉ mục âm."""
        index = self._normalize_existing_index(index)
        self._elements[index] = item

    def insert(self, index, item) -> None:
        """Chèn phần tử vào chỉ mục."""
        if index < 0:
            index = max(0, index + self._size)
        if not (0 <= index <= self._size):
            raise IndexError("List: Chỉ mục chèn ngoài phạm vi")

        if self._size == self._capacity:
            self._resize(self._capacity * 2)

        for i in range(self._size, index, -1):
            self._elements[i] = self._elements[i - 1]
        self._elements[index] = item
        self._size += 1

    def pop(self, index=-1):
        """Xóa và trả về phần tử tại chỉ mục, mặc định là cuối danh sách."""
        if self.is_empty():
            raise IndexError("List: Pop từ danh sách rỗng")

        index = self._normalize_existing_index(index)
        item = self._elements[index]
        for i in range(index, self._size - 1):
            self._elements[i] = self._elements[i + 1]
        self._size -= 1
        self._elements[self._size] = None

        if self._size < self._capacity // 4 and self._capacity // 2 >= self._MIN_CAPACITY:
            self._resize(self._capacity // 2)

        return item

    def is_empty(self) -> bool:
        return self._size == 0

    def to_list(self) -> list:
        return [self._elements[i] for i in range(self._size)]

    def _resize(self, new_capacity: int) -> None:
        new_capacity = max(new_capacity, self._MIN_CAPACITY)
        new_elements = [None] * new_capacity
        for i in range(self._size):
            new_elements[i] = self._elements[i]
        self._elements = new_elements
        self._capacity = new_capacity

    def _normalize_existing_index(self, index: int) -> int:
        if index < 0:
            index += self._size
        if not (0 <= index < self._size):
            raise IndexError("List: Chỉ mục ngoài phạm vi")
        return index

    def __len__(self):
        return self._size

    def __iter__(self):
        for i in range(self._size):
            yield self._elements[i]

    def __getitem__(self, index):
        return self.get(index)

    def __setitem__(self, index, value):
        self.set(index, value)

    def __repr__(self):
        return f"List({self.to_list()})"

    def __str__(self):
        if self.is_empty():
            return "List:[]"
        return "List:[" + ", ".join(str(item) for item in self) + "]"


# --- Merge Sort (Sắp xếp trộn tự cài đặt) ---

def merge_sort(arr: list, key=lambda x: x, reverse: bool = False) -> list:
    """Sắp xếp bằng merge sort và trả về list mới."""
    if len(arr) <= 1:
        return arr[:]

    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key=key, reverse=reverse)
    right = merge_sort(arr[mid:], key=key, reverse=reverse)
    return _merge(left, right, key, reverse)


def _merge(left: list, right: list, key, reverse: bool) -> list:
    result = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        left_key = key(left[i])
        right_key = key(right[j])
        take_left = left_key >= right_key if reverse else left_key <= right_key

        if take_left:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


# --- MinHeap (Đống cực tiểu) ---

class MinHeap:
    """Min-heap tự cài đặt, ưu tiên phần tử có priority nhỏ nhất."""

    def __init__(self):
        self._data = []

    def push(self, priority, value) -> None:
        self._data.append((priority, value))
        self._sift_up(len(self._data) - 1)

    def pop(self):
        if not self._data:
            raise IndexError("MinHeap: Pop từ đống rỗng")

        self._swap(0, len(self._data) - 1)
        item = self._data.pop()
        if self._data:
            self._sift_down(0)
        return item

    def peek(self):
        if not self._data:
            raise IndexError("MinHeap: Peek từ đống rỗng")
        return self._data[0]

    def _sift_up(self, i: int) -> None:
        while i > 0:
            parent = (i - 1) // 2
            if self._data[parent][0] <= self._data[i][0]:
                break
            self._swap(parent, i)
            i = parent

    def _sift_down(self, i: int) -> None:
        n = len(self._data)
        while True:
            smallest = i
            left = 2 * i + 1
            right = 2 * i + 2

            if left < n and self._data[left][0] < self._data[smallest][0]:
                smallest = left
            if right < n and self._data[right][0] < self._data[smallest][0]:
                smallest = right
            if smallest == i:
                break

            self._swap(i, smallest)
            i = smallest

    def _swap(self, i: int, j: int) -> None:
        self._data[i], self._data[j] = self._data[j], self._data[i]

    def __len__(self):
        return len(self._data)


# --- PrefixTrie (Cây tiền tố cho autocomplete) ---

class TrieNode:
    """Node trong cây tiền tố."""

    def __init__(self):
        self.children = HashTable()
        self.values = []
        self.is_end = False


class PrefixTrie:
    """Trie dùng cho autocomplete theo tiền tố chuỗi."""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, key: str, value=None) -> None:
        key = str(key).strip()
        if not key:
            return

        current = self.root
        for char in key.lower():
            child = current.children.get(char)
            if child is None:
                child = TrieNode()
                current.children.put(char, child)
            current = child

        current.is_end = True
        final_value = key if value is None else value
        if final_value not in current.values:
            current.values.append(final_value)

    def autocomplete(self, prefix: str, limit: int = 8) -> list:
        prefix = str(prefix).strip().lower()
        if not prefix or limit <= 0:
            return []

        current = self.root
        for char in prefix:
            current = current.children.get(char)
            if current is None:
                return []

        results = []
        self._collect(current, results, limit)
        return results

    def _collect(self, node: TrieNode, results: list, limit: int) -> None:
        if len(results) >= limit:
            return

        if node.is_end:
            for value in node.values:
                if len(results) >= limit:
                    return
                results.append(value)

        child_keys = merge_sort(node.children.keys(), key=lambda item: item)
        for key in child_keys:
            if len(results) >= limit:
                return
            self._collect(node.children.get(key), results, limit)
