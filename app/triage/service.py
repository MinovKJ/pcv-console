"""
Triage service: orchestrates injection check → LLM → verifier → metrics.
Stores results in MongoDB.
"""
from __future__ import annotations

import time
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.triage.injection_guard import scan_for_injection
from app.triage.verifier_adapter import run_verification
from app.triage.schemas import TriageRequest, TriageRunOut


_cfg = get_settings()

# ── Graph serialization helpers (inline, no PCV import needed) ─────────────────

def _serialize_format_a(nodes: list[dict], edges: list[dict]) -> str:
    lines = ["### FORMAT A: CHRONOLOGICAL PROVENANCE STREAM", "Observed System Entities:"]
    for n in nodes:
        lines.append(f'  - Canonical ID: "{n["id"]}" | Display Name: "{n.get("name", n["id"])}" (Type: {n.get("type","?")})')
    lines.append("\nChronological Sequence of Interactions:")
    for e in sorted(edges, key=lambda x: x.get("timestamp") or float("inf")):
        t = e.get("timestamp")
        t_str = f"t={t}" if t is not None else "time=N/A"
        lines.append(f'  [{t_str}] "{e["source"]}" --{e.get("relation","?")}---> "{e["target"]}"')
    return "\n".join(lines)


def _serialize_format_b(nodes: list[dict], edges: list[dict]) -> str:
    from collections import defaultdict
    by_src: dict = defaultdict(list)
    for e in edges:
        by_src[str(e["source"])].append(e)
    lines = ["### FORMAT B: TYPED GRAPH ADJACENCY RECORDS", "Observed System Entities:"]
    for n in nodes:
        lines.append(f'  - Canonical ID: "{n["id"]}" | Display Name: "{n.get("name", n["id"])}" (Type: {n.get("type","?")})')
    lines.append("\nDirected Graph Adjacency Records:")
    for n in nodes:
        src = str(n["id"])
        outgoing = by_src.get(src, [])
        lines.append(f'  From Node "{src}":')
        if not outgoing:
            lines.append('    (No outgoing interactions)')
        else:
            for e in outgoing:
                t = e.get("timestamp")
                t_str = f"t={t}" if t is not None else "time=N/A"
                lines.append(f'    --> "{e["target"]}" [Relation: {e.get("relation","?")} | {t_str}]')
    return "\n".join(lines)


_SERIALIZERS = {
    "format_a": _serialize_format_a,
    "format_b": _serialize_format_b,
}


# ── LLM call (Ollama structured output) ────────────────────────────────────────

_PCV_SCHEMA = {
    "type": "object",
    "properties": {
        "direct_edge_claims": {"type": "array", "items": {"type": "object"}},
        "path_claims": {"type": "array", "items": {"type": "object"}},
        "accused_entity_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["direct_edge_claims", "path_claims", "accused_entity_ids"],
}

_SYSTEM_PROMPT = (
    "You are an expert SOC provenance analyst. "
    "Analyze the telemetry graph and output structured claims in JSON. "
    "Only use canonical IDs. Ground every assertion in the graph."
)


async def _call_llm(serialized: str) -> tuple[bool, dict, str]:
    """Returns (success, parsed_claims, raw_response)."""
    payload = {
        "model": _cfg.ollama_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"[TELEMETRY]\n{serialized}\n\nOutput your structured claims."},
        ],
        "format": _PCV_SCHEMA,
        "options": {"temperature": 0.0, "top_p": 1.0, "seed": 42},
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{_cfg.ollama_host}/api/chat", json=payload)
            r.raise_for_status()
            content = r.json()["message"]["content"]
            return True, json.loads(content), content
    except Exception as exc:
        return False, {}, str(exc)


# ── Main triage orchestrator ────────────────────────────────────────────────────

