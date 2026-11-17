"""Ablation: workflow without the MockLLM draft call. Same steps, same host gate.

    python -m lab8.benchmark --shapes workflow,workflow_nodraft --extra-shape workflow_nodraft=bonus.ablation_workflow_nodraft:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/bonus_ablation_nodraft.json
"""

from __future__ import annotations

from lab8.db import connect
from lab8.schemas import RunResult
from lab8.shapes.workflow import _run

SHAPE = "workflow_nodraft"


def run_claim(claim_id: str, *, seed: int, store_path: str, crash_at: str | None = None) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at, shape=SHAPE, draft=False)
    finally:
        conn.close()
