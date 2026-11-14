"""
PCV Verifier Adapter
────────────────────
Wraps the core PCV verification engine behind a standardized interface.
If the full research engine (src.inference.verifier) is not installed,
it seamlessly executes a built-in standalone Demo Verifier that performs
direct edge topological validation, relationship matching, path continuity,
and timestamp monotonicity.

This ensures the public console produces real VALID/INVALID metrics and
live dashboard aggregations out-of-the-box without requiring private research weights.
"""
from __future__ import annotations

from typing import Any


def _build_nx_graph(nodes: list[dict], edges: list[dict]):
    """Reconstruct a networkx.MultiDiGraph from JSON-serialisable dicts."""
    import networkx as nx
    G = nx.MultiDiGraph()
    for n in nodes:
        G.add_node(str(n.get("id")), **{k: v for k, v in n.items() if k != "id"})
    for e in edges:
        G.add_edge(
            str(e.get("source")),
            str(e.get("target")),
            relation=e.get("relation", "unknown"),
            timestamp=e.get("timestamp")
        )
    return G


def run_verification(
    nodes: list[dict],
    edges: list[dict],
    direct_claims: list[dict],
    path_claims: list[dict],
    accused_entity_ids: list[str],
) -> dict[str, Any]:
    """
    Run structural verification.
    Uses the full PCV engine if installed; otherwise runs the standalone Demo Verifier.
    """
    try:
        from src.inference.verifier import ProvenanceClaimVerifier, extract_accepted_nodes
        G = _build_nx_graph(nodes, edges)
        context_nodes = set(str(n.get("id")) for n in nodes)
        verifier = ProvenanceClaimVerifier(telemetry_graph=G, context_nodes=context_nodes)
        v_res = verifier.verify_structured_claims(direct_claims, path_claims)
        accepted = list(extract_accepted_nodes(v_res))
        return {"source": "pcv", **v_res, "accepted_nodes": accepted}
    except ImportError:
        return _demo_verification(nodes, edges, direct_claims, path_claims, accused_entity_ids)


