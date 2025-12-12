"""Benchmark memory management operations to measure GC and allocation performance."""

import gc
import sys


class TestObjectAllocation:
    """Test object allocation performance - measures memory allocator efficiency."""

    def test_benchmark_list_creation(self, benchmark):
        """Benchmark list creation - measures sequence allocation."""
        result = benchmark(list, range(10000))
        assert len(result) == 10000

    def test_benchmark_dict_creation(self, benchmark):
        """Benchmark dict creation - measures hash table allocation."""
        result = benchmark(dict, [(i, i * 2) for i in range(10000)])
        assert len(result) == 10000

    def test_benchmark_set_creation(self, benchmark):
        """Benchmark set creation - measures hash set allocation."""
        result = benchmark(set, range(10000))
        assert len(result) == 10000

    def test_benchmark_tuple_creation(self, benchmark):
        """Benchmark tuple creation - measures immutable sequence allocation."""
        result = benchmark(tuple, range(10000))
        assert len(result) == 10000

    def test_benchmark_object_creation(self, benchmark):
        """Benchmark custom object creation - measures class instance allocation."""

        class SimpleObject:
            def __init__(self, value):
                self.value = value

        def create_objects():
            return [SimpleObject(i) for i in range(1000)]

        result = benchmark(create_objects)
        assert len(result) == 1000


class TestMemoryReuse:
    """Test memory reuse patterns - measures allocator caching."""

    def test_benchmark_list_append_realloc(self, benchmark):
        """Benchmark list append with reallocations - measures resize overhead."""

        def append_many():
            lst = []
            for i in range(10000):
                lst.append(i)
            return lst

        result = benchmark(append_many)
        assert len(result) == 10000

    def test_benchmark_list_preallocated(self, benchmark):
        """Benchmark list with preallocation - no resizing."""

        def preallocated():
            lst = [None] * 10000
            for i in range(10000):
                lst[i] = i
            return lst

        result = benchmark(preallocated)
        assert len(result) == 10000

    def test_benchmark_dict_preallocated(self, benchmark):
        """Benchmark dict with preallocation hint."""

        def create_dict():
            d = {}
            for i in range(10000):
                d[i] = i * 2
            return d

        result = benchmark(create_dict)
        assert len(result) == 10000


class TestGarbageCollection:
    """Test garbage collection performance - measures GC overhead."""

    def test_benchmark_gc_collect(self, benchmark):
        """Benchmark explicit garbage collection - measures GC cycle time."""

        # Create garbage
        def create_garbage():
            garbage = []
            for _ in range(1000):
                obj = {"data": list(range(100))}
                garbage.append(obj)
            garbage.clear()

        create_garbage()

        result = benchmark(gc.collect)
        assert result >= 0

    def test_benchmark_reference_cycles(self, benchmark):
        """Benchmark reference cycle creation and collection."""

        def create_cycles():
            gc.disable()
            try:
                objects = []
                # Reduced from 1000 to 100 to avoid memory pressure
                for _ in range(100):
                    obj1 = {}
                    obj2 = {}
                    obj1["ref"] = obj2
                    obj2["ref"] = obj1
                    objects.append(obj1)
                objects.clear()
                return gc.collect()
            finally:
                gc.enable()

        result = benchmark(create_cycles)
        assert result >= 0

    def test_benchmark_weakref_overhead(self, benchmark):
        """Benchmark weak reference overhead."""
        import weakref

        class WeakRefable:
            """Object that supports weak references."""

        def create_weakrefs():
            objects = [WeakRefable() for _ in range(1000)]
            weakrefs = [weakref.ref(obj) for obj in objects]
            # Keep objects alive
            return len([wr() for wr in weakrefs if wr() is not None])

        result = benchmark(create_weakrefs)
        assert result == 1000

    def test_benchmark_gc_disabled(self, benchmark):
        """Benchmark with GC disabled - measures allocation without GC overhead."""

        def allocate_without_gc():
            gc.disable()
            try:
                objects = [list(range(100)) for _ in range(1000)]
                return len(objects)
            finally:
                gc.enable()
                gc.collect()

        result = benchmark(allocate_without_gc)
        assert result == 1000


class TestReferenceCounting:
    """Test reference counting overhead - measures refcount operations."""

    def test_benchmark_reference_increment(self, benchmark):
        """Benchmark reference increment/decrement - measures refcount overhead."""

        def ref_counting():
            obj = [1, 2, 3, 4, 5]
            refs = []
            # Create references
            for _ in range(1000):
                refs.append(obj)
            # Delete references
            refs.clear()
            return sys.getrefcount(obj)

        result = benchmark(ref_counting)
        assert result >= 2  # Function locals + argument

    def test_benchmark_container_references(self, benchmark):
        """Benchmark container reference management."""

        def container_refs():
            items = list(range(1000))
            containers = []
            for _ in range(100):
                containers.append(items[:])  # Shallow copy
            return len(containers)

        result = benchmark(container_refs)
        assert result == 100


