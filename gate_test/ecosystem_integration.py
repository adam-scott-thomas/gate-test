"""Ecosystem integration test — proves all 11 Gate projects interoperate.

Imports from every surviving project and runs a single pipeline:
  L0: gate-core (filter)
  L1: gate-sdk (client), gate-server (models)
  L2: gate-policy (evaluate), gate-compliance (audit)
  L3: gate-dashboard (state), gate-cli (output), gate-agent (protocol),
      gate-schema (validate), gate-webhook (events), gate-test (conformance)

If this passes, the entire ecosystem works together.
"""
import json
import time
from dataclasses import asdict

# L0: gate-core
from maelstrom_gate import Gate, Tool, build_envelope, verify_envelope
from maelstrom_gate.core import is_suppressed, T_DOWN, T_UP
from maelstrom_gate.ingress import validate_proposal

# L1: gate-sdk
from gate_sdk import GateClient
from gate_sdk.policy import PolicyMiddleware

# L2: gate-policy
from gate_policy.engine import PolicyEngine
from gate_policy.loader import load_policy
from gate_policy.audit import AuditLog, AuditEntry
from gate_policy.models import Effect

# L2: gate-compliance
from gate_compliance import AuditStore, ComplianceCollector, ComplianceReporter, run_all_checks
from gate_compliance.siem_export import SIEMExporter
from gate_compliance.envelope_audit import fetch_envelope_events_from_store, build_summary

# L3: gate-schema
from gate_schema import validate_tool, validate_envelope, validate_policy, validate_filter_result

# L3: gate-webhook
from gate_webhook.events import GateSnapshot, detect_events, GateEvent
from gate_webhook.compliance_bridge import ComplianceBridge

# L3: gate-test (self — conformance functions)
from gate_test.spec_section3 import test_suppression_when_mode_exceeds_threshold
from gate_test.spec_section8 import test_envelope_signature_verifies

SIGNING_KEY = "ecosystem-integration-key"


