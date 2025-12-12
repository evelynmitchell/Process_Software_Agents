"""Benchmark NumPy array operations to test memory management and computation speed."""

import numpy as np
import pytest


class TestArrayCreation:
    """Test array creation performance - measures allocation and initialization."""

    def test_benchmark_array_zeros(self, benchmark):
        """Benchmark creating large zero arrays - tests memory allocation."""
        result = benchmark(np.zeros, (1000, 1000))
        assert result.shape == (1000, 1000)

    def test_benchmark_array_ones(self, benchmark):
        """Benchmark creating large ones arrays."""
        result = benchmark(np.ones, (1000, 1000))
        assert result.shape == (1000, 1000)

    def test_benchmark_array_random(self, benchmark):
        """Benchmark random array generation - tests RNG and allocation."""
        result = benchmark(np.random.rand, 1000, 1000)
        assert result.shape == (1000, 1000)

    def test_benchmark_array_arange(self, benchmark):
        """Benchmark arange creation - tests sequential allocation."""
        result = benchmark(np.arange, 0, 1000000)
        assert len(result) == 1000000

    def test_benchmark_array_linspace(self, benchmark):
        """Benchmark linspace creation - tests division and allocation."""
        result = benchmark(np.linspace, 0, 1000, 100000)
        assert len(result) == 100000


class TestArrayArithmetic:
    """Test basic arithmetic operations - measures vectorization performance."""

    @pytest.fixture
    def large_arrays(self):
        """Create large test arrays."""
        return np.random.rand(1000, 1000), np.random.rand(1000, 1000)

    def test_benchmark_array_addition(self, benchmark, large_arrays):
        """Benchmark element-wise addition - tests vectorization."""
        a, b = large_arrays
        result = benchmark(np.add, a, b)
        assert result.shape == a.shape

    def test_benchmark_array_multiplication(self, benchmark, large_arrays):
        """Benchmark element-wise multiplication."""
        a, b = large_arrays
        result = benchmark(np.multiply, a, b)
        assert result.shape == a.shape

    def test_benchmark_array_division(self, benchmark, large_arrays):
        """Benchmark element-wise division."""
        a, b = large_arrays
        result = benchmark(np.divide, a, b)
        assert result.shape == a.shape

    def test_benchmark_array_power(self, benchmark):
        """Benchmark power operations - tests transcendental functions."""
        a = np.random.rand(1000, 1000)
        result = benchmark(np.power, a, 2.5)
        assert result.shape == a.shape


class TestLinearAlgebra:
    """Test linear algebra operations - measures optimized BLAS/LAPACK performance."""

    @pytest.fixture
    def matrices(self):
        """Create test matrices."""
        return np.random.rand(500, 500), np.random.rand(500, 500)

    def test_benchmark_matrix_multiply(self, benchmark, matrices):
        """Benchmark matrix multiplication - key operation for ML workloads."""
        a, b = matrices
        result = benchmark(np.dot, a, b)
        assert result.shape == (500, 500)

    def test_benchmark_matrix_transpose(self, benchmark):
        """Benchmark transpose - tests memory layout operations."""
        a = np.random.rand(1000, 1000)
        result = benchmark(np.transpose, a)
        assert result.shape == (1000, 1000)

    def test_benchmark_matrix_inverse(self, benchmark):
        """Benchmark matrix inversion - computationally intensive."""
        a = np.random.rand(500, 500)
        result = benchmark(np.linalg.inv, a)
        assert result.shape == (500, 500)

    def test_benchmark_eigenvalues(self, benchmark):
        """Benchmark eigenvalue computation - complex operation."""
        a = np.random.rand(300, 300)
        result = benchmark(np.linalg.eigvals, a)
        assert len(result) == 300

    def test_benchmark_svd(self, benchmark):
        """Benchmark Singular Value Decomposition - memory and computation intensive."""
        a = np.random.rand(300, 300)
        u, s, vh = benchmark(np.linalg.svd, a)
        assert u.shape == (300, 300)