async def run_triage(
    request: TriageRequest,
    submitted_by: int,
    mongo: AsyncIOMotorDatabase,
) -> TriageRunOut:
    """Full pipeline: inject-check → serialise → LLM → verify → store in Mongo."""
    run_id = str(uuid.uuid4())
    t0 = time.monotonic()

    nodes = request.graph.nodes
    edges = request.graph.edges
    fmt = request.format.lower()

    # 1. Serialise the graph
    serializer_fn = _SERIALIZERS.get(fmt, _serialize_format_a)
    serialized = serializer_fn(nodes, edges)

    # 2. Injection Guard (Module 1 — runs before LLM)
    guard = scan_for_injection(serialized)
    injection_result = {
        "is_clean": guard.is_clean,
        "risk_score": guard.risk_score,
        "explicit_hit_count": guard.explicit_hit_count,
        "subtle_hit_count": guard.subtle_hit_count,
        "recommendation": guard.recommendation,
        "matches": [
            {"threat_class": m.threat_class, "pattern_name": m.pattern_name,
             "matched_text": m.matched_text, "char_offset": m.char_offset}
            for m in guard.matches
        ],
    }

    # 3. LLM call (skipped if explicit injection detected)
    llm_success = False
    llm_output: dict = {}
    llm_raw = ""
    direct_claims: list = []
    path_claims: list = []
    accused_pre: list = []

    if not guard.should_block:
        llm_success, llm_output, llm_raw = await _call_llm(serialized)
        if llm_success:
            direct_claims = llm_output.get("direct_edge_claims", [])
            path_claims = llm_output.get("path_claims", [])
            accused_pre = llm_output.get("accused_entity_ids", [])

    # 4. PCV Structural Verification
    verifier_result = run_verification(nodes, edges, direct_claims, path_claims, accused_pre)
    accepted_nodes: set = set(verifier_result.get("accepted_nodes", []))
    accused_post = [e for e in accused_pre if str(e).strip() in accepted_nodes]

    # 5. Compute metrics inline
    total_direct = verifier_result.get("direct_claims_count", 0)
    total_paths = verifier_result.get("path_claims_count", 0)
    metrics = {
        "direct_valid": verifier_result.get("direct_valid", 0),
        "direct_invalid": verifier_result.get("direct_invalid", 0),
        "direct_unverifiable": verifier_result.get("direct_unverifiable", 0),
        "DEVR": ((verifier_result.get("direct_invalid", 0) + verifier_result.get("direct_unverifiable", 0)) / total_direct)
                if total_direct > 0 else None,
        "path_valid": verifier_result.get("path_valid", 0),
        "path_invalid": verifier_result.get("path_invalid", 0),
        "PIR": (verifier_result.get("path_invalid", 0) / total_paths) if total_paths > 0 else None,
        "temporal_inversions": verifier_result.get("temporal_inversions", 0),
        "evaluable_temporal_pairs": verifier_result.get("evaluable_temporal_pairs", 0),
        "injection_risk_score": guard.risk_score,
    }

    duration_ms = round((time.monotonic() - t0) * 1000)

    # 6. Store the alert document (if not already stored)
    alert_id = request.alert_id or str(uuid.uuid4())
    if not request.alert_id:
        await mongo["alerts"].insert_one({
            "_id": alert_id,
            "submitted_by": submitted_by,
            "submitted_at": datetime.now(timezone.utc),
            "graph": {"nodes": nodes, "edges": edges},
            "label": request.label,
        })

    # 7. Store the triage run document
    run_doc = {
        "_id": run_id,
        "alert_id": alert_id,
        "submitted_by": submitted_by,
        "format": fmt,
        "model": _cfg.ollama_model,
        "created_at": datetime.now(timezone.utc),
        "duration_ms": duration_ms,
        "injection_guard": injection_result,
        "llm_success": llm_success,
        "llm_blocked": guard.should_block,
        "llm_output": llm_output,
        "llm_raw": llm_raw,
        "verifier_result": verifier_result,
        "accused_pre": accused_pre,
        "accused_post": accused_post,
        "metrics": metrics,
        "serialized_graph": serialized,
    }
    await mongo["triage_runs"].insert_one(run_doc)

    return TriageRunOut(
        run_id=run_id,
        alert_id=alert_id,
        format=fmt,
        model=_cfg.ollama_model,
        duration_ms=duration_ms,
        injection_guard=injection_result,
        llm_success=llm_success,
        llm_blocked=guard.should_block,
        accused_pre=accused_pre,
        accused_post=accused_post,
        metrics=metrics,
        verifier_source=verifier_result.get("source", "unknown"),
    )
