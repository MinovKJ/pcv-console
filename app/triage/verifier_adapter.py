"""
PCV Verifier Adapter
────────────────────
Wraps the core PCV verification engine behind a standardized interface.
If the pcv core package is not installed, falls back to a deterministic STUB
that returns a well-formed result, keeping the console fully functional.

To link the core verifier:
    pip install -e /path/to/pcv-core   # or install private package
"""
from __future__ import annotations

from typing import Any


def _build_nx_graph(nodes: list[dict], edges: list[dict]):
    """Reconstruct a networkx.MultiDiGraph from JSON-serialisable dicts."""
    import networkx as nx
    G = nx.MultiDiGraph()
    for n in nodes:
        G.add_node(str(n["id"]), **{k: v for k, v in n.items() if k != "id"})
    for e in edges:
        G.add_edge(str(e["source"]), str(e["target"]),
                   relation=e.get("relation", "unknown"),
                   timestamp=e.get("timestamp"))
    return G


def run_verification(
    nodes: list[dict],
    edges: list[dict],
    direct_claims: list[dict],
    path_claims: list[dict],
    accused_entity_ids: list[str],
) -> dict[str, Any]:
    """
    Run the PCV structural verifier.
    Returns the standard verifier_results dict plus extracted accepted nodes.
    """
    try:
        from src.inference.verifier import ProvenanceClaimVerifier, extract_accepted_nodes
        G = _build_nx_graph(nodes, edges)
        context_nodes = set(str(n["id"]) for n in nodes)
        verifier = ProvenanceClaimVerifier(telemetry_graph=G, context_nodes=context_nodes)
        v_res = verifier.verify_structured_claims(direct_claims, path_claims)
        accepted = list(extract_accepted_nodes(v_res))
        return {"source": "pcv", **v_res, "accepted_nodes": accepted}
    except ImportError:
        return _stub_verification(direct_claims, path_claims, accused_entity_ids)


def _stub_verification(
    direct_claims: list[dict],
    path_claims: list[dict],
    accused_entity_ids: list[str],
) -> dict[str, Any]:
    """
    Deterministic STUB — used when PCV package is not installed.
    Marks every claim as UNVERIFIABLE to avoid false positives.
    """
    return {
        "source": "stub",
        "stub_warning": "Real PCV verifier not installed. Install the pcv package for real results.",
        "direct_claims_count": len(direct_claims),
        "direct_valid": 0,
        "direct_invalid": 0,
        "direct_unverifiable": len(direct_claims),
        "path_claims_count": len(path_claims),
        "path_valid": 0,
        "path_invalid": 0,
        "evaluable_temporal_pairs": 0,
        "temporal_inversions": 0,
        "accepted_direct_edges": [],
        "rejected_direct_edges": [{"claim": c, "status": "UNVERIFIABLE", "reason": "stub"} for c in direct_claims],
        "accepted_paths": [],
        "rejected_paths": [{"path_claim": p, "status": "UNVERIFIABLE", "reason": "stub"} for p in path_claims],
        "accepted_nodes": [],
    }

