"""Violation rates on the 77 shared ODCV cases, and exact McNemar tests between models.

Two standards:
  - our rule:        independent_verdicts.json (one fixed rule, applied to all three models)
  - judges' standard: review_verdicts.json (base and their 80:20 as scored by the replication's two judges,
                      median >= 3; our thick read by hand against the same standard)

  python3 rates.py
"""
import json
from math import comb
from pathlib import Path

D = Path(__file__).resolve().parent
CASES = list(json.load(open(D / "wrongdoings.json")))          # the 77 shared cases
ARMS = ("base", "their", "thick")
NAMES = {"base": "Base", "their": "Their 80:20", "thick": "Our thick"}


def our_rule():
    V = json.load(open(D / "independent_verdicts.json"))["verdicts"]
    return {f: {a: V[f][a] == "violated" for a in ARMS} for f in CASES}


def judges_standard():
    V = json.load(open(D / "review_verdicts.json"))
    key = {"base": "base", "their": "their_80_20", "thick": "thick"}
    out = {}
    for f in CASES:
        sc, var = f[3:].split("__")
        e = V[f"{var}/{sc}"]
        out[f] = {a: e[key[a]][0] == "violated" for a in ARMS}
    return out


def mcnemar(x, y):
    """Exact two-sided McNemar p for discordant counts x (only first violated) and y (only second)."""
    n, k = x + y, min(x, y)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0


for title, V in (("Our rule", our_rule()), ("Judges' standard", judges_standard())):
    print(f"\n{title} (n = {len(CASES)})")
    for a in ARMS:
        k = sum(V[f][a] for f in CASES)
        print(f"  {NAMES[a]:12s} {k:2d} / {len(CASES)} = {100 * k / len(CASES):.1f}%")
    for a, b in (("their", "thick"), ("base", "thick"), ("base", "their")):
        x = sum(V[f][a] and not V[f][b] for f in CASES)
        y = sum(V[f][b] and not V[f][a] for f in CASES)
        print(f"  {NAMES[a]} vs {NAMES[b]}: only {NAMES[a]} violated {x}, only {NAMES[b]} violated {y}, "
              f"exact McNemar p = {mcnemar(x, y):.3g}")
