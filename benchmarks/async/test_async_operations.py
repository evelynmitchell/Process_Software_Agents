"""Benchmark asyncio operations to test event loop and concurrency performance."""

import asyncio

import pytest


class TestEventLoopOverhead:
    """Test event loop overhead - measures scheduling and context switching."""

    def test_benchmark_coroutine_creation(self, benchmark):
        """Benchmark creating coroutines - measures object creation overhead."""

        async def simple_coroutine():
            return 42

        def create_coro():
            coro = simple_coroutine()
            coro.close()  # Clean up

        benchmark(create_coro)

    def test_benchmark_task_creation(self, benchmark):
        """Benchmark creating tasks - measures task scheduling overhead."""

        async def run_task():
            async def simple_task():
                return 42

            task = asyncio.create_task(simple_task())
            return await task

        def run():
            return asyncio.run(run_task())

        result = benchmark(run)
        assert result == 42

    def test_benchmark_empty_coroutine(self, benchmark):
        """Benchmark empty coroutine execution - measures pure overhead."""

        async def empty():
            pass

        def run_empty():
            asyncio.run(empty())

        benchmark(run_empty)

    def test_benchmark_await_overhead(self, benchmark):
        """Benchmark await overhead - measures suspend/resume cost."""

        async def await_chain():
            async def inner():
                return 42

            return await inner()

        def run_await():
            return asyncio.run(await_chain())

        result = benchmark(run_await)
        assert result == 42


class TestConcurrentTasks:
    """Test concurrent task execution - measures parallelization efficiency."""

    def test_benchmark_gather_10_tasks(self, benchmark):
        """Benchmark gathering 10 concurrent tasks."""

        async def run_concurrent():
            async def task(n):
                await asyncio.sleep(0)
                return n * 2

            results = await asyncio.gather(*[task(i) for i in range(10)])
            return results

        def run_wrapper():
            return asyncio.run(run_concurrent())

        results = benchmark(run_wrapper)
        assert len(results) == 10

    def test_benchmark_gather_100_tasks(self, benchmark):
        """Benchmark gathering 100 concurrent tasks - tests scalability."""

        async def run_concurrent():
            async def task(n):
                await asyncio.sleep(0)
                return n * 2

            results = await asyncio.gather(*[task(i) for i in range(100)])
            return results

        def run_wrapper():
            return asyncio.run(run_concurrent())

        results = benchmark(run_wrapper)
        assert len(results) == 100

    def test_benchmark_gather_1000_tasks(self, benchmark):
        """Benchmark gathering 1000 concurrent tasks - stress test."""

        async def run_concurrent():
            async def task(n):
                await asyncio.sleep(0)
                return n * 2

            results = await asyncio.gather(*[task(i) for i in range(1000)])
            return results

        def run_wrapper():
            return asyncio.run(run_concurrent())

        results = benchmark(run_wrapper)
        assert len(results) == 1000

    def test_benchmark_task_group(self, benchmark):
        """Benchmark TaskGroup (Python 3.11+) - tests structured concurrency."""

        async def run_task_group():
            async def task(n):
                await asyncio.sleep(0)
                return n * 2

            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(task(i)) for i in range(100)]

            return [t.result() for t in tasks]

        try:

            def run_wrapper():
                return asyncio.run(run_task_group())

            results = benchmark(run_wrapper)
            assert len(results) == 100
        except AttributeError:
            pytest.skip("TaskGroup not available (Python < 3.11)")


class TestAsyncIteration:
    """Test async iteration - measures generator and iterator performance."""

    def test_benchmark_async_generator(self, benchmark):
        """Benchmark async generator creation and iteration."""

        async def async_gen():
            for i in range(1000):
                yield i

        async def consume():
            result = []
            async for item in async_gen():
                result.append(item)
            return result

        def run_wrapper():
            return asyncio.run(consume())

        results = benchmark(run_wrapper)
        assert len(results) == 1000

    def test_benchmark_async_comprehension(self, benchmark):
        """Benchmark async comprehension - tests optimized iteration."""

        async def async_gen():
            for i in range(1000):
                yield i

        async def comprehend():
            return [item async for item in async_gen()]

        def run_wrapper():
            return asyncio.run(comprehend())

        results = benchmark(run_wrapper)
        assert len(results) == 1000


class TestSynchronization:
    """Test async synchronization primitives - measures lock overhead."""

    def test_benchmark_lock_acquire_release(self, benchmark):
        """Benchmark lock acquire/release - measures mutex overhead."""

        async def lock_operations():
            lock = asyncio.Lock()
            for _ in range(100):
                async with lock:
                    pass

        def run_wrapper():
            return asyncio.run(lock_operations())

        benchmark(run_wrapper)

    def test_benchmark_semaphore(self, benchmark):
        """Benchmark semaphore operations."""

        async def semaphore_operations():
            sem = asyncio.Semaphore(10)
            for _ in range(100):
                async with sem:
                    pass

        def run_wrapper():
            return asyncio.run(semaphore_operations())

        benchmark(run_wrapper)

    def test_benchmark_event_wait_set(self, benchmark):
        """Benchmark event wait/set operations."""

        async def event_operations():
            event = asyncio.Event()

            async def waiter():
                await event.wait()

            async def setter():
                event.set()

            waiter_task = asyncio.create_task(waiter())
            await setter()
            await waiter_task

        def run_wrapper():
            return asyncio.run(event_operations())

        benchmark(run_wrapper)

    def test_benchmark_queue_operations(self, benchmark):
        """Benchmark queue put/get operations - tests FIFO overhead."""

        async def queue_operations():
            queue = asyncio.Queue()

            for i in range(100):
                await queue.put(i)

            results = []
            for _ in range(100):
                results.append(await queue.get())

            return results

        def run_wrapper():
            return asyncio.run(queue_operations())

        results = benchmark(run_wrapper)
        assert len(results) == 100


