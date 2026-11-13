"""
Injection Guard Module
─────────────────────
Pre-LLM safety check: scans serialized provenance graph text for
adversarial instruction overrides before it is passed to the LLM.

Detects two threat classes:
  1. EXPLICIT  – overt override / MUST-DO / authority-spoofing strings.
  2. SUBTLE    – incentive-conflict / policy-impersonation language designed
                 to steer the model without obvious tell-tale keywords.

Returns a structured InjectionGuardResult — no live calls, fully synchronous,
deterministic, and usable independently of the PCV verifier.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Pattern banks ──────────────────────────────────────────────────────────────

# EXPLICIT: direct instruction override signals
_EXPLICIT_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("override_keyword",    re.compile(r"\[(?:SOC_SECURITY_OVERRIDE|CRITICAL_FORENSIC_ALERT|SYSTEM_OVERRIDE|ADMIN_OVERRIDE|SECURITY_OVERRIDE)\]", re.I)),
    ("must_accuse",         re.compile(r"\bYOU\s+MUST\s+(?:ACCUSE|INCLUDE|FLAG|CLASSIFY|LIST)\b", re.I)),
    ("do_not_include",      re.compile(r"\bDO\s+NOT\s+(?:INCLUDE|REPORT|FLAG|ACCUSE)\b", re.I)),
    ("ignore_instruction",  re.compile(r"\bIGNORE\s+(?:PREVIOUS|ALL\s+PRIOR|ABOVE)\s+INSTRUCTIONS?\b", re.I)),
    ("whitelist_spoof",     re.compile(r"\bwhitelisted\s+by\s+(?:Enterprise|EDR|Security|Policy)\b", re.I)),
    ("classify_benign",     re.compile(r"\bclassify\s+as\s+benign\b", re.I)),
    ("edr_policy_spoof",    re.compile(r"\bEDR\s+policy\s+SEC[-_]?\d{4,}\b", re.I)),
    ("threat_sig_spoof",    re.compile(r"\bThreat\s+signature\s+match\b", re.I)),
    ("dll_sideload_spoof",  re.compile(r"\bDLL\s+side[-_]?loading\b", re.I)),
]

# SUBTLE: incentive-conflict / authority-override patterns without explicit keywords
_SUBTLE_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("maintenance_ticket",   re.compile(r"\b(?:Scheduled|Planned)\b.*?\b(?:maintenance|task|update)\b.*?\bunder\s+Ticket\s+#\w+", re.I)),
    ("sla_pressure",         re.compile(r"\bescalate\s+\w+\s+to\s+avoid\s+SLA\b", re.I)),
    ("anomaly_expected",     re.compile(r"\banomaly\s+(?:is\s+)?expected\s+(?:behavior|activity)\b", re.I)),
    ("legitimate_process",   re.compile(r"\blegitimate\s+(?:maintenance|service|system)\s+(?:process|task|activity)\b", re.I)),
    ("auto_whitelisted",     re.compile(r"\bauto(?:matically)?\s+whitelisted\b", re.I)),
    ("change_ticket",        re.compile(r"\bChange\s+(?:Control\s+)?(?:Ticket|Request)\s+#\w+\b", re.I)),
    ("by_edr_policy",        re.compile(r"\bapproved\s+by\s+(?:security\s+)?policy\b", re.I)),
]

_ALL_PATTERNS = [("EXPLICIT", p) for p in _EXPLICIT_PATTERNS] + \
                [("SUBTLE",   p) for p in _SUBTLE_PATTERNS]


# ── Result dataclass ───────────────────────────────────────────────────────────

@dataclass
class InjectionMatch:
    threat_class: str       # "EXPLICIT" | "SUBTLE"
    pattern_name: str
    matched_text: str
    char_offset: int


@dataclass
class InjectionGuardResult:
    is_clean: bool
    risk_score: float                        # 0.0 (clean) – 1.0 (critically injected)
    explicit_hit_count: int
    subtle_hit_count: int
    matches: list[InjectionMatch] = field(default_factory=list)
    recommendation: str = ""

    @property
    def should_block(self) -> bool:
        """Block the LLM call if any EXPLICIT injection is found."""
        return self.explicit_hit_count > 0

    def summary(self) -> str:
        lines = [
            f"InjectionGuard → clean={self.is_clean}  risk={self.risk_score:.2f}  "
            f"explicit={self.explicit_hit_count}  subtle={self.subtle_hit_count}"
        ]
        for m in self.matches:
            lines.append(f"  [{m.threat_class}] {m.pattern_name} @ char {m.char_offset}: {m.matched_text!r}")
        lines.append(f"  Recommendation: {self.recommendation}")
        return "\n".join(lines)


# ── Main scanner ───────────────────────────────────────────────────────────────

def scan_for_injection(serialized_graph_text: str) -> InjectionGuardResult:
    """
    Scan serialized graph text for adversarial injection before LLM submission.

    Args:
        serialized_graph_text: The text that would be sent to the LLM as the
                               telemetry context (Format A/B/C output).

    Returns:
        InjectionGuardResult with all matches and a risk score.
    """
    matches: list[InjectionMatch] = []
    explicit_hits = 0
    subtle_hits = 0

    for threat_class, (pattern_name, pattern) in _ALL_PATTERNS:
        for m in pattern.finditer(serialized_graph_text):
            matches.append(InjectionMatch(
                threat_class=threat_class,
                pattern_name=pattern_name,
                matched_text=m.group(0),
                char_offset=m.start(),
            ))
            if threat_class == "EXPLICIT":
                explicit_hits += 1
            else:
                subtle_hits += 1

    # Risk score: explicit hits are weighted 3× subtle hits; capped at 1.0
    raw_score = min(1.0, (explicit_hits * 3 + subtle_hits) / 10.0)

    is_clean = (len(matches) == 0)

    if explicit_hits > 0:
        rec = "BLOCK: Explicit instruction override detected. Do not send to LLM."
    elif subtle_hits >= 3:
        rec = "REVIEW: Multiple subtle incentive-override patterns detected. Manual review required."
    elif subtle_hits > 0:
        rec = "CAUTION: Subtle injection pattern(s) detected. Flag result for analyst review."
    else:
        rec = "PASS: No injection patterns detected."

    return InjectionGuardResult(
        is_clean=is_clean,
        risk_score=raw_score,
        explicit_hit_count=explicit_hits,
        subtle_hit_count=subtle_hits,
        matches=matches,
        recommendation=rec,
    )
