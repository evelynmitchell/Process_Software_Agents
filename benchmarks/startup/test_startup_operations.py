"""Benchmark process startup, import time, and module loading performance."""

import importlib
import subprocess
import sys
import time

import pytest


class TestImportTime:
    """Test module import performance - measures module loading overhead."""

    def test_benchmark_import_sys(self, benchmark):
        """Benchmark importing sys module - lightweight builtin."""

        def import_module():
            import sys as _sys  # pylint: disable=reimported

            return _sys

        result = benchmark(import_module)
        assert result is not None

    def test_benchmark_import_os(self, benchmark):
        """Benchmark importing os module - moderate complexity."""

        def import_module():
            import os as _os

            return _os

        result = benchmark(import_module)
        assert result is not None

    def test_benchmark_import_json(self, benchmark):
        """Benchmark importing json module - C extension."""

        def import_module():
            import json as _json

            return _json

        result = benchmark(import_module)
        assert result is not None

    def test_benchmark_import_re(self, benchmark):
        """Benchmark importing re module - regex engine."""

        def import_module():
            import re as _re

            return _re

        result = benchmark(import_module)
        assert result is not None

    def test_benchmark_import_pathlib(self, benchmark):
        """Benchmark importing pathlib - filesystem operations."""

        def import_module():
            import pathlib as _pathlib

            return _pathlib

        result = benchmark(import_module)
        assert result is not None

    def test_benchmark_import_datetime(self, benchmark):
        """Benchmark importing datetime module."""

        def import_module():
            import datetime as _datetime

            return _datetime

        result = benchmark(import_module)
        assert result is not None

    def test_benchmark_import_collections(self, benchmark):
        """Benchmark importing collections module."""

        def import_module():
            import collections as _collections

            return _collections

        result = benchmark(import_module)
        assert result is not None


class TestHeavyImports:
    """Test importing heavy modules - measures complex initialization."""

    def test_benchmark_import_unittest(self, benchmark):
        """Benchmark importing unittest framework."""

        def import_module():
            import unittest as _unittest

            return _unittest

        result = benchmark(import_module)
        assert result is not None

    def test_benchmark_import_asyncio(self, benchmark):
        """Benchmark importing asyncio - event loop initialization."""

        def import_module():
            import asyncio as _asyncio

            return _asyncio

        result = benchmark(import_module)
        assert result is not None

    def test_benchmark_import_multiprocessing(self, benchmark):
        """Benchmark importing multiprocessing."""

        def import_module():
            import multiprocessing as _mp

            return _mp

        result = benchmark(import_module)
        assert result is not None

    def test_benchmark_import_concurrent(self, benchmark):
        """Benchmark importing concurrent.futures."""

        def import_module():
            import concurrent.futures as _cf

            return _cf

        result = benchmark(import_module)
        assert result is not None


class TestThirdPartyImports:
    """Test importing third-party modules - measures package complexity."""

    def test_benchmark_import_numpy(self, benchmark):
        """Benchmark importing numpy - large numerical library."""
        try:

            def import_module():
                import numpy as _np

                return _np

            result = benchmark(import_module)
            assert result is not None
        except ImportError:
            pytest.skip("NumPy not available")

    def test_benchmark_import_pytest(self, benchmark):
        """Benchmark importing pytest framework."""

        def import_module():
            import pytest as _pytest  # pylint: disable=reimported

            return _pytest

        result = benchmark(import_module)
        assert result is not None


class TestDynamicImport:
    """Test dynamic import mechanisms - measures importlib overhead."""

    def test_benchmark_importlib_import(self, benchmark):
        """Benchmark importlib.import_module - dynamic import."""
        result = benchmark(importlib.import_module, "sys")
        assert result is not None

    def test_benchmark_importlib_reload(self, benchmark):
        """Benchmark module reload - measures re-initialization."""
        import json

        result = benchmark(importlib.reload, json)
        assert result is not None

    def test_benchmark_from_import(self, benchmark):
        """Benchmark from X import Y syntax."""

        def from_import():
            from os import path

            return path

        result = benchmark(from_import)
        assert result is not None


