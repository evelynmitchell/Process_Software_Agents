"""Benchmark PyTorch tensor operations and neural network performance."""

import pytest

# PyTorch import with fallback
try:
    import torch
    import torch.nn.functional as F
    from torch import nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="PyTorch not available")


if TORCH_AVAILABLE:

    class TestTensorCreation:
        """Test tensor creation performance - measures allocation and device transfer."""

        def test_benchmark_tensor_zeros(self, benchmark):
            """Benchmark creating large zero tensors."""
            result = benchmark(torch.zeros, 1000, 1000)
            assert result.shape == (1000, 1000)

        def test_benchmark_tensor_ones(self, benchmark):
            """Benchmark creating large ones tensors."""
            result = benchmark(torch.ones, 1000, 1000)
            assert result.shape == (1000, 1000)

        def test_benchmark_tensor_rand(self, benchmark):
            """Benchmark random tensor generation."""
            result = benchmark(torch.rand, 1000, 1000)
            assert result.shape == (1000, 1000)

        def test_benchmark_tensor_randn(self, benchmark):
            """Benchmark normal distribution random tensors."""
            result = benchmark(torch.randn, 1000, 1000)
            assert result.shape == (1000, 1000)

        def test_benchmark_tensor_arange(self, benchmark):
            """Benchmark range tensor creation."""
            result = benchmark(torch.arange, 0, 1000000)
            assert len(result) == 1000000

        @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
        def test_benchmark_tensor_to_cuda(self, benchmark):
            """Benchmark CPU to GPU transfer - measures device transfer overhead."""
            cpu_tensor = torch.rand(1000, 1000)
            result = benchmark(lambda t: t.cuda(), cpu_tensor)
            assert result.is_cuda

        @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
        def test_benchmark_tensor_from_cuda(self, benchmark):
            """Benchmark GPU to CPU transfer."""
            cuda_tensor = torch.rand(1000, 1000).cuda()
            result = benchmark(lambda t: t.cpu(), cuda_tensor)
            assert not result.is_cuda

    class TestTensorArithmetic:
        """Test basic tensor arithmetic - measures vectorization and kernel performance."""

        @pytest.fixture
        def large_tensors(self):
            """Create large test tensors."""
            return torch.rand(1000, 1000), torch.rand(1000, 1000)

        def test_benchmark_tensor_addition(self, benchmark, large_tensors):
            """Benchmark element-wise addition."""
            a, b = large_tensors
            result = benchmark(torch.add, a, b)
            assert result.shape == a.shape

        def test_benchmark_tensor_multiplication(self, benchmark, large_tensors):
            """Benchmark element-wise multiplication."""
            a, b = large_tensors
            result = benchmark(torch.mul, a, b)
            assert result.shape == a.shape

        def test_benchmark_tensor_division(self, benchmark, large_tensors):
            """Benchmark element-wise division."""
            a, b = large_tensors
            result = benchmark(torch.div, a, b)
            assert result.shape == a.shape

        def test_benchmark_tensor_power(self, benchmark):
            """Benchmark power operations."""
            a = torch.rand(1000, 1000)
            result = benchmark(torch.pow, a, 2.5)
            assert result.shape == a.shape

        def test_benchmark_tensor_matmul(self, benchmark):
            """Benchmark matrix multiplication - key operation for deep learning."""
            a = torch.rand(500, 500)
            b = torch.rand(500, 500)
            result = benchmark(torch.matmul, a, b)
            assert result.shape == (500, 500)

    class TestNeuralNetworkOps:
        """Test neural network operations - measures optimized kernels."""

        def test_benchmark_relu(self, benchmark):
            """Benchmark ReLU activation - most common activation function."""
            x = torch.randn(1000, 1000)
            result = benchmark(F.relu, x)
            assert result.shape == x.shape

        def test_benchmark_softmax(self, benchmark):
            """Benchmark softmax - common output activation."""
            x = torch.randn(1000, 1000)
            result = benchmark(F.softmax, x, dim=1)
            assert result.shape == x.shape

        def test_benchmark_layer_norm(self, benchmark):
            """Benchmark layer normalization."""
            x = torch.randn(32, 100, 512)
            layer = nn.LayerNorm(512)
            result = benchmark(layer, x)
            assert result.shape == x.shape

        def test_benchmark_batch_norm(self, benchmark):
            """Benchmark batch normalization."""
            x = torch.randn(32, 100, 512)
            layer = nn.BatchNorm1d(100)
            result = benchmark(layer, x)
            assert result.shape == x.shape

        def test_benchmark_conv2d(self, benchmark):
            """Benchmark 2D convolution - core operation in CNNs."""
            x = torch.randn(32, 3, 224, 224)
            conv = nn.Conv2d(3, 64, kernel_size=3, padding=1)
            result = benchmark(conv, x)
            assert result.shape == (32, 64, 224, 224)

        def test_benchmark_linear(self, benchmark):
            """Benchmark linear layer - core operation in transformers."""
            x = torch.randn(32, 512)
            linear = nn.Linear(512, 512)
            result = benchmark(linear, x)
            assert result.shape == (32, 512)

    class TestGradients:
        """Test gradient computation - measures autograd performance."""

        def test_benchmark_simple_backward(self, benchmark):
            """Benchmark simple backward pass."""

            def backward_pass():
                x = torch.randn(1000, 1000, requires_grad=True)
                y = x**2
                loss = y.sum()
                loss.backward()
                return x.grad

            result = benchmark(backward_pass)
            assert result is not None

        def test_benchmark_matmul_backward(self, benchmark):
            """Benchmark matrix multiplication backward pass."""

            def backward_pass():
                x = torch.randn(500, 500, requires_grad=True)
                w = torch.randn(500, 500, requires_grad=True)
                y = torch.matmul(x, w)
                loss = y.sum()
                loss.backward()
                return x.grad, w.grad

            x_grad, w_grad = benchmark(backward_pass)
            assert x_grad is not None and w_grad is not None

        def test_benchmark_mlp_backward(self, benchmark):
            """Benchmark multi-layer perceptron backward pass."""

            class SimpleMLP(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.fc1 = nn.Linear(512, 512)
                    self.fc2 = nn.Linear(512, 512)
                    self.fc3 = nn.Linear(512, 10)

                def forward(self, x):
                    x = F.relu(self.fc1(x))
                    x = F.relu(self.fc2(x))
                    return self.fc3(x)

            def train_step():
                model = SimpleMLP()
                x = torch.randn(32, 512)
                y = torch.randint(0, 10, (32,))

                output = model(x)
                loss = F.cross_entropy(output, y)
                loss.backward()
                return loss.item()

            result = benchmark(train_step)
            assert result > 0

    class TestMemoryOperations:
        """Test memory-related operations - measures allocation patterns."""

        def test_benchmark_tensor_clone(self, benchmark):
            """Benchmark tensor cloning - deep copy operation."""
            x = torch.rand(1000, 1000)
            result = benchmark(torch.clone, x)
            assert result.shape == x.shape

        def test_benchmark_tensor_reshape(self, benchmark):
            """Benchmark tensor reshape - view vs copy."""
            x = torch.rand(1000, 1000)
            result = benchmark(lambda t: t.reshape(100, 10000), x)
            assert result.shape == (100, 10000)

        def test_benchmark_tensor_transpose(self, benchmark):
            """Benchmark tensor transpose."""
            x = torch.rand(1000, 1000)
            result = benchmark(torch.transpose, x, 0, 1)
            assert result.shape == (1000, 1000)

        def test_benchmark_tensor_contiguous(self, benchmark):
            """Benchmark making tensor contiguous - memory layout change."""
            x = torch.rand(1000, 1000).t()
            result = benchmark(lambda t: t.contiguous(), x)
            assert result.is_contiguous()

        def test_benchmark_tensor_concatenate(self, benchmark):
            """Benchmark tensor concatenation - memory allocation."""
            tensors = [torch.rand(100, 1000) for _ in range(10)]
            result = benchmark(torch.cat, tensors, dim=0)
            assert result.shape == (1000, 1000)

    class TestComplexModels:
        """Test complex model operations - end-to-end performance."""

        def test_benchmark_transformer_layer(self, benchmark):
            """Benchmark transformer layer forward pass."""
            layer = nn.TransformerEncoderLayer(d_model=512, nhead=8, batch_first=True)
            x = torch.randn(32, 100, 512)
            result = benchmark(layer, x)
            assert result.shape == (32, 100, 512)

        def test_benchmark_attention(self, benchmark):
            """Benchmark multi-head attention."""
            attention = nn.MultiheadAttention(512, 8, batch_first=True)
            x = torch.randn(32, 100, 512)
            result = benchmark(lambda q: attention(q, q, q)[0], x)
            assert result.shape == (32, 100, 512)

        def test_benchmark_resnet_block(self, benchmark):
            """Benchmark ResNet-style block."""

            class ResNetBlock(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.conv1 = nn.Conv2d(64, 64, 3, padding=1)
                    self.bn1 = nn.BatchNorm2d(64)
                    self.conv2 = nn.Conv2d(64, 64, 3, padding=1)
                    self.bn2 = nn.BatchNorm2d(64)

                def forward(self, x):
                    identity = x
                    out = F.relu(self.bn1(self.conv1(x)))
                    out = self.bn2(self.conv2(out))
                    out += identity
                    return F.relu(out)

            block = ResNetBlock()
            x = torch.randn(32, 64, 56, 56)
            result = benchmark(block, x)
            assert result.shape == (32, 64, 56, 56)

    class TestDataTypes:
        """Test different data types - measures precision vs performance tradeoffs."""

        def test_benchmark_float32_matmul(self, benchmark):
            """Benchmark float32 matrix multiplication - default precision."""
            a = torch.rand(500, 500, dtype=torch.float32)
            b = torch.rand(500, 500, dtype=torch.float32)
            result = benchmark(torch.matmul, a, b)
            assert result.dtype == torch.float32

        def test_benchmark_float16_matmul(self, benchmark):
            """Benchmark float16 matrix multiplication - half precision."""
            a = torch.rand(500, 500, dtype=torch.float16)
            b = torch.rand(500, 500, dtype=torch.float16)
            result = benchmark(torch.matmul, a, b)
            assert result.dtype == torch.float16

        def test_benchmark_int64_operations(self, benchmark):
            """Benchmark integer operations."""
            a = torch.randint(0, 100, (1000, 1000), dtype=torch.int64)
            b = torch.randint(0, 100, (1000, 1000), dtype=torch.int64)
            result = benchmark(torch.add, a, b)
            assert result.dtype == torch.int64