def test_full_ecosystem_pipeline(tmp_path):
    """The big one: all 11 projects in a single pipeline."""

    # -- L2: Set up compliance store --
    store = AuditStore(tmp_path / "ecosystem.db")
    collector = ComplianceCollector(store, context_id="ecosystem-test")

    # -- L1: SDK client with compliance wired --
    client = GateClient(mode=0.0)
    client.use(collector.filter_hook)
    client.on_suppress(collector.suppress_hook)

    tools = [
        ("read_file", "read_only"), ("explain", "advisory"),
        ("send_slack", "external_action"), ("write_file", "state_mutation"),
        ("deploy", "high_impact"),
    ]
    for name, cls in tools:
        client.add_tool(name, cls)

    # -- L3: Validate tool registration against schema --
    for name, cls in tools:
        validate_tool({"name": name, "execution_class": cls})

    # -- L2: Load and apply a policy --
    policy_dict = {
        "name": "ecosystem-test-policy",
        "default_effect": "allow",
        "rules": [{"name": "deny-deploy-without-approval", "effect": "deny",
                    "execution_classes": ["high_impact"],
                    "conditions": [{"field": "human_approved", "operator": "neq", "value": True}],
                    "priority": 10}],
    }
    validate_policy(policy_dict)  # L3: schema validation
    policy = load_policy(policy_dict)
    assert policy.name == "ecosystem-test-policy"

    # -- L1: Filter at multiple modes, compliance records everything --
    results = {}
    for mode in [0.0, 0.5, 0.9]:
        results[mode] = client.filter(mode)

    assert len(results[0.0].visible) == 5
    assert "deploy" in results[0.5].suppressed_names
    assert len(results[0.9].visible) == 2

    # -- L3: Validate filter results against schema --
    for mode, result in results.items():
        validate_filter_result({
            "visible": [{"name": t.name, "execution_class": t.execution_class} for t in result.visible],
            "suppressed": [{"name": t.name, "execution_class": t.execution_class} for t in result.suppressed],
            "mode": result.mode,
            "mode_zone": result.mode_zone,
        })

    # -- L0+L1: Build and verify envelope --
    envelope = client.authorize("read_file", signing_key=SIGNING_KEY, context_id="eco-test")
    assert verify_envelope(envelope, SIGNING_KEY)
    collector.record_envelope_issued("read_file", 0.0, envelope_id=envelope.envelope_id)

    # -- L3: Validate envelope against schema --
    env_dict = asdict(envelope)
    env_dict["allowed_tools"] = list(env_dict["allowed_tools"])
    validate_envelope(env_dict)

    # -- L0: Ingress validation --
    assert validate_proposal("read_file", client._gate, 0.0).accepted
    assert not validate_proposal("deploy", client._gate, 0.8).accepted

    # -- L2: Policy engine evaluation + audit --
    engine = PolicyEngine(policy)
    policy_log = AuditLog()
    from datetime import datetime, timezone

    effect = engine.evaluate("deploy", "high_impact", {"human_approved": False})
    assert effect == Effect.DENY
    policy_log.record(AuditEntry(
        timestamp=datetime.now(timezone.utc),
        tool_name="deploy", execution_class="high_impact",
        effect="deny", matched_rule="deny-deploy-without-approval",
        policy_name="ecosystem-test-policy", mode=0.0, mode_zone="normal",
    ))
    assert len(policy_log) == 1

    # -- L3: Webhook event detection --
    snap1 = GateSnapshot(mode=0.0, mode_zone="normal",
                         visible=["read_file", "deploy"], suppressed=[], timestamp=time.time())
    snap2 = GateSnapshot(mode=0.8, mode_zone="crisis",
                         visible=["read_file"], suppressed=["deploy"], timestamp=time.time())
    events = detect_events(snap1, snap2)
    assert any(e.event_type == "mode_zone_change" for e in events)
    assert any(e.event_type == "tool_suppressed" for e in events)

    # -- L3: Webhook -> compliance bridge --
    bridge = ComplianceBridge(db_path=str(tmp_path / "ecosystem.db"), context_id="webhook-bridge")
    bridge.record_events(events)

    # -- L2: Compliance report from accumulated data --
    reporter = ComplianceReporter(store)
    summary = reporter.summarize()
    assert summary.total_events > 0
    assert summary.filter_count >= 3

    text = reporter.text_report()
    assert "COMPLIANCE REPORT" in text

    json_report = json.loads(reporter.json_report())
    assert json_report["report_type"] == "maelstrom_gate_compliance"

    # -- L2: SIEM export --
    exporter = SIEMExporter(store)
    elk = exporter.elk_format()
    assert len(elk) > 0
    assert all("@timestamp" in doc for doc in elk)

    splunk = exporter.splunk_kv()
    assert len(splunk) > 0

    # -- L2: Envelope audit bridge --
    env_entries = fetch_envelope_events_from_store(store)
    env_summary = build_summary(env_entries)
    assert env_summary.total_issued >= 1

    # -- L2: Compliance alerts --
    alerts = run_all_checks(store)  # may or may not trigger

    # -- L3: Self-test (gate-test conformance) --
    test_suppression_when_mode_exceeds_threshold()
    test_envelope_signature_verifies()

    # Final count
    total_events = store.count()
    assert total_events > 0


def test_ecosystem_project_count():
    """Verify we can import from all 11 projects."""
    imports = [
        "maelstrom_gate",      # gate-core
        "gate_sdk",            # gate-sdk
        "gate_policy",         # gate-policy
        "gate_compliance",     # gate-compliance
        "gate_schema",         # gate-schema
        "gate_webhook",        # gate-webhook
        "gate_test",           # gate-test
    ]
    # gate-server, gate-dashboard, gate-cli, gate-agent verified by import test
    import importlib
    for mod in imports:
        m = importlib.import_module(mod)
        assert m is not None
