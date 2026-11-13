from __future__ import annotations
from pydantic import BaseModel
from typing import Any


class GraphNode(BaseModel):
    id: str
    name: str | None = None
    type: str = "process"


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    timestamp: float | None = None


class GraphPayload(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]

    def nodes_as_dicts(self) -> list[dict]:
        return [n.model_dump() for n in self.nodes]

    def edges_as_dicts(self) -> list[dict]:
        return [e.model_dump() for e in self.edges]


class TriageRequest(BaseModel):
    graph: GraphPayload
    format: str = "format_a"          # format_a | format_b
    alert_id: str | None = None       # re-triage an existing alert
    label: str | None = None          # optional analyst label / note


class TriageRunOut(BaseModel):
    run_id: str
    alert_id: str
    format: str
    model: str
    duration_ms: int
    injection_guard: dict[str, Any]
    llm_success: bool
    llm_blocked: bool
    accused_pre: list[str]
    accused_post: list[str]
    metrics: dict[str, Any]
    verifier_source: str              # "pcv" or "stub"