class TestReductions:
    """Test reduction operations - measures aggregation performance."""

    @pytest.fixture
    def large_array(self):
        """Create large test array."""
        return np.random.rand(10000, 1000)

    def test_benchmark_sum(self, benchmark, large_array):
        """Benchmark sum reduction."""
        result = benchmark(np.sum, large_array)
        assert isinstance(result, float | np.floating)

    def test_benchmark_mean(self, benchmark, large_array):
        """Benchmark mean calculation."""
        result = benchmark(np.mean, large_array)
        assert isinstance(result, float | np.floating)

    def test_benchmark_std(self, benchmark, large_array):
        """Benchmark standard deviation - tests variance calculation."""
        result = benchmark(np.std, large_array)
        assert isinstance(result, float | np.floating)

    def test_benchmark_max(self, benchmark, large_array):
        """Benchmark max reduction."""
        result = benchmark(np.max, large_array)
        assert isinstance(result, float | np.floating)

    def test_benchmark_argmax(self, benchmark, large_array):
        """Benchmark argmax - tests indexing."""
        result = benchmark(np.argmax, large_array)
        assert isinstance(result, int | np.integer)


class TestIndexingSlicing:
    """Test array indexing and slicing - measures memory access patterns."""

    @pytest.fixture
    def array_3d(self):
        """Create 3D test array."""
        return np.random.rand(100, 100, 100)

    def test_benchmark_basic_indexing(self, benchmark, array_3d):
        """Benchmark basic indexing - tests direct memory access."""
        result = benchmark(lambda a: a[50, 50, 50], array_3d)
        assert isinstance(result, float | np.floating)

    def test_benchmark_slicing(self, benchmark, array_3d):
        """Benchmark array slicing - tests view creation."""
        result = benchmark(lambda a: a[10:90, 10:90, :], array_3d)
        assert result.shape == (80, 80, 100)

    def test_benchmark_boolean_indexing(self, benchmark):
        """Benchmark boolean indexing - tests conditional access."""
        a = np.random.rand(1000, 1000)
        result = benchmark(lambda arr: arr[arr > 0.5], a)
        assert len(result) > 0

    def test_benchmark_fancy_indexing(self, benchmark):
        """Benchmark fancy indexing - tests indirect access."""
        a = np.random.rand(1000, 1000)
        indices = np.random.randint(0, 1000, size=10000)
        result = benchmark(lambda arr, idx: arr[idx, idx % 1000], a, indices)
        assert len(result) == 10000


class TestBroadcasting:
    """Test broadcasting operations - measures implicit shape expansion."""

    def test_benchmark_broadcast_addition(self, benchmark):
        """Benchmark broadcasting in addition - tests shape compatibility."""
        a = np.random.rand(1000, 1000)
        b = np.random.rand(1000, 1)
        result = benchmark(np.add, a, b)
        assert result.shape == (1000, 1000)

    def test_benchmark_broadcast_outer_product(self, benchmark):
        """Benchmark outer product via broadcasting."""
        a = np.random.rand(5000)
        b = np.random.rand(5000)
        result = benchmark(np.outer, a, b)
        assert result.shape == (5000, 5000)


class TestMemoryLayout:
    """Test different memory layouts - C-contiguous vs Fortran-contiguous."""

    def test_benchmark_c_contiguous_sum(self, benchmark):
        """Benchmark sum on C-contiguous array - row-major order."""
        a = np.random.rand(1000, 1000)
        assert a.flags["C_CONTIGUOUS"]
        result = benchmark(np.sum, a, axis=1)
        assert len(result) == 1000

    def test_benchmark_f_contiguous_sum(self, benchmark):
        """Benchmark sum on Fortran-contiguous array - column-major order."""
        a = np.asfortranarray(np.random.rand(1000, 1000))
        assert a.flags["F_CONTIGUOUS"]
        result = benchmark(np.sum, a, axis=0)
        assert len(result) == 1000

    def test_benchmark_copy_c_to_f(self, benchmark):
        """Benchmark converting C-contiguous to Fortran-contiguous."""
        a = np.random.rand(1000, 1000)
        result = benchmark(np.asfortranarray, a)
        assert result.flags["F_CONTIGUOUS"]
