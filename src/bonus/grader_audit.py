"""B7 — metamorphic audit of the three candidate `summarize` graders.

Run from `src/`:

    python -m bonus.grader_audit --out reports/bonus_grader_audit.json

Each relation compares `summarize(a)` with `summarize(b)` for a transformed input
`b`. No relation needs the "true" pass rate or cost; it only needs to know how the
output must move when the input moves. The grader files under `grader_audit/` and
`lab8/metrics.py` are read, never modified.

Relations:
  R1 delay_days_2_vs_3   business decision flips at the 3-day threshold (lab8.compensation.quote)
  R2 infra_invariance    adding infra_error trials keeps every graded metric
  R3 duplicate_scaling   duplicating the list keeps rates/means, doubles totals
  R4 permutation         (team, new) reordering trials keeps every output
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import random
from pathlib import Path
from typing import Any, Callable

from lab8.compensation import quote

SRC = Path(__file__).resolve().parents[1]
FIXTURES = SRC / "grader_audit" / "fixtures"
GRADERS = ("grader_a", "grader_b", "grader_c")
TOL = 1e-9

# Keys from lab8.metrics.summarize, grouped by how they must react.
RATE_KEYS = (
    "pass_rate",
    "pass_5",
    "seed_variance",
    "seed_min",
    "seed_max",
    "cost_per_success_vnd",
    "mean_steps",
    "p95_steps",
    "mean_model_calls",
    "mean_tool_calls",
)
TOTAL_KEYS = ("trials", "graded_trials", "successes", "total_simulated_cost_vnd")
# Graded metrics that infra trials must not move. `trials` counts every row, so it may grow.
INFRA_KEYS = RATE_KEYS + ("graded_trials", "successes", "total_simulated_cost_vnd", "seed_pass_rates")


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def load_grader(name: str) -> Callable[[list[dict[str, Any]]], dict[str, Any]]:
    return importlib.import_module(f"grader_audit.{name}").summarize


def _close(x: Any, y: Any) -> bool:
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        return abs(float(x) - float(y)) <= TOL * max(1.0, abs(float(x)), abs(float(y)))
    return x == y


def _diff(key: str, expected: Any, got: Any) -> dict[str, Any]:
    return {"key": key, "expected": expected, "got": got}


def check_infra(summarize: Callable, fixture: dict[str, Any]) -> list[dict[str, Any]]:
    """R2: b = a + infra_error trials. Graded metrics must not change."""
    ra, rb = summarize(fixture["a"]), summarize(fixture["b"])
    out = []
    for shape, sa in ra.items():
        sb = rb.get(shape, {})
        for key in INFRA_KEYS:
            if not _close(sa.get(key), sb.get(key)):
                out.append(_diff(f"{shape}.{key}", sa.get(key), sb.get(key)))
    return out


def check_duplicate(summarize: Callable, fixture: dict[str, Any]) -> list[dict[str, Any]]:
    """R3: b = a + a. Rates and means unchanged, totals doubled."""
    ra, rb = summarize(fixture["a"]), summarize(fixture["b"])
    out = []
    for shape, sa in ra.items():
        sb = rb.get(shape, {})
        for key in RATE_KEYS:
            if not _close(sa.get(key), sb.get(key)):
                out.append(_diff(f"{shape}.{key}", sa.get(key), sb.get(key)))
        if sa.get("seed_pass_rates") != sb.get("seed_pass_rates"):
            out.append(_diff(f"{shape}.seed_pass_rates", sa.get("seed_pass_rates"), sb.get("seed_pass_rates")))
        for key in TOTAL_KEYS:
            want = 2 * sa[key] if sa.get(key) is not None else None
            if not _close(want, sb.get(key)):
                out.append(_diff(f"{shape}.{key}", want, sb.get(key)))
    return out


def permuted(trials: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    rows = [dict(t) for t in trials]
    random.Random(seed).shuffle(rows)
    return rows


def check_permutation(
    summarize: Callable, trials: list[dict[str, Any]], seeds: tuple[int, ...] = (0, 1, 2, 3, 4)
) -> list[dict[str, Any]]:
    """R4 (new): a trial list is a multiset. Any reorder must give the same report."""
    base = summarize(trials)
    orders = [list(reversed(trials))] + [permuted(trials, s) for s in seeds]
    out = []
    for idx, rows in enumerate(orders):
        other = summarize(rows)
        for shape, sa in base.items():
            for key, value in sa.items():
                if key == "reasons":
                    continue
                if not _close(value, other.get(shape, {}).get(key)):
                    out.append(_diff(f"order{idx}.{shape}.{key}", value, other.get(shape, {}).get(key)))
    return out


def check_delay(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    """R1: 2 days -> no refund, 3 days -> exactly the shipping fee (business_rules.md)."""
    qa = quote(fixture["a"]["order"], fixture["policies"], as_of=fixture["as_of"])
    qb = quote(fixture["b"]["order"], fixture["policies"], as_of=fixture["as_of"])
    fee = int(fixture["b"]["order"]["shipping_fee_vnd"])
    out = []
    if qa.amount_vnd != 0:
        out.append(_diff("a.amount_vnd (delay 2)", 0, qa.amount_vnd))
    if qb.amount_vnd != fee:
        out.append(_diff("b.amount_vnd (delay 3)", fee, qb.amount_vnd))
    if "SHIP-LATE-03" not in qb.clause_ids:
        out.append(_diff("b.clause_ids", ["SHIP-LATE-03"], qb.clause_ids))
    return out


def audit() -> dict[str, Any]:
    infra = load_fixture("metamorphic_infra")
    dup = load_fixture("metamorphic_duplicate")
    delay = load_fixture("metamorphic_claim_delay")
    delay_diffs = check_delay(delay)
    matrix: dict[str, dict[str, Any]] = {}
    for name in GRADERS:
        summarize = load_grader(name)
        rows = {
            "R1_delay_days_2_vs_3": delay_diffs,
            "R2_infra_invariance": check_infra(summarize, infra),
            "R3_duplicate_scaling": check_duplicate(summarize, dup),
            "R4_permutation": check_permutation(summarize, infra["b"]),
        }
        matrix[name] = {
            rel: {"holds": not diffs, "deviations": diffs} for rel, diffs in rows.items()
        }
    fingerprint = hashlib.sha256(
        b"".join((FIXTURES / f"{n}.json").read_bytes() for n in ("metamorphic_claim_delay", "metamorphic_infra", "metamorphic_duplicate"))
    ).hexdigest()[:12]
    return {
        "run_id": f"B7-grader-audit-{fingerprint}",
        "fixtures_sha256_12": fingerprint,
        "relations": ["R1_delay_days_2_vs_3", "R2_infra_invariance", "R3_duplicate_scaling", "R4_permutation"],
        "matrix": matrix,
        "summary": {
            name: {rel: ("holds" if cell["holds"] else f"deviates x{len(cell['deviations'])}") for rel, cell in m.items()}
            for name, m in matrix.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="B7 metamorphic grader audit")
    parser.add_argument("--out", default="reports/bonus_grader_audit.json")
    args = parser.parse_args()
    report = audit()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    width = max(len(r) for r in report["relations"])
    print("relation".ljust(width), *(g.ljust(16) for g in GRADERS))
    for rel in report["relations"]:
        print(rel.ljust(width), *(report["summary"][g][rel].ljust(16) for g in GRADERS))
    print(f"run_id {report['run_id']} -> {out}")


if __name__ == "__main__":
    main()
