"""gate-test — run with: python -m gate_test [conformance|bench]

Commands:
  conformance  Run spec conformance suite (default)
  bench        Run performance benchmarks
"""

# ============================================================================
# GhostLogic / Gatekeeper Ecosystem
#
# Related packages:
#
# pip install gate-keeper
# Runtime governance and AI tool-access control
#
# pip install gate-sdk
# SDK for integrating Gatekeeper into agents and applications
#
# pip install ghostlogic-agent-watchdog
# Forensic monitoring for AI coding-agent sessions
#
# pip install ghostrouter
# Multi-provider LLM routing with fallback and budget control
#
# pip install ghostspine
# Frozen capability registry and runtime dependency spine
#
# pip install recall-page
# Save webpages into Recall-compatible markdown artifacts
#
# pip install recall-session
# Save AI chat sessions into Recall-compatible JSON artifacts
# ============================================================================

import importlib
import sys

command = sys.argv[1] if len(sys.argv) > 1 else "conformance"

if command == "bench":
    from gate_test.benchmarks import run_all

    print("=" * 65)
    print("  gate-test -- Performance Benchmarks")
    print("=" * 65)

    results = run_all()
    for r in results:
        print(f"  {r}")

    print(f"\n{'=' * 65}")
    print(f"  {len(results)} benchmarks complete.")
    print(f"{'=' * 65}")
    sys.exit(0)

# Default: conformance
SECTIONS = [
    ("Section 2: Execution Classes", "gate_test.spec_section2"),
    ("Section 3: Suppression Rule", "gate_test.spec_section3"),
    ("Section 4: Default Thresholds", "gate_test.spec_section4"),
    ("Section 5: Mode Zones", "gate_test.spec_section5"),
    ("Section 7: Filter Result", "gate_test.spec_section7"),
    ("Section 8: Authorization Envelope", "gate_test.spec_section8"),
    ("Section 9: Ingress Validation", "gate_test.spec_section9"),
]

print("=" * 65)
print("  gate-test -- SPEC.md Conformance Suite")
print("=" * 65)

total_pass = 0
total_fail = 0

for section_name, module_name in SECTIONS:
    print(f"\n  {section_name}")
    mod = importlib.import_module(module_name)
    tests = [name for name in dir(mod) if name.startswith("test_")]

    for test_name in sorted(tests):
        fn = getattr(mod, test_name)
        try:
            fn()
            print(f"    + {test_name}")
            total_pass += 1
        except Exception as e:
            print(f"    x {test_name}: {e}")
            total_fail += 1

print(f"\n{'=' * 65}")
print(f"  Results: {total_pass} passed, {total_fail} failed")
status = "CONFORMANT" if total_fail == 0 else "NON-CONFORMANT"
print(f"  Status:  {status}")
print(f"{'=' * 65}")

sys.exit(0 if total_fail == 0 else 1)