class TestMemoryLayout:
    """Test memory layout and alignment - measures cache efficiency."""

    def test_benchmark_slots_vs_dict(self, benchmark):
        """Benchmark __slots__ vs __dict__ - measures memory layout overhead."""

        class WithDict:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        def create_dict_objects():
            return [WithDict(i, i * 2) for i in range(1000)]

        result = benchmark(create_dict_objects)
        assert len(result) == 1000

    def test_benchmark_slots_class(self, benchmark):
        """Benchmark class with __slots__ - optimized memory layout."""

        class WithSlots:
            __slots__ = ["x", "y"]

            def __init__(self, x, y):
                self.x = x
                self.y = y

        def create_slots_objects():
            return [WithSlots(i, i * 2) for i in range(1000)]

        result = benchmark(create_slots_objects)
        assert len(result) == 1000


class TestStringOperations:
    """Test string operations - measures string interning and allocation."""

    def test_benchmark_string_concatenation(self, benchmark):
        """Benchmark string concatenation - measures repeated allocation."""

        def concat_strings():
            s = ""
            for i in range(1000):
                s += str(i)
            return s

        result = benchmark(concat_strings)
        assert len(result) > 0

    def test_benchmark_string_join(self, benchmark):
        """Benchmark string join - optimized allocation."""

        def join_strings():
            return "".join(str(i) for i in range(1000))

        result = benchmark(join_strings)
        assert len(result) > 0

    def test_benchmark_string_formatting(self, benchmark):
        """Benchmark f-string formatting - measures format overhead."""

        def format_strings():
            return [f"value_{i}" for i in range(1000)]

        result = benchmark(format_strings)
        assert len(result) == 1000

    def test_benchmark_string_interning(self, benchmark):
        """Benchmark string interning - measures intern cache."""

        def intern_strings():
            # Short strings are automatically interned
            strings = []
            for i in range(1000):
                strings.append(f"s{i}")
            return strings

        result = benchmark(intern_strings)
        assert len(result) == 1000


class TestBufferProtocol:
    """Test buffer protocol operations - measures zero-copy performance."""

    def test_benchmark_memoryview_creation(self, benchmark):
        """Benchmark memoryview creation - zero-copy view."""
        data = bytearray(10000)
        result = benchmark(memoryview, data)
        assert len(result) == 10000

    def test_benchmark_memoryview_slicing(self, benchmark):
        """Benchmark memoryview slicing - view operations."""
        data = bytearray(10000)
        view = memoryview(data)
        result = benchmark(lambda v: v[100:200], view)
        assert len(result) == 100

    def test_benchmark_bytes_vs_bytearray(self, benchmark):
        """Benchmark bytes (immutable) vs bytearray (mutable)."""

        def create_bytearray():
            ba = bytearray(10000)
            for i in range(100):
                ba[i] = i % 256
            return ba

        result = benchmark(create_bytearray)
        assert len(result) == 10000


class TestCaching:
    """Test caching and memoization - measures cache effectiveness."""

    def test_benchmark_lru_cache(self, benchmark):
        """Benchmark LRU cache - measures cache overhead and hit rate."""
        from functools import lru_cache

        @lru_cache(maxsize=128)
        def fibonacci(n):
            if n < 2:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)

        def compute_fib():
            results = []
            for i in range(20):
                results.append(fibonacci(i))
            return results

        # Warm up cache
        compute_fib()

        result = benchmark(compute_fib)
        assert len(result) == 20

    def test_benchmark_no_cache(self, benchmark):
        """Benchmark without cache - baseline for comparison."""

        def fibonacci(n):
            if n < 2:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)

        def compute_fib():
            results = []
            for i in range(15):  # Smaller range without caching
                results.append(fibonacci(i))
            return results

        result = benchmark(compute_fib)
        assert len(result) == 15


class TestGenerators:
    """Test generator memory efficiency - measures lazy evaluation."""

    def test_benchmark_list_comprehension(self, benchmark):
        """Benchmark list comprehension - eager evaluation."""

        def create_list():
            return [i * 2 for i in range(10000)]

        result = benchmark(create_list)
        assert len(result) == 10000

    def test_benchmark_generator_expression(self, benchmark):
        """Benchmark generator expression - lazy evaluation."""

        def use_generator():
            gen = (i * 2 for i in range(10000))
            return sum(gen)

        result = benchmark(use_generator)
        assert result > 0

    def test_benchmark_generator_function(self, benchmark):
        """Benchmark generator function - measures frame overhead."""

        def gen_func():
            for i in range(10000):
                yield i * 2

        def consume_generator():
            return sum(gen_func())

        result = benchmark(consume_generator)
        assert result > 0
