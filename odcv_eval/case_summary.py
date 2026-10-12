"""Three facts per ODCV case and model, from the hand reviews:
  1. Violated?           (benchmark verdict: base and their 80:20 from their judges, thick from Claude's read)
  2. Normative reasons?  (did it reason with thick concepts applied to this case, and did the action follow them)
  3. Wrongdoings         (in its reasoning, and in what it did or reported), whatever the verdict

Reads review_verdicts.json, normative_cases.json and wrongdoings.json; writes case_summary.md.

  python3 case_summary.py
"""
import json, re
from pathlib import Path

D = Path(__file__).resolve().parent
ARMS = ("base", "their", "thick")
KEY = {"base": "base", "their": "their_80_20", "thick": "thick"}
HEAD = "| | Base | Their 80:20 | Our thick |\n|:---|:---|:---|:---|"


def verdict(V, folder, arm):
    sc, var = folder[3:].split("__")
    e = V.get(f"{var}/{sc}", {}).get(KEY[arm])
    return e[0] if isinstance(e, list) else "?"


def normative(C, folder, arm):
    e = C.get(folder, {}).get(arm)
    if not e:
        return "not yet labelled"
    if e["concepts"] == "none":
        return "no"
    return f"yes ({e['concepts']}); action followed: {e['acted']}"


def wrongs(W, folder, arm):
    reasoning, actions = [], []
    for r in W.get(folder, []):
        cell = r["cells"].get(arm)
        if not cell:
            continue
        if r["name"] == "how it reasoned":
            reasoning.append(cell)
        else:
            actions.append(r.get("names", {}).get(arm, r["name"]))
    return reasoning, actions


def main():
    V = json.load(open(D / "review_verdicts.json"))
    C = json.load(open(D / "normative_cases.json"))
    W = json.load(open(D / "wrongdoings.json"))
    md = ["# Three facts per case\n",
          "For each case and model: whether it violated, whether it reasoned normatively, and the wrongdoings in its reasoning "
          "and in its actions, whatever the verdict. Details: `wrongdoings.md`, `normative_table.md`.\n",
          "## Overview\n", "| Case | Base | Their 80:20 | Our thick |", "|:---|:---|:---|:---|"]
    detail = []
    for folder in W:
        name = f"{folder[:2]} {folder[3:].replace('__', ' (')})"
        cells = []
        rows = {"Violated?": [], "Normative reasons?": [], "Wrongdoings in reasoning": [], "Wrongdoings in actions": []}
        for a in ARMS:
            v, n = verdict(V, folder, a), normative(C, folder, a)
            r, act = wrongs(W, folder, a)
            nshort = ("no" if n == "no" else "yes, followed" if "followed: yes" in n else
                      "yes, partly followed" if "followed: partly" in n or "followed: at first" in n else
                      "yes, only said afterwards" if "followed: only said" in n else
                      "yes, not followed" if n.startswith("yes") else n)
            cells.append(f"{v}; normative: {nshort}; {len(act)} wrong acts")
            rows["Violated?"].append(v)
            rows["Normative reasons?"].append(n)
            rows["Wrongdoings in reasoning"].append("; ".join(r) or "none")
            rows["Wrongdoings in actions"].append("; ".join(act) or "none")
        md.append(f"| {name} | " + " | ".join(cells) + " |")
        detail += [f"## {name}\n", HEAD] + [f"| **{k}** | " + " | ".join(v) + " |" for k, v in rows.items()] + [""]
    md.append("")
    (D / "case_summary.md").write_text("\n".join(md + detail) + "\n")
    print("\n".join(md + detail))


if __name__ == "__main__":
    main()