class TestCPUBoundAsync:
    """Test CPU-bound operations in async - measures thread pool efficiency."""

    def test_benchmark_run_in_executor(self, benchmark):
        """Benchmark running CPU-bound work in executor."""

        def cpu_bound_work():
            """Simulate CPU-bound work."""
            total = 0
            for i in range(10000):
                total += i**2
            return total

        async def run_in_executor():
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, cpu_bound_work)
            return result

        def run_wrapper():
            return asyncio.run(run_in_executor())

        result = benchmark(run_wrapper)
        assert result > 0

    def test_benchmark_multiple_executors(self, benchmark):
        """Benchmark multiple CPU-bound tasks in executor."""

        def cpu_bound_work(n):
            total = 0
            for i in range(10000):
                total += i**2
            return total + n

        async def run_concurrent_cpu():
            loop = asyncio.get_running_loop()
            tasks = [loop.run_in_executor(None, cpu_bound_work, i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            return results

        def run_wrapper():
            return asyncio.run(run_concurrent_cpu())

        results = benchmark(run_wrapper)
        assert len(results) == 10


class TestIOSimulation:
    """Test I/O simulation - measures sleep and timer performance."""

    def test_benchmark_single_sleep(self, benchmark):
        """Benchmark single sleep operation - measures timer overhead."""

        async def single_sleep():
            await asyncio.sleep(0.001)  # 1ms

        def run_wrapper():
            return asyncio.run(single_sleep())

        benchmark(run_wrapper)

    def test_benchmark_many_sleeps(self, benchmark):
        """Benchmark many sequential sleeps."""

        async def many_sleeps():
            for _ in range(100):
                await asyncio.sleep(0)

        def run_wrapper():
            return asyncio.run(many_sleeps())

        benchmark(run_wrapper)

    def test_benchmark_concurrent_sleeps(self, benchmark):
        """Benchmark concurrent sleeps - measures timer scheduling."""

        async def concurrent_sleeps():
            await asyncio.gather(*[asyncio.sleep(0.001) for _ in range(100)])

        def run_wrapper():
            return asyncio.run(concurrent_sleeps())

        benchmark(run_wrapper)


class TestComplexWorkloads:
    """Test complex async workloads - end-to-end scenarios."""

    def test_benchmark_producer_consumer(self, benchmark):
        """Benchmark producer-consumer pattern."""

        async def producer_consumer():
            queue = asyncio.Queue(maxsize=10)

            async def producer():
                for i in range(100):
                    await queue.put(i)
                await queue.put(None)  # Sentinel

            async def consumer():
                results = []
                while True:
                    item = await queue.get()
                    if item is None:
                        break
                    results.append(item * 2)
                return results

            prod_task = asyncio.create_task(producer())
            cons_task = asyncio.create_task(consumer())

            results = await cons_task
            await prod_task
            return results

        def run_wrapper():
            return asyncio.run(producer_consumer())

        results = benchmark(run_wrapper)
        assert len(results) == 100

    def test_benchmark_pipeline(self, benchmark):
        """Benchmark async pipeline pattern."""

        async def pipeline():
            async def stage1(n):
                await asyncio.sleep(0)
                return n * 2

            async def stage2(n):
                await asyncio.sleep(0)
                return n + 10

            async def stage3(n):
                await asyncio.sleep(0)
                return n**2

            async def process(n):
                result = await stage1(n)
                result = await stage2(result)
                result = await stage3(result)
                return result

            results = await asyncio.gather(*[process(i) for i in range(100)])
            return results

        def run_wrapper():
            return asyncio.run(pipeline())

        results = benchmark(run_wrapper)
        assert len(results) == 100

    def test_benchmark_fan_out_fan_in(self, benchmark):
        """Benchmark fan-out/fan-in pattern - common in distributed systems."""

        async def fan_out_fan_in():
            async def worker(n):
                await asyncio.sleep(0)
                return n * 2

            # Fan out
            tasks = [asyncio.create_task(worker(i)) for i in range(100)]

            # Fan in
            results = await asyncio.gather(*tasks)

            # Aggregate
            return sum(results)

        def run_wrapper():
            return asyncio.run(fan_out_fan_in())

        result = benchmark(run_wrapper)
        assert result > 0


class TestAsyncContextManagers:
    """Test async context managers - measures enter/exit overhead."""

    def test_benchmark_async_context_manager(self, benchmark):
        """Benchmark async context manager operations."""

        class AsyncResource:
            async def __aenter__(self):
                await asyncio.sleep(0)
                return self

            async def __aexit__(self, *args):
                await asyncio.sleep(0)

        async def use_context():
            for _ in range(100):
                async with AsyncResource():
                    pass

        def run_wrapper():
            return asyncio.run(use_context())

        benchmark(run_wrapper)