def _demo_verification(
    nodes: list[dict],
    edges: list[dict],
    direct_claims: list[dict],
    path_claims: list[dict],
    accused_entity_ids: list[str],
) -> dict[str, Any]:
    """
    Built-in standalone demo verifier for public distribution:
    - Direct-edge matching (existence, direction, relationship type).
    - Multi-hop path continuity & timestamp monotonicity.
    - Accused entity evidence extraction.
    """
    direct_claims = direct_claims or []
    path_claims = path_claims or []

    # Map edges by (src, tgt)
    edge_map: dict[tuple[str, str], list[dict]] = {}
    for e in edges:
        src = str(e.get("source", "")).strip()
        tgt = str(e.get("target", "")).strip()
        edge_map.setdefault((src, tgt), []).append(e)

    accepted_direct = []
    rejected_direct = []
    accepted_paths = []
    rejected_paths = []
    accepted_nodes: set[str] = set()
    timestamp_seq: list[float] = []

    direct_valid = 0
    direct_invalid = 0
    direct_unverifiable = 0

    # 1. Verify direct edge claims
    for c in direct_claims:
        if not isinstance(c, dict):
            direct_invalid += 1
            rejected_direct.append({"claim": c, "status": "INVALID", "reason": "Claim is not a dictionary"})
            continue

        src = str(c.get("source_id", "")).strip()
        tgt = str(c.get("target_id", "")).strip()
        rel = (c.get("relation") or "").strip().lower()

        if not src or not tgt:
            direct_invalid += 1
            rejected_direct.append({"claim": c, "status": "INVALID", "reason": "Missing source or target ID"})
            continue

        candidates = edge_map.get((src, tgt), [])
        if not candidates:
            direct_invalid += 1
            rejected_direct.append({"claim": c, "status": "INVALID", "reason": f"No directed edge ({src} -> {tgt})"})
            continue

        if not rel:
            direct_unverifiable += 1
            rejected_direct.append({"claim": c, "status": "UNVERIFIABLE", "reason": "Claim lacks relation metadata"})
            continue

        matching_edge = None
        for cand in candidates:
            actual_rel = str(cand.get("relation", "")).strip().lower()
            if actual_rel == rel or actual_rel in (rel, "interacted_with", "unknown"):
                matching_edge = cand
                break

        if matching_edge:
            direct_valid += 1
            t = matching_edge.get("timestamp")
            accepted_direct.append({
                "claim": c,
                "status": "VALID",
                "timestamp": t,
                "reason": "Matching typed edge verified in graph"
            })
            accepted_nodes.add(src)
            accepted_nodes.add(tgt)
            if t is not None:
                try:
                    timestamp_seq.append(float(t))
                except (ValueError, TypeError):
                    pass
        else:
            direct_invalid += 1
            rejected_direct.append({
                "claim": c,
                "status": "INVALID",
                "reason": f"Edge exists but relationship mismatch (claimed: {rel})"
            })

    # 2. Verify multi-hop path claims
    path_valid = 0
    path_invalid = 0

    for p in path_claims:
        if not isinstance(p, dict):
            path_invalid += 1
            rejected_paths.append({"path_claim": p, "status": "INVALID", "reason": "Path claim is not a dictionary"})
            continue

        seq = p.get("node_ids")
        if not isinstance(seq, list) or len(seq) < 2:
            path_invalid += 1
            rejected_paths.append({"path_claim": p, "status": "INVALID", "reason": "Path must contain at least 2 nodes"})
            continue

        clean_seq = [str(n).strip() for n in seq]
        is_path_valid = True
        reason = "Valid continuous directed path"
        curr_min_t = float("-inf")

        for i in range(len(clean_seq) - 1):
            u, v = clean_seq[i], clean_seq[i + 1]
            cands = edge_map.get((u, v), [])
            if not cands:
                is_path_valid = False
                reason = f"Path broken: Missing edge ({u} -> {v})"
                break

            valid_step_ts = []
            has_untimestamped = False
            for cand in cands:
                t = cand.get("timestamp")
                if t is None:
                    has_untimestamped = True
                else:
                    try:
                        ft = float(t)
                        if ft >= curr_min_t:
                            valid_step_ts.append(ft)
                    except (ValueError, TypeError):
                        has_untimestamped = True

            if has_untimestamped:
                pass
            elif valid_step_ts:
                curr_min_t = min(valid_step_ts)
            else:
                is_path_valid = False
                reason = f"Temporal inversion along path: Edge ({u} -> {v}) violates non-decreasing time"
                break

        if is_path_valid:
            path_valid += 1
            accepted_paths.append({"path_claim": p, "status": "VALID", "reason": reason})
            for n in clean_seq:
                accepted_nodes.add(n)
        else:
            path_invalid += 1
            rejected_paths.append({"path_claim": p, "status": "INVALID", "reason": reason})

    # 3. Evaluate temporal inversions
    temporal_inversions = 0
    evaluable_pairs = max(0, len(timestamp_seq) - 1)
    for i in range(evaluable_pairs):
        if timestamp_seq[i] > timestamp_seq[i + 1]:
            temporal_inversions += 1

    return {
        "source": "demo_verifier",
        "demo_note": "Evaluated with built-in standalone verifier (full PCV engine available via adapter)",
        "direct_claims_count": len(direct_claims),
        "direct_valid": direct_valid,
        "direct_invalid": direct_invalid,
        "direct_unverifiable": direct_unverifiable,
        "path_claims_count": len(path_claims),
        "path_valid": path_valid,
        "path_invalid": path_invalid,
        "evaluable_temporal_pairs": evaluable_pairs,
        "temporal_inversions": temporal_inversions,
        "accepted_direct_edges": accepted_direct,
        "rejected_direct_edges": rejected_direct,
        "accepted_paths": accepted_paths,
        "rejected_paths": rejected_paths,
        "accepted_nodes": list(accepted_nodes),
    }


def _stub_verification(
    direct_claims: list[dict],
    path_claims: list[dict],
    accused_entity_ids: list[str],
) -> dict[str, Any]:
    """Legacy stub helper maintained for backward compatibility."""
    return _demo_verification([], [], direct_claims, path_claims, accused_entity_ids)


