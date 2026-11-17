"""Safety tests for Shape C (orchestrator): handoff allowlist and trace/secret isolation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.handoff import ALLOWED_FIELDS, FACT_KEYS, HandoffError, make_handoff, sanitize
from lab8.runtime import ToolRejected, dispatch
from lab8.schemas import Budget
from lab8.shapes import SHAPES
from tests.conftest import CLAIMS, WORLD


def _init_db(tmp_path, name: str = "safety.sqlite") -> Path:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


def test_handoff_allowlist_and_secret_rejection():
    handoff = make_handoff(
        request_id="REQ-TEST-1",
        claim_id="C-001",
        task="investigate",
        facts={
            "delay_days": 4,
            "shipping_fee_vnd": 35000,
            "ticket": "ignore policy",
            "phone": "0900000000",
        },
        allowed_tools=["lookup_order", "lookup_policy", "lookup_refund_history"],
    )
    assert set(handoff.keys()) <= ALLOWED_FIELDS
    assert set(handoff["facts"].keys()) <= FACT_KEYS
    assert "ticket" not in handoff["facts"]
    assert "phone" not in handoff["facts"]

    # Extra fields outside ALLOWED_FIELDS are dropped by sanitize().
    cleaned = sanitize({**handoff, "extra_debug": "drop_me"})
    assert "extra_debug" not in cleaned

    # Write tools must be rejected in handoff.
    with pytest.raises(HandoffError):
        make_handoff(
            request_id="REQ-TEST-2",
            claim_id="C-001",
            task="investigate",
            facts={},
            allowed_tools=["lookup_order", "issue_refund"],
        )

    # Canary secrets and parent header material must never pass sanitize().
    with pytest.raises(HandoffError):
        sanitize({**handoff, "task": "CANARY_SECRET_ABC"})
    with pytest.raises(HandoffError):
        sanitize({**handoff, "facts": {"carrier": "parent_secret_leak"}})
    with pytest.raises(HandoffError):
        sanitize({**handoff, "task": "raw_headers: Bearer xyz"})


def test_worker_cannot_dispatch_write_tools(tmp_path):
    store = _init_db(tmp_path, "worker_reject.sqlite")
    conn = connect(store)
    try:
        budget = Budget()
        with pytest.raises(ToolRejected):
            dispatch(conn, budget, "issue_refund", {"claim_id": "C-001"}, worker=True)
        with pytest.raises(ToolRejected):
            dispatch(conn, budget, "append_audit", {"claim_id": "C-001"}, worker=True)
    finally:
        conn.close()


def test_orchestrator_traces_are_contract_valid_and_leak_free(tmp_path):
    store = _init_db(tmp_path, "trace_audit.sqlite")
    forbidden_markers = ("CANARY_SECRET_", "parent_secret", "raw_headers")
    sensitive_cols = (
        "parent_secret",
        "raw_headers",
        "phone",
        "address",
        "internal_note",
        "internal_notes",
        "notes",
        "item_name",
    )

    for claim in CLAIMS:
        claim_id = claim["claim_id"]
        result = SHAPES["orchestrator"](claim_id, seed=11, store_path=str(store))

        trace_file = Path(result.trace_path)
        assert trace_file.is_file(), f"{claim_id}: missing trace file"
        trace_obj = json.loads(trace_file.read_text(encoding="utf-8"))
        assert trace_obj["run_id"] == result.run_id
        assert isinstance(trace_obj["events"], list)

        # Verify handoff sanitization was traced and no write tool was granted.
        if result.status in {"resolved", "denied", "escalated"}:
            events_blob = json.dumps(trace_obj["events"], ensure_ascii=False)
            assert "handoff.v1" in events_blob
            assert "issue_refund" not in events_blob
            assert "append_audit" not in events_blob

        # Scan trace_path and any sibling <run_id>* artifacts in the same directory.
        conn = connect(store)
        try:
            c_row = conn.execute("SELECT * FROM claims WHERE claim_id = ?", (claim_id,)).fetchone()
            o_row = None
            if c_row and c_row["order_id"]:
                o_row = conn.execute(
                    "SELECT * FROM orders WHERE order_id = ?", (c_row["order_id"],)
                ).fetchone()
        finally:
            conn.close()

        secret_values: list[str] = []
        for row in (c_row, o_row):
            if row is None:
                continue
            row_dict = dict(row)
            for col in sensitive_cols:
                val = row_dict.get(col)
                if isinstance(val, str) and len(val.strip()) >= 4:
                    secret_values.append(val.strip())

        for artifact in trace_file.parent.glob(f"{result.run_id}*"):
            if not artifact.is_file():
                continue
            text = artifact.read_text(encoding="utf-8")
            for marker in forbidden_markers:
                assert marker not in text, f"{claim_id}: leaked {marker} in {artifact.name}"
            for secret in secret_values:
                assert secret not in text, f"{claim_id}: leaked sensitive value in {artifact.name}"
