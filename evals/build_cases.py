"""Build evals/cases.jsonl.

Standard cases: the 152 messages generated for the sample day in
https://github.com/bikramlaishram/parcel-pickup-optimizer (data/day.json), with ground truth
taken straight from the generator's request records.
Hard cases: hand-written and hand-labelled, in evals/hard_cases.jsonl.

Usage: python evals/build_cases.py /path/to/parcel-pickup-optimizer/data/day.json
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vendored.rule_parser import compose, hhmm

HERE = os.path.dirname(os.path.abspath(__file__))
day = json.load(open(sys.argv[1]))
rnd = random.Random(1)
rows = []
for r in day["requests"]:
    rows.append({"id": f"std-{r['id']}", "kind": "standard", "tags": ["generated"], "message": compose(r, rnd),
                 "expected": {"needs_human_check": False, "requests": [{
                     "customer": [r["customer"]], "lat": r["lat"], "lon": r["lon"], "parcels": r["parcels"],
                     "tw_start": hhmm(r["tw_start"]), "tw_end": hhmm(r["tw_end"]), "priority": r["priority"]}]}})
hard = [json.loads(l) for l in open(os.path.join(HERE, "hard_cases.jsonl")) if l.strip()]
with open(os.path.join(HERE, "cases.jsonl"), "w") as f:
    for row in rows + hard:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
print(len(rows), "standard +", len(hard), "hard")
