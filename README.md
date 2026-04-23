# gate-test

[![status](https://img.shields.io/badge/status-v0.1.0-blue)]()
[![tests](https://img.shields.io/badge/tests-47_passing-brightgreen)]()
[![license](https://img.shields.io/badge/license-Apache_2.0-green)]()

> Spec conformance suite for Maelstrom Gate. Every test maps to a SPEC.md
> section.

Pass this suite = spec-compliant. Point it at any Gate implementation (Python,
Go, or wire-level via `gate-server`) and it verifies behavior section by
section — execution classes, suppression rule, default thresholds, mode zones,
filter result shape, envelope signing, ingress validation.

## Install

```bash
pip install gate-test  # once published
# or from source:
pip install -e .
```

## Run

```bash
python -m gate_test            # conformance suite
python -m gate_test bench      # performance benchmarks
# or via pytest:
pytest tests/
```

Sample output:

```
=== Section 2: Execution Classes    [7/7] ===
=== Section 3: Suppression Rule     [5/5] ===
=== Section 4: Default Thresholds   [4/4] ===
=== Section 5: Mode Zones           [6/6] ===
=== Section 7: Filter Result        [5/5] ===
=== Section 8: Authorization Envelope [9/9] ===
=== Section 9: Ingress Validation   [6/6] ===
=== Ecosystem Integration           [5/5] ===
=== Performance Benchmarks          [5/5] ===
```

## Cross-language vectors

`vectors/envelope_signing.json` contains deterministic envelope signing vectors
used to prove `gate-server-go` and `gate-server` produce byte-identical
HMAC-SHA256 signatures. Any new implementation runs against these.

## Sections tested

| Section | Coverage |
|---------|----------|
| 2 | Execution class definitions |
| 3 | Suppression rule (mode ≥ threshold) |
| 4 | Default thresholds per class |
| 5 | Mode zone boundaries (normal/elevated/crisis) |
| 7 | `ToolFilter` shape and invariants |
| 8 | Authorization envelope signing + verification |
| 9 | Ingress validation (proposal rejection at mode) |

Plus ecosystem integration: `gate-sdk`, `gate-policy`, `gate-schema`,
`gate-compliance` cooperation.

## Optional deps

```bash
pip install gate-test[policy]  # include gate-policy integration tests
pip install gate-test[schema]  # include gate-schema validation tests
```

## How it fits

Testing and reference for [Maelstrom Gate](https://github.com/adam-scott-thomas/maelstrom-gate).
The thing new implementations run before claiming conformance.

## License

Apache-2.0.
