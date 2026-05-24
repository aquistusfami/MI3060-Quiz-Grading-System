import unittest

from custom_structures import HashTable, List, MinHeap, PrefixTrie


class ConstantHashKey:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "same-bucket"

    def __eq__(self, other):
        return isinstance(other, ConstantHashKey) and self.value == other.value

    def __hash__(self):
        return hash(self.value)


class CustomStructureTests(unittest.TestCase):
    def test_hash_table_insert_update_remove_and_collision_lookup(self):
        table = HashTable(capacity=4)
        key_a = ConstantHashKey("A")
        key_b = ConstantHashKey("B")

        table.put(key_a, "first")
        table.put(key_b, "second")
        table.put("plain", "value")
        table.put(key_a, "updated")

        self.assertEqual(table.get(key_a), "updated")
        self.assertEqual(table.get(key_b), "second")
        self.assertEqual(table.get("plain"), "value")
        self.assertTrue(table.remove(key_b))
        self.assertIsNone(table.get(key_b))
        self.assertFalse(table.remove(key_b))

    def test_hash_table_resizes_and_keeps_values(self):
        table = HashTable(capacity=4)
        for index in range(20):
            table.put(f"key-{index}", index)

        self.assertGreaterEqual(table.capacity, 32)
        for index in range(20):
            self.assertEqual(table.get(f"key-{index}"), index)

    def test_list_append_insert_pop_negative_index_and_shrink(self):
        items = List(initial_capacity=8)
        for value in range(20):
            items.append(value)

        items.insert(1, 99)
        self.assertEqual(items.get(1), 99)
        self.assertEqual(items[-1], 19)
        self.assertEqual(items.pop(1), 99)

        while len(items) > 2:
            items.pop()

        self.assertEqual(items.to_list(), [0, 1])
        self.assertGreaterEqual(items._capacity, 8)

    def test_min_heap_returns_items_by_priority(self):
        heap = MinHeap()
        heap.push((3, "c"), "third")
        heap.push((1, "a"), "first")
        heap.push((2, "b"), "second")

        self.assertEqual(heap.pop()[1], "first")
        self.assertEqual(heap.pop()[1], "second")
        self.assertEqual(heap.pop()[1], "third")

        with self.assertRaises(IndexError):
            heap.pop()

    def test_prefix_trie_autocomplete_limit_duplicate_and_sorted_traversal(self):
        trie = PrefixTrie()
        trie.insert("20230003")
        trie.insert("20230001")
        trie.insert("20230002")
        trie.insert("20230002")
        trie.insert("20240001")

        self.assertEqual(
            trie.autocomplete("2023", limit=10),
            ["20230001", "20230002", "20230003"],
        )
        self.assertEqual(trie.autocomplete("2023", limit=2), ["20230001", "20230002"])
        self.assertEqual(trie.autocomplete("9999"), [])


if __name__ == "__main__":
    unittest.main()
