# Vendored from https://github.com/bikramlaishram/parcel-pickup-optimizer (src/intake.py), MIT License, (c) 2026 Bikram Laishram.
# compose() generates the synthetic messages; parse() is the rule-based baseline.
"""Request intake: turn free-text customer messages into structured pickup requests.

The demo uses a deterministic parser so results are reproducible. In production this
step would be an LLM extraction call with a strict JSON schema, with this parser kept
as a validation and fallback layer.
"""
import re, random

TEMPLATES = [
    "Hello! Please pick up {n} parcels from {c} today between {a} and {b}.{x}",
    "Need a courier at {c}: {n} boxes ready from {a}, must be collected by {b}.{x}",
    "Pickup request - {c}, {n} pcs, window {a}-{b}.{x}",
    "Hi team, {c} here. {n} parcels for pickup, any time {a} to {b} works.{x}",
]
EXPRESS = [" Express please.", " Urgent, same-day express.", " This one is express."]

def hhmm(m): return f"{m // 60:02d}:{m % 60:02d}"

def compose(req, rnd):
    msg = rnd.choice(TEMPLATES).format(n=req["parcels"], c=req["customer"], a=hhmm(req["tw_start"]),
                                       b=hhmm(req["tw_end"]), x=rnd.choice(EXPRESS) if req["priority"] == "express" else "")
    return msg + f" [location pin {req['lat']:.5f}, {req['lon']:.5f}]"

def parse(msg):
    n = int(re.search(r"(\d+)\s*(?:parcels|boxes|pcs)", msg).group(1))
    times = re.findall(r"\b(\d{2}):(\d{2})\b", msg)
    (h1, m1), (h2, m2) = times[0], times[1]
    cust = re.search(r"((?:[A-Z][\w-]*\s)+(?:[a-z]+\s)?#\d{3})", msg).group(1)
    lat, lon = map(float, re.search(r"pin\s*([\d.]+),\s*([\d.]+)", msg).groups())
    return {"customer": cust.strip(), "parcels": n, "tw_start": int(h1) * 60 + int(m1),
            "tw_end": int(h2) * 60 + int(m2),
            "priority": "express" if re.search(r"express|urgent", msg, re.I) else "standard",
            "lat": lat, "lon": lon}
