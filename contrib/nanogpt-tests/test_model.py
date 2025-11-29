"""Tests for nanoGPT model.py

This test suite provides coverage for the core GPT model components:
- GPTConfig dataclass
- LayerNorm (custom implementation)
- CausalSelfAttention
- MLP (feed-forward network)
- Block (transformer block)
- GPT (full model)

Run with: pytest tests/test_model.py -v
Coverage: pytest tests/test_model.py --cov=model --cov-report=term-missing
"""

import pytest
import torch

from model import GPTConfig, LayerNorm, CausalSelfAttention, MLP, Block, GPT


class TestGPTConfig:
    """Tests for GPTConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = GPTConfig()
        assert config.block_size == 1024
        assert config.vocab_size == 50304
        assert config.n_layer == 12
        assert config.n_head == 12
        assert config.n_embd == 768
        assert config.dropout == 0.0
        assert config.bias is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = GPTConfig(
            block_size=256,
            vocab_size=1000,
            n_layer=4,
            n_head=4,
            n_embd=128,
            dropout=0.1,
            bias=False
        )
        assert config.block_size == 256
        assert config.vocab_size == 1000
        assert config.n_layer == 4
        assert config.n_head == 4
        assert config.n_embd == 128
        assert config.dropout == 0.1
        assert config.bias is False

    def test_small_config_for_testing(self):
        """Test minimal config for fast testing."""
        config = GPTConfig(
            block_size=32,
            vocab_size=100,
            n_layer=2,
            n_head=2,
            n_embd=64,
            dropout=0.0,
            bias=True
        )
        assert config.n_embd % config.n_head == 0  # Must be divisible


class TestLayerNorm:
    """Tests for custom LayerNorm implementation."""

    def test_layer_norm_with_bias(self):
        """Test LayerNorm with bias enabled."""
        ln = LayerNorm(ndim=64, bias=True)
        assert ln.weight.shape == (64,)
        assert ln.bias is not None
        assert ln.bias.shape == (64,)

    def test_layer_norm_without_bias(self):
        """Test LayerNorm without bias."""
        ln = LayerNorm(ndim=64, bias=False)
        assert ln.weight.shape == (64,)
        assert ln.bias is None

    def test_layer_norm_forward(self):
        """Test LayerNorm forward pass."""
        ln = LayerNorm(ndim=64, bias=True)
        x = torch.randn(2, 10, 64)  # batch=2, seq=10, dim=64
        y = ln(x)
        assert y.shape == x.shape

    def test_layer_norm_normalization(self):
        """Test that output is approximately normalized."""
        ln = LayerNorm(ndim=64, bias=False)
        # Reset weights to default for predictable behavior
        ln.weight.data.fill_(1.0)
        x = torch.randn(2, 10, 64)
        y = ln(x)
        # Check that mean is close to 0 and std close to 1
        assert y.mean(dim=-1).abs().max() < 0.1
        assert (y.std(dim=-1) - 1.0).abs().max() < 0.1


class TestCausalSelfAttention:
    """Tests for CausalSelfAttention module."""

    def test_attention_init(self, small_config):
        """Test attention initialization."""
        attn = CausalSelfAttention(small_config)
        assert attn.n_head == 4
        assert attn.n_embd == 64
        assert attn.dropout == 0.0

    def test_attention_forward(self, small_config):
        """Test attention forward pass."""
        attn = CausalSelfAttention(small_config)
        x = torch.randn(2, 16, 64)  # batch=2, seq=16, dim=64
        y = attn(x)
        assert y.shape == x.shape

    def test_attention_different_seq_lengths(self, small_config):
        """Test attention with various sequence lengths."""
        attn = CausalSelfAttention(small_config)
        for seq_len in [1, 8, 16, 32]:
            x = torch.randn(2, seq_len, 64)
            y = attn(x)
            assert y.shape == x.shape


class TestMLP:
    """Tests for MLP (feed-forward) module."""

    def test_mlp_init(self, small_config):
        """Test MLP initialization."""
        mlp = MLP(small_config)
        # First layer expands 4x
        assert mlp.c_fc.in_features == 64
        assert mlp.c_fc.out_features == 256
        # Second layer projects back
        assert mlp.c_proj.in_features == 256
        assert mlp.c_proj.out_features == 64

    def test_mlp_forward(self, small_config):
        """Test MLP forward pass."""
        mlp = MLP(small_config)
        x = torch.randn(2, 16, 64)
        y = mlp(x)
        assert y.shape == x.shape


class TestBlock:
    """Tests for transformer Block."""

    def test_block_init(self, small_config):
        """Test Block initialization."""
        block = Block(small_config)
        assert isinstance(block.ln_1, LayerNorm)
        assert isinstance(block.attn, CausalSelfAttention)
        assert isinstance(block.ln_2, LayerNorm)
        assert isinstance(block.mlp, MLP)

    def test_block_forward(self, small_config):
        """Test Block forward pass."""
        block = Block(small_config)
        x = torch.randn(2, 16, 64)
        y = block(x)
        assert y.shape == x.shape

    def test_block_residual_connections(self, small_config):
        """Test that block uses residual connections."""
        block = Block(small_config)
        x = torch.randn(2, 16, 64)
        y = block(x)
        # Output should not be identical to input (transformations applied)
        assert not torch.allclose(x, y)


class TestGPT:
    """Tests for full GPT model."""

    def test_gpt_init(self, small_config, capsys):
        """Test GPT initialization."""
        model = GPT(small_config)
        assert model.config == small_config
        assert len(model.transformer.h) == 2  # n_layer
        # Check parameter count is printed
        captured = capsys.readouterr()
        assert "number of parameters" in captured.out

    def test_gpt_forward_no_targets(self, small_config):
        """Test GPT forward pass without targets (inference)."""
        model = GPT(small_config)
        model.eval()
        idx = torch.randint(0, 100, (2, 16))  # batch=2, seq=16
        logits, loss = model(idx)
        assert logits.shape == (2, 1, 100)  # Only last position
        assert loss is None

    def test_gpt_forward_with_targets(self, small_config):
        """Test GPT forward pass with targets (training)."""
        model = GPT(small_config)
        idx = torch.randint(0, 100, (2, 16))
        targets = torch.randint(0, 100, (2, 16))
        logits, loss = model(idx, targets)
        assert logits.shape == (2, 16, 100)  # All positions
        assert loss is not None
        assert loss.item() > 0

    def test_gpt_get_num_params(self, small_config):
        """Test parameter counting."""
        model = GPT(small_config)
        n_params = model.get_num_params()
        n_params_with_emb = model.get_num_params(non_embedding=False)
        assert n_params > 0
        assert n_params_with_emb > n_params  # Includes position embeddings

    def test_gpt_crop_block_size(self, small_config):
        """Test cropping block size."""
        model = GPT(small_config)
        model.crop_block_size(16)
        assert model.config.block_size == 16
        assert model.transformer.wpe.weight.shape[0] == 16

    def test_gpt_generate(self, small_config):
        """Test text generation."""
        model = GPT(small_config)
        model.eval()
        idx = torch.randint(0, 100, (1, 5))  # Start with 5 tokens
        generated = model.generate(idx, max_new_tokens=10)
        assert generated.shape == (1, 15)  # 5 + 10 new tokens

    def test_gpt_generate_with_temperature(self, small_config):
        """Test generation with temperature scaling."""
        model = GPT(small_config)
        model.eval()
        idx = torch.randint(0, 100, (1, 5))
        # Low temperature should give more deterministic outputs
        generated = model.generate(idx, max_new_tokens=5, temperature=0.1)
        assert generated.shape == (1, 10)

    def test_gpt_generate_with_top_k(self, small_config):
        """Test generation with top-k sampling."""
        model = GPT(small_config)
        model.eval()
        idx = torch.randint(0, 100, (1, 5))
        generated = model.generate(idx, max_new_tokens=5, top_k=10)
        assert generated.shape == (1, 10)

    def test_gpt_configure_optimizers(self, small_config):
        """Test optimizer configuration."""
        model = GPT(small_config)
        optimizer = model.configure_optimizers(
            weight_decay=0.1,
            learning_rate=1e-4,
            betas=(0.9, 0.95),
            device_type='cpu'
        )
        assert isinstance(optimizer, torch.optim.AdamW)
        assert len(optimizer.param_groups) == 2  # decay and no-decay groups

    def test_gpt_estimate_mfu(self, small_config):
        """Test MFU estimation."""
        model = GPT(small_config)
        mfu = model.estimate_mfu(fwdbwd_per_iter=1, dt=1.0)
        assert mfu > 0
        assert mfu < 1  # Should be less than 100% utilization

    def test_gpt_sequence_too_long(self, small_config):
        """Test that too-long sequences raise assertion."""
        model = GPT(small_config)
        idx = torch.randint(0, 100, (1, 64))  # Longer than block_size=32
        with pytest.raises(AssertionError):
            model(idx)


class TestGPTIntegration:
    """Integration tests for GPT training loop."""

    def test_training_step(self, tiny_config):
        """Test a single training step."""
        model = GPT(tiny_config)
        optimizer = model.configure_optimizers(
            weight_decay=0.1,
            learning_rate=1e-3,
            betas=(0.9, 0.95),
            device_type='cpu'
        )

        # Training data
        idx = torch.randint(0, 50, (4, 16))
        targets = torch.randint(0, 50, (4, 16))

        # Forward pass
        logits, loss = model(idx, targets)

        # Backward pass
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        assert loss.item() > 0

    def test_overfitting_small_batch(self, tiny_config):
        """Test that model can overfit a small batch."""
        model = GPT(tiny_config)
        optimizer = model.configure_optimizers(
            weight_decay=0.0,
            learning_rate=1e-2,
            betas=(0.9, 0.95),
            device_type='cpu'
        )

        # Fixed small batch to overfit
        torch.manual_seed(42)
        idx = torch.randint(0, 50, (2, 8))
        targets = torch.randint(0, 50, (2, 8))

        initial_loss = None
        for _ in range(50):
            logits, loss = model(idx, targets)
            if initial_loss is None:
                initial_loss = loss.item()
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

        final_loss = loss.item()
        # Loss should decrease significantly
        assert final_loss < initial_loss * 0.5