class TestSubprocessCreation:
    """Test subprocess creation - measures process startup overhead."""

    def test_benchmark_subprocess_run_simple(self, benchmark):
        """Benchmark simple subprocess execution."""
        result = benchmark(
            subprocess.run,
            [sys.executable, "-c", "print(42)"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_benchmark_subprocess_empty(self, benchmark):
        """Benchmark subprocess with minimal work - pure overhead."""
        result = benchmark(
            subprocess.run, [sys.executable, "-c", ""], capture_output=True
        )
        assert result.returncode == 0

    def test_benchmark_subprocess_with_import(self, benchmark):
        """Benchmark subprocess with module import - startup + import."""
        result = benchmark(
            subprocess.run,
            [sys.executable, "-c", "import sys; print(sys.version_info)"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_benchmark_subprocess_popen(self, benchmark):
        """Benchmark Popen creation - lower level API."""

        def create_process():
            with subprocess.Popen(
                [sys.executable, "-c", ""],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as proc:
                proc.wait()
                return proc.returncode

        result = benchmark(create_process)
        assert result == 0


class TestInterpreterStartup:
    """Test Python interpreter startup time."""

    def test_benchmark_interpreter_startup_time(self, benchmark):
        """Benchmark complete interpreter startup time."""

        def measure_startup():
            start = time.perf_counter()
            subprocess.run([sys.executable, "-c", ""], capture_output=True, check=False)
            return time.perf_counter() - start

        # Note: This measures subprocess overhead + interpreter startup
        result = benchmark(measure_startup)
        assert result > 0

    def test_benchmark_interpreter_with_site(self, benchmark):
        """Benchmark interpreter startup with site module."""
        result = benchmark(
            subprocess.run, [sys.executable, "-c", "import site"], capture_output=True
        )
        assert result.returncode == 0

    def test_benchmark_interpreter_no_site(self, benchmark):
        """Benchmark interpreter startup without site module (-S flag)."""
        result = benchmark(
            subprocess.run, [sys.executable, "-S", "-c", ""], capture_output=True
        )
        assert result.returncode == 0


class TestModuleCache:
    """Test module caching effectiveness - measures .pyc impact."""

    def test_benchmark_first_import(self, benchmark):
        """Benchmark first import (may compile .pyc)."""

        # Use a module that's unlikely to be imported yet
        def import_module():
            import pydoc

            return pydoc

        result = benchmark(import_module)
        assert result is not None

    def test_benchmark_reimport(self, benchmark):
        """Benchmark re-import from cache."""
        # Import once to ensure it's cached

        # Now benchmark importing again (should use cache)
        def import_module():
            import email as _email

            return _email

        result = benchmark(import_module)
        assert result is not None


class TestLazyImport:
    """Test lazy import patterns - measures deferred loading."""

    def test_benchmark_eager_import(self, benchmark):
        """Benchmark eager import - all at once."""

        def eager_imports():
            # pylint: disable=reimported,import-outside-toplevel
            import json
            import os
            import pathlib
            import re
            import sys

            return os, sys, re, json, pathlib

        result = benchmark(eager_imports)
        assert len(result) == 5

    def test_benchmark_lazy_import_wrapper(self, benchmark):
        """Benchmark lazy import using wrapper."""

        class LazyImport:
            def __init__(self, module_name):
                self.module_name = module_name
                self._module = None

            def __getattr__(self, name):
                if self._module is None:
                    self._module = importlib.import_module(self.module_name)
                return getattr(self._module, name)

        def use_lazy():
            lazy_json = LazyImport("json")
            # Force actual import
            return lazy_json.dumps({"test": "data"})

        result = benchmark(use_lazy)
        assert result is not None


class TestPackageDiscovery:
    """Test package discovery and metadata - measures packaging overhead."""

    def test_benchmark_sys_modules_lookup(self, benchmark):
        """Benchmark sys.modules lookup - module registry."""
        import sys  # pylint: disable=reimported

        result = benchmark(lambda: "sys" in sys.modules)
        assert result is True

    def test_benchmark_module_file_lookup(self, benchmark):
        """Benchmark __file__ attribute access."""
        import os

        result = benchmark(lambda: os.__file__)
        assert result is not None

    def test_benchmark_module_spec_lookup(self, benchmark):
        """Benchmark __spec__ attribute access - PEP 451."""
        import json

        result = benchmark(lambda: json.__spec__)
        assert result is not None


class TestEnvironmentSetup:
    """Test environment setup overhead - measures initialization cost."""

    def test_benchmark_simple_script_execution(self, benchmark):
        """Benchmark executing a simple script - end-to-end timing."""
        script = "x = 1 + 1"
        result = benchmark(
            subprocess.run, [sys.executable, "-c", script], capture_output=True
        )
        assert result.returncode == 0

    def test_benchmark_script_with_calculation(self, benchmark):
        """Benchmark script with calculation."""
        script = "sum(range(1000))"
        result = benchmark(
            subprocess.run, [sys.executable, "-c", script], capture_output=True
        )
        assert result.returncode == 0

    def test_benchmark_optimized_mode(self, benchmark):
        """Benchmark with -O optimization flag."""
        result = benchmark(
            subprocess.run, [sys.executable, "-O", "-c", ""], capture_output=True
        )
        assert result.returncode == 0

    def test_benchmark_isolated_mode(self, benchmark):
        """Benchmark with -I isolated mode."""
        result = benchmark(
            subprocess.run, [sys.executable, "-I", "-c", ""], capture_output=True
        )
        assert result.returncode == 0
