# PCV Console

**Alert triage and case management backend for EDR provenance graph analysis.**

Built on top of the Provenance Claim Verifier (PCV) research engine. Analysts submit EDR alerts or provenance subgraphs; the system runs pre-LLM injection detection, LLM-assisted triage, and deterministic structural verification — then stores everything for search and reporting.

> **Isolation note:** This is a standalone engineering project. It imports the PCV verifier as a dependency via an adapter. The PCV research repository (`rp/`) is never modified here.

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │          PCV Console API (FastAPI)       │
                    │                                         │
  Analyst ─HTTP──▶  │  /auth  /users  /cases  /alerts        │
                    │  /triage/run   /dashboard/*            │
                    └────────┬─────────────┬─────────────────┘
                             │             │
                    ┌────────▼──┐   ┌──────▼──────────────────┐
                    │  MySQL 8  │   │      MongoDB 7           │
                    │           │   │                          │
                    │  users    │   │  alerts        (graphs)  │
                    │  cases    │   │  triage_runs   (results) │
                    │  assign.  │   │                          │
                    │  audit    │   │  Aggregation pipelines   │
                    └───────────┘   └──────────────────────────┘
```

### Triage Pipeline (per run)

```
Submit graph ──▶ Injection Guard ──▶ [BLOCK if explicit injection]
                        │
                        ▼ (clean / subtle-only)
                  Serialise graph (Format A or B)
                        │
                        ▼
                  LLM call (Ollama, temp=0, seed=42)
                  direct_edge_claims + path_claims + accused_entity_ids
                        │
                        ▼
                  PCV Structural Verifier
                  VALID / INVALID / UNVERIFIABLE per claim
                        │
                        ▼
                  Offline Metrics (DEVR, PIR, TIR, injection_risk_score)
                        │
                        ▼
                  Store in MongoDB → return TriageRunOut
```

---

## Quick Start

### 1. Prerequisites

- Docker Desktop (with Compose v2)
- Python 3.11+ (for local dev / test)

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set strong passwords and your JWT_SECRET_KEY
```

### 3. Start all services

```bash
docker compose up --build
```

API is available at: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### 4. Seed the database

```bash
# After containers are healthy:
docker compose exec api python scripts/seed_db.py
```

Default credentials after seeding:

| Username  | Password      | Role    |
|-----------|---------------|---------|
| `admin`   | `admin1234`   | admin   |
| `analyst1`| `analyst1234` | analyst |

**Change these immediately in any non-local environment.**

### 5. Run the test suite (no Docker required)

```bash
pip install -r requirements.txt -r requirements-dev.txt aiosqlite
pytest tests/test_injection_guard.py tests/test_verifier_adapter.py -v
```

---

## API Reference (key endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | Get JWT access + refresh tokens |
| `POST` | `/auth/refresh` | Rotate access token |
| `GET`  | `/users/me` | Current user info |
| `POST` | `/cases/` | Create a new investigation case |
| `POST` | `/cases/{id}/alerts` | Link an alert to a case |
| `POST` | `/triage/run` | **Submit graph → full pipeline** |
| `GET`  | `/triage/runs` | List triage run summaries |
| `GET`  | `/triage/runs/{run_id}` | Full run detail |
| `GET`  | `/dashboard/verification-pass-rate` | DEVR/PIR by format |
| `GET`  | `/dashboard/injection-stats` | Injection block counts |
| `GET`  | `/dashboard/temporal-inversion-rate` | TIR by format |
| `GET`  | `/dashboard/throughput` | Avg duration, total runs |

---

## Injection Guard Module

Located at `app/triage/injection_guard.py`. Runs **before** the LLM call.

Detects two threat classes:

| Class | Examples | Action |
|-------|----------|--------|
| **EXPLICIT** | `[SOC_SECURITY_OVERRIDE]`, `YOU MUST ACCUSE`, `DO NOT INCLUDE`, `classify as benign` | **Block** — LLM never called |
| **SUBTLE** | Maintenance-ticket spoofing, SLA-pressure language, change-control impersonation | **Flag** — run proceeds, result marked for review |

Returns `InjectionGuardResult` with risk score (0.0–1.0), hit counts, and matched segments.

---

## Plugging in the Real PCV Verifier

The adapter in `app/triage/verifier_adapter.py` tries:

```python
from src.inference.verifier import ProvenanceClaimVerifier, extract_accepted_nodes
```

If the PCV package is not installed, it falls back to a stub that marks all claims `UNVERIFIABLE` (safe default — no false positives).

To use the real verifier:

```bash
# From the console project root:
pip install -e /path/to/rp
```

or add `pcv @ file:///path/to/rp` to `requirements.txt`.

---

## Project Structure

```
pcv-console/
├── app/
│   ├── main.py                   # FastAPI app + lifespan
│   ├── config.py                 # Pydantic settings
│   ├── dependencies.py           # JWT guard, role check, audit logger
│   ├── auth/                     # Login, refresh, JWT utils
│   ├── users/                    # User CRUD (admin-only create)
│   ├── cases/                    # Case management + alert assignment
│   ├── alerts/                   # Alert document store (Mongo)
│   ├── triage/
│   │   ├── injection_guard.py    # ← Pre-LLM injection scanner
│   │   ├── verifier_adapter.py   # ← PCV verifier wrapper / stub
│   │   ├── service.py            # ← Full pipeline orchestrator
│   │   ├── router.py
│   │   └── schemas.py
│   ├── dashboard/                # Aggregation pipeline endpoints
│   └── db/
│       ├── mysql.py              # SQLAlchemy async engine
│       ├── mongo.py              # Motor async client
│       └── models/               # ORM: User, Case, AlertAssignment, AuditLog
├── tests/
│   ├── test_injection_guard.py   # 15 offline unit tests
│   ├── test_verifier_adapter.py  # 7 adapter tests (stub + real PCV)
│   └── test_triage.py            # Integration tests (mocked DB/LLM)
├── scripts/seed_db.py            # Seeds MySQL + MongoDB with synthetic data
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── .github/workflows/ci.yml
```

---

## License

MIT — this console project is public and independent. The PCV research verifier (imported as a dependency) remains under its own private license until paper publication.
