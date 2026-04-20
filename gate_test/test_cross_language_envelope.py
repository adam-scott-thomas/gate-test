"""Cross-language envelope signing conformance test.

Both the Python reference (maelstrom-gate) and the Go implementation
(gate-server-go) MUST produce byte-identical canonical JSON and the
same HMAC-SHA256 signatures for the same inputs.

Vectors are stored in vectors/envelope_signing.json so the Go test
suite (gate-server-go/internal/envelope/vectors_test.go) can load and
assert against the same expected values.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

VECTORS_PATH = Path(__file__).parent.parent / "vectors" / "envelope_signing.json"


def _load_vectors() -> dict:
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))


def _sign(payload: dict, key: str) -> tuple[str, str, str]:
    """Reproduce the signing algorithm in pure stdlib for conformance.

    Returns (canonical_json, sha256_hex, hmac_hex).
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).digest()
    sig = hmac.new(key.encode(), digest, hashlib.sha256).hexdigest()
    return canonical, digest.hex(), sig


def test_vectors_file_exists():
    assert VECTORS_PATH.exists(), f"vectors file missing: {VECTORS_PATH}"


def test_canonical_and_signature_match_vectors():
    """Pure-stdlib signing must reproduce every vector's canonical JSON and sig."""
    data = _load_vectors()
    key = data["signing_key"]
    for v in data["vectors"]:
        canonical, sha_hex, sig = _sign(v["input"], key)
        assert canonical == v["canonical_json"], f"{v['name']}: canonical JSON drift"
        assert sig == v["expected_signature"], f"{v['name']}: signature drift"


def test_python_core_matches_vectors():
    """maelstrom-gate's _canonical_hash + HMAC must match vectors."""
    from maelstrom_gate.envelope import _canonical_hash

    data = _load_vectors()
    key = data["signing_key"]
    for v in data["vectors"]:
        digest = _canonical_hash(v["input"])
        sig = hmac.new(key.encode(), digest, hashlib.sha256).hexdigest()
        assert sig == v["expected_signature"], f"{v['name']}: core drifted from vectors"
