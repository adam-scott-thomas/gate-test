"""Performance benchmarks for Gatekeeper.

Establishes baseline performance numbers for gate-core filter operations.
Essential data for anyone evaluating Gate for production use.

Run: python -m gate_test bench
Or:  pytest gate_test/benchmarks.py -v (tests assert performance thresholds)
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from gatekeeper import Gate, Tool, build_envelope, verify_envelope


EXECUTION_CLASSES = ["read_only", "advisory", "external_action", "state_mutation", "high_impact"]


def _build_gate(n_tools: int) -> Gate:
    """Build a gate with n_tools, cycling through execution classes."""
    gate = Gate()
    for i in range(n_tools):
        cls = EXECUTION_CLASSES[i % len(EXECUTION_CLASSES)]
        gate.add_tool(Tool(f"tool_{i}", execution_class=cls, description=f"Test tool {i}"))
    return gate


@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    total_seconds: float
    ops_per_second: float
    avg_microseconds: float

    def __str__(self) -> str:
        return (f"{self.name}: {self.ops_per_second:,.0f} ops/s "
                f"({self.avg_microseconds:.1f} us/op, {self.iterations} iterations)")


def _bench(name: str, fn, iterations: int = 1000) -> BenchmarkResult:
    """Run a benchmark and return the result."""
    # Warmup
    for _ in range(min(10, iterations)):
        fn()

    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    elapsed = time.perf_counter() - start

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_seconds=elapsed,
        ops_per_second=iterations / elapsed if elapsed > 0 else float("inf"),
        avg_microseconds=(elapsed / iterations) * 1_000_000,
    )


# --- Benchmarks ---


def bench_filter_10_tools() -> BenchmarkResult:
    gate = _build_gate(10)
    return _bench("filter(10 tools)", lambda: gate.filter(0.5), iterations=10_000)


def bench_filter_100_tools() -> BenchmarkResult:
    gate = _build_gate(100)
    return _bench("filter(100 tools)", lambda: gate.filter(0.5), iterations=5_000)


def bench_filter_1000_tools() -> BenchmarkResult:
    gate = _build_gate(1000)
    return _bench("filter(1000 tools)", lambda: gate.filter(0.5), iterations=1_000)


def bench_filter_mode_sweep() -> BenchmarkResult:
    """Filter at 11 different modes (0.0 to 1.0)."""
    gate = _build_gate(50)
    modes = [i / 10 for i in range(11)]

    def sweep():
        for m in modes:
            gate.filter(m)

    return _bench("filter(50 tools, 11 modes)", sweep, iterations=1_000)


def bench_envelope_build() -> BenchmarkResult:
    tool = Tool("read_file", execution_class="read_only")
    return _bench("build_envelope", lambda: build_envelope(tool, 0.5, "ctx", "key"), iterations=5_000)


def bench_envelope_verify() -> BenchmarkResult:
    tool = Tool("read_file", execution_class="read_only")
    env = build_envelope(tool, 0.5, "ctx", "key")
    return _bench("verify_envelope", lambda: verify_envelope(env, "key"), iterations=5_000)


def bench_tool_registration() -> BenchmarkResult:
    """Register 100 tools from scratch."""
    tools = [Tool(f"t_{i}", execution_class=EXECUTION_CLASSES[i % 5]) for i in range(100)]

    def register():
        g = Gate()
        g.add_tools(tools)

    return _bench("register(100 tools)", register, iterations=2_000)


ALL_BENCHMARKS = [
    bench_filter_10_tools,
    bench_filter_100_tools,
    bench_filter_1000_tools,
    bench_filter_mode_sweep,
    bench_envelope_build,
    bench_envelope_verify,
    bench_tool_registration,
]


def run_all() -> list[BenchmarkResult]:
    results = []
    for bench_fn in ALL_BENCHMARKS:
        result = bench_fn()
        results.append(result)
    return results


# --- Pytest tests (assert minimum performance) ---


def test_filter_10_tools_fast():
    """10-tool filter should exceed 50,000 ops/s."""
    r = bench_filter_10_tools()
    assert r.ops_per_second > 50_000, f"Too slow: {r}"


def test_filter_100_tools_fast():
    """100-tool filter should exceed 10,000 ops/s."""
    r = bench_filter_100_tools()
    assert r.ops_per_second > 10_000, f"Too slow: {r}"


def test_filter_1000_tools_acceptable():
    """1000-tool filter should exceed 1,000 ops/s."""
    r = bench_filter_1000_tools()
    assert r.ops_per_second > 1_000, f"Too slow: {r}"


def test_envelope_build_fast():
    """Envelope build should exceed 5,000 ops/s."""
    r = bench_envelope_build()
    assert r.ops_per_second > 5_000, f"Too slow: {r}"


def test_envelope_verify_fast():
    """Envelope verify should exceed 10,000 ops/s."""
    r = bench_envelope_verify()
    assert r.ops_per_second > 10_000, f"Too slow: {r}"
