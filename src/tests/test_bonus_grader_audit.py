"""B7 — metamorphic audit of grader_a / grader_b / grader_c.

    python -m pytest -q tests/test_bonus_grader_audit.py

Every relation runs on all three graders (parametrize). A cell where the team found
a deviation is marked `xfail(strict=True)` with the measured numbers in the reason:
the suite stays green, the finding stays visible in the output, and if a grader is
ever fixed the strict xfail turns red so the table must be updated.
"""

from __future__ import annotations

import json
from collections import defaultdict

import pytest

from bonus.grader_audit import (
    GRADERS,
    audit,
    check_delay,
    check_duplicate,
    check_infra,
    check_permutation,
    load_fixture,
    load_grader,
)
from lab8.metrics import summarize as official_summarize

INFRA = load_fixture("metamorphic_infra")
DUP = load_fixture("metamorphic_duplicate")
DELAY = load_fixture("metamorphic_claim_delay")


def _cell(grader: str, reason: str | None = None):
    if reason is None:
        return pytest.param(grader, id=grader)
    return pytest.param(grader, id=grader, marks=pytest.mark.xfail(strict=True, reason=reason))


PASS5_DUP = "pass_5 0.667 -> 0.0 under duplication: lab8.metrics counts rows per claim, not distinct seeds"


# --- R1: business decision flips at the 3-day threshold ------------------------------


def test_r1_delay_2_vs_3_flips_decision_by_business_rule():
    assert check_delay(DELAY) == []


def test_r1_only_delay_differs_between_the_pair():
    a, b = dict(DELAY["a"]["order"]), dict(DELAY["b"]["order"])
    assert (a.pop("delay_days"), b.pop("delay_days")) == (2, 3)
    assert a == b, "the pair must differ only in delay_days for the relation to mean anything"


# --- R2: infra trials must not count as wrong decisions ------------------------------


@pytest.mark.parametrize(
    "grader",
    [
        _cell("grader_a"),
        _cell("grader_b"),
        _cell("grader_c", "counts infra_error trials as failures: pass_rate 0.75 -> 0.5625 (+4 infra rows in denominator)"),
    ],
)
def test_r2_infra_trials_do_not_move_graded_metrics(grader):
    assert check_infra(load_grader(grader), INFRA) == []


@pytest.mark.parametrize("grader", GRADERS)
def test_r2_pass_rate_only(grader):
    """Narrow form of R2 used in the report table: just pass_rate."""
    ra, rb = load_grader(grader)(INFRA["a"]), load_grader(grader)(INFRA["b"])
    moved = abs(ra["workflow"]["pass_rate"] - rb["workflow"]["pass_rate"]) > 1e-12
    assert moved == (grader == "grader_c")


# --- R3: duplicated list keeps rates, doubles totals ---------------------------------


@pytest.mark.parametrize(
    "grader",
    [
        _cell("grader_a", "double-counts first trial cost per claim: total 473.0 != 2*283.5, cost/success 31.5 -> 26.28; " + PASS5_DUP),
        _cell("grader_b", PASS5_DUP),
        _cell("grader_c", PASS5_DUP),
    ],
)
def test_r3_duplicate_keeps_rates_and_doubles_totals(grader):
    assert check_duplicate(load_grader(grader), DUP) == []


@pytest.mark.parametrize("grader", GRADERS)
def test_r3_without_pass5_isolates_grader_specific_bug(grader):
    """Drop pass_5 (shared with lab8.metrics) to see which grader has its own R3 bug."""
    diffs = [d for d in check_duplicate(load_grader(grader), DUP) if not d["key"].endswith("pass_5")]
    assert bool(diffs) == (grader == "grader_a")


def test_r3_pass5_defect_lives_in_official_metrics():
    ra, rb = official_summarize(DUP["a"]), official_summarize(DUP["b"])
    assert ra["workflow"]["pass_5"] > 0
    assert rb["workflow"]["pass_5"] == 0.0


# --- R4 (team, new): trial order must not matter -------------------------------------


@pytest.mark.parametrize(
    "grader",
    [
        _cell("grader_a", "extra cost uses the FIRST trial seen per claim: reversed order gives total 285.0 vs 283.5"),
        _cell("grader_b"),
        _cell("grader_c"),
    ],
)
def test_r4_permutation_keeps_every_output(grader):
    assert check_permutation(load_grader(grader), INFRA["b"]) == []


def _order_dependent_mutant(trials):
    """Synthetic bug: seed_min reports the rate of whichever seed appears first."""
    report = load_grader("grader_b")(trials)  # correct on R1-R3 except the shared pass_5 defect
    by_seed = defaultdict(list)
    for t in trials:
        if t.get("passed") is not None and not t.get("infra_error"):
            by_seed[t["seed"]].append(bool(t["passed"]))
    first = next(t["seed"] for t in trials if t.get("passed") is not None and not t.get("infra_error"))
    for stats in report.values():
        stats["seed_min"] = sum(by_seed[first]) / len(by_seed[first])
    return report


def test_r4_catches_an_order_bug_that_r2_and_r3_miss():
    # Old relations stay silent on this mutant (ignoring the shared pass_5 defect)...
    assert check_infra(_order_dependent_mutant, INFRA) == []
    assert [d for d in check_duplicate(_order_dependent_mutant, DUP) if not d["key"].endswith("pass_5")] == []
    # ...but reordering exposes it.
    assert check_permutation(_order_dependent_mutant, INFRA["b"]) != []


# --- report is reproducible -----------------------------------------------------------


def test_audit_report_is_deterministic_and_matches_findings():
    first, second = audit(), audit()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    s = first["summary"]
    assert s["grader_b"]["R2_infra_invariance"] == "holds"
    assert s["grader_c"]["R2_infra_invariance"].startswith("deviates")
    assert s["grader_a"]["R4_permutation"].startswith("deviates")
    assert all(s[g]["R1_delay_days_2_vs_3"] == "holds" for g in GRADERS)
