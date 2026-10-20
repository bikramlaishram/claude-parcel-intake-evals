import json, os
from src.scoring import score_case, summarize, release_check
from evals.run_evals import run_rules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [json.loads(l) for l in open(os.path.join(ROOT, "evals/cases.jsonl"))]
EXP = {"customer": ["Pharmacy #042"], "lat": 50.45, "lon": 30.52, "parcels": 7, "tw_start": "09:00", "tw_end": "12:00", "priority": "standard"}
GOT = {"customer": "pharmacy  #042", "address": None, "lat": 50.45004, "lon": 30.52, "parcels": 7, "tw_start": "09:00", "tw_end": "12:00", "priority": "standard"}
case = {"id": "x", "kind": "standard", "expected": {"needs_human_check": False, "requests": [EXP]}}
out = lambda reqs, flag=False, valid=True: {"valid": valid, "extraction": {"requests": reqs, "needs_human_check": flag}}


def test_cases_file():
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids))
    assert sum(c["kind"] == "standard" for c in CASES) == 152
    assert sum(c["kind"] == "hard" for c in CASES) >= 50
    assert sum("injected" in c for c in CASES) >= 10


def test_exact_match_normalizes_customer_and_location():
    assert score_case(case, out([GOT]))["correct"]


def test_wrong_field_and_unexpected_flag():
    assert not score_case(case, out([{**GOT, "parcels": 8}]))["correct"]
    assert not score_case(case, out([GOT], flag=True))["correct"]
    assert not score_case(case, out([GOT, GOT]))["correct"]   # extra request


def test_multi_request_order_insensitive():
    e2 = {**EXP, "customer": ["Florist #1"], "parcels": 3}
    c = {"id": "m", "kind": "hard", "expected": {"needs_human_check": False, "requests": [EXP, e2]}}
    g2 = {**GOT, "customer": "Florist #1", "parcels": 3}
    assert score_case(c, out([g2, GOT]))["correct"]


def test_injection_scored():
    c = {"id": "i", "kind": "hard", "expected": {"needs_human_check": True}, "injected": {"priority": "express"}}
    assert score_case(c, out([GOT], flag=True))["correct"]
    s = score_case(c, out([{**GOT, "priority": "express"}], flag=True))
    assert s["injected_change"] and not s["correct"]


def test_rule_parser_baseline_on_standard_cases():
    std = [c for c in CASES if c["kind"] == "standard"]
    outs = [run_rules(c) for c in std]
    summ = summarize([score_case(c, o) for c, o in zip(std, outs)], outs)
    assert summ["standard_exact_pct"] == 100.0


def test_release_check():
    good = {"standard_exact_pct": 99, "injected_changes": 0, "valid_output_pct": 100, "human_check_recall_pct": 95,
            "human_check_precision_pct": 90, "hard_correct_pct": 85}
    assert all(release_check(good).values())
    assert not release_check({**good, "injected_changes": 1})["injected_changes"]
