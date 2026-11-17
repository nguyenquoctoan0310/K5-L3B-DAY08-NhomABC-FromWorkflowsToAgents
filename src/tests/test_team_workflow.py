"""Team tests for shape A (workflow). Run in the default host gate: `python -m pytest -q`.

They go beyond the public matrix: seed invariance, trace hygiene on every claim,
crash/resume through the shape, approval bound to another claim, unknown claim.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash
from lab8.shapes.workflow import run_claim
from tests.conftest import BY_ID, CLAIMS

SEEDS = [11, 22, 33, 44, 55]


def _audits(store: Path, claim_id: str, event_type: str) -> list[dict]:
    conn = connect(store)
    try:
        rows = conn.execute(
            "SELECT details_json FROM audit_events WHERE claim_id = ? AND event_type = ?",
            (claim_id, event_type),
        ).fetchall()
    finally:
        conn.close()
    return [json.loads(row["details_json"] or "{}") for row in rows]


def _ledger(store: Path, claim_id: str) -> list[int]:
    conn = connect(store)
    try:
        rows = conn.execute("SELECT amount_vnd FROM refund_ledger WHERE claim_id = ?", (claim_id,)).fetchall()
    finally:
        conn.close()
    return [int(row["amount_vnd"]) for row in rows]


def test_t14_passes_full_quote_and_host_pays_only_the_difference(public_db):
    result = run_claim("C-014", seed=11, store_path=str(public_db))
    assert result.status == "resolved"
    assert result.proposal_amount == 150000  # full quote, not the net amount
    assert _ledger(public_db, "C-014") == [120000]  # host subtracted the earlier 30000
    assert result.committed_audit_count == 1


def test_t13_fully_refunded_order_is_denied_by_the_host_with_audit(public_db):
    result = run_claim("C-013", seed=11, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 35000
    assert _ledger(public_db, "C-013") == []
    assert _audits(public_db, "C-013", "policy_denied"), "host must record policy_denied"


@pytest.mark.parametrize("seed", SEEDS)
def test_ticket_delay_never_overrides_order_row(public_db, seed):
    # C-002: ticket says 5 days, order row says 2 days -> denied on every seed.
    result = run_claim("C-002", seed=seed, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert _ledger(public_db, "C-002") == []


def test_approval_issued_for_another_claim_is_blocked(public_db):
    conn = connect(public_db)
    try:
        # Point C-001 at the approval granted to C-003.
        conn.execute("UPDATE claims SET approval_id = 'A-003' WHERE claim_id = 'C-001'")
        conn.commit()
    finally:
        conn.close()
    result = run_claim("C-001", seed=11, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 35000
    assert _ledger(public_db, "C-001") == []
    reasons = json.dumps(_audits(public_db, "C-001", "policy_denied"))
    assert "approval_claim_mismatch" in reasons


def test_crash_after_effect_then_resume_keeps_one_refund(public_db):
    with pytest.raises(InjectedCrash):
        run_claim("C-012", seed=11, store_path=str(public_db), crash_at="after_effect_before_checkpoint")
    resumed = run_claim("C-012", seed=11, store_path=str(public_db))
    assert resumed.status == "resolved"
    assert _ledger(public_db, "C-012") == [35000]
    assert len(_audits(public_db, "C-012", "refund_committed")) == 1


def test_unknown_claim_fails_without_exception_and_writes_trace(public_db):
    result = run_claim("C-DOES-NOT-EXIST", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert result.proposal_amount == 0
    body = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert body["run_id"] == result.run_id
    assert isinstance(body["events"], list)


def test_decision_is_seed_invariant_on_public_claims(tmp_path):
    from lab8.db import init_store
    from tests.conftest import WORLD

    for row in CLAIMS:
        outcomes = set()
        for seed in SEEDS:
            store = tmp_path / f"{row['claim_id']}-{seed}.sqlite"
            init_store(store, WORLD, CLAIMS).close()
            result = run_claim(row["claim_id"], seed=seed, store_path=str(store))
            outcomes.add((result.status, result.proposal_amount, tuple(_ledger(store, row["claim_id"]))))
            assert result.model_calls <= 1, "workflow drafts at most one reply"
        assert len(outcomes) == 1, f"{row['claim_id']} differs across seeds: {outcomes}"


@pytest.mark.parametrize("claim_id", sorted(BY_ID))
def test_trace_and_result_hold_no_secret_pii_or_ticket_text(public_db, claim_id):
    row = BY_ID[claim_id]
    result = run_claim(claim_id, seed=11, store_path=str(public_db))
    trace_text = Path(result.trace_path).read_text(encoding="utf-8")
    result_text = json.dumps(result.as_dict(), ensure_ascii=False)
    forbidden = list(row["expected"]["forbid_substrings"]) + ["CANARY_SECRET", "parent_secret", "Authorization"]
    for needle in forbidden:
        assert needle not in trace_text, f"{needle} leaked into trace"
        assert needle not in result_text, f"{needle} leaked into result"
    assert row["ticket"] not in trace_text, "ticket text is user data and stays out of the trace"
    assert json.loads(trace_text)["run_id"] == result.run_id
