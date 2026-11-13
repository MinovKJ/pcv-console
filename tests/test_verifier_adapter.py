"""
Tests for the verifier adapter — offline, no DB, no LLM.
Verifies that the stub and (if installed) the real PCV adapter
both return well-formed result dictionaries.
"""
import pytest
from app.triage.verifier_adapter import run_verification, _stub_verification


NODES = [
    {"id": "101", "name": "powershell.exe", "type": "process"},
    {"id": "202", "name": "cmd.exe", "type": "process"},
    {"id": "303", "name": "beacon.exe", "type": "process"},
    {"id": "404", "name": "198.51.100.1:443", "type": "socket"},
]
EDGES = [
    {"source": "101", "target": "202", "relation": "fork", "timestamp": 100.0},
    {"source": "202", "target": "303", "relation": "exec", "timestamp": 110.0},
    {"source": "303", "target": "404", "relation": "connect", "timestamp": 120.0},
]

DIRECT_CLAIMS = [
    {"source_id": "101", "target_id": "202", "relation": "fork"},
    {"source_id": "202", "target_id": "999", "relation": "exec"},   # fabricated target
]
PATH_CLAIMS = [{"node_ids": ["101", "202", "303", "404"]}]
ACCUSED = ["303", "404"]


def _assert_well_formed(result: dict):
    required_keys = [
        "direct_claims_count", "direct_valid", "direct_invalid", "direct_unverifiable",
        "path_claims_count", "path_valid", "path_invalid",
        "accepted_direct_edges", "rejected_direct_edges",
        "accepted_paths", "rejected_paths", "accepted_nodes",
    ]
    for k in required_keys:
        assert k in result, f"Missing key: {k}"


def test_stub_well_formed():
    result = _stub_verification(DIRECT_CLAIMS, PATH_CLAIMS, ACCUSED)
    _assert_well_formed(result)
    assert result["source"] == "stub"
    # Stub marks everything UNVERIFIABLE — zero valid
    assert result["direct_valid"] == 0
    assert result["direct_unverifiable"] == len(DIRECT_CLAIMS)
    assert result["accepted_nodes"] == []


def test_run_verification_returns_well_formed():
    result = run_verification(NODES, EDGES, DIRECT_CLAIMS, PATH_CLAIMS, ACCUSED)
    _assert_well_formed(result)
    assert result["source"] in ("pcv", "stub")


def test_pcv_verifier_valid_edge():
    """If PCV is installed, the first direct claim (101->202 fork) should be VALID."""
    result = run_verification(NODES, EDGES, DIRECT_CLAIMS[:1], [], ACCUSED)
    if result["source"] == "pcv":
        assert result["direct_valid"] == 1
        assert result["direct_invalid"] == 0
    else:
        # Stub mode — just verify keys
        _assert_well_formed(result)


def test_pcv_verifier_fabricated_target_invalid():
    """If PCV is installed, the second claim (202->999 exec) should be INVALID (node 999 absent)."""
    result = run_verification(NODES, EDGES, DIRECT_CLAIMS[1:2], [], ACCUSED)
    if result["source"] == "pcv":
        assert result["direct_valid"] == 0
        assert result["direct_invalid"] >= 1
    else:
        _assert_well_formed(result)


def test_pcv_verifier_valid_path():
    """Full 4-hop path 101->202->303->404 should be VALID when PCV is installed."""
    result = run_verification(NODES, EDGES, [], PATH_CLAIMS, ACCUSED)
    if result["source"] == "pcv":
        assert result["path_valid"] == 1
    else:
        _assert_well_formed(result)


def test_empty_claims_no_crash():
    result = run_verification(NODES, EDGES, [], [], [])
    _assert_well_formed(result)
    assert result["direct_claims_count"] == 0
    assert result["path_claims_count"] == 0


def test_empty_graph_no_crash():
    result = run_verification([], [], DIRECT_CLAIMS, PATH_CLAIMS, ACCUSED)
    _assert_well_formed(result)

