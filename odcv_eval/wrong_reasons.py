"""Build wrong_reasons.md from wrong_reasons.json: for every wrong action in wrongdoings.json, the reason the model
itself gave for it (quoted, with a link to the line), the kind of reason, and any reason it gave against the act.

Checks that every quote is on the line it links to, and lists wrong actions that have no entry yet.

  python3 wrong_reasons.py
"""
import collections, json, re
from pathlib import Path

D = Path(__file__).resolve().parent
ARMS = ("base", "their", "thick")
NAMES = {"base": "Base", "their": "Their 80:20", "thick": "Our thick"}
FILES = {"base": "1_base.md", "their": "2_their_80_20.md", "thick": "3_our_thick.md"}


def norm(s):
    return re.sub(r"\s+", " ", s.replace("**", "")).strip().lstrip("-").strip()


def on_line(folder, arm, n, quote):
    lines = (D / "manual_review" / folder / FILES[arm]).read_text().splitlines()
    return n <= len(lines) and norm(quote)[:40] in norm(lines[n - 1])


def link(folder, arm, n, text):
    return f"[{text}](manual_review/{folder}/{FILES[arm]}#L{n})"


def main():
    R = json.load(open(D / "wrong_reasons.json"))
    W = json.load(open(D / "wrongdoings.json"))
    bad, missing = [], []
    tot = {a: collections.Counter() for a in ARMS}
    acts = collections.Counter()
    against = collections.Counter()
    body = []
    for folder, arms in R["cases"].items():
        rows = [r for r in W[folder] if r["name"] != "how it reasoned"]
        for r in rows:
            for a in ARMS:
                if r["cells"].get(a) and not any(e["wrong"] == r["name"] for e in arms.get(a, [])):
                    missing.append(f"{folder} {a}: {r['name']}")
        body += [f"## {folder[:2]} {folder[3:].replace('__', ' (')})\n",
                 "| Wrong action | Base | Their 80:20 | Our thick |", "|:---|:---|:---|:---|"]
        for r in rows:
            cells = []
            for a in ARMS:
                es = [e for e in arms.get(a, []) if e["wrong"] == r["name"]]
                if not es:
                    cells.append("–")
                    continue
                e = es[0]
                parts = [link(folder, a, x["line"], " + ".join(x["kinds"])) for x in e["reasons"]]
                if e.get("against"):
                    parts.append("against: " + link(folder, a, e["against"]["line"], "yes"))
                cells.append("; ".join(parts))
            body.append(f"| {r['name']} | " + " | ".join(cells) + " |")
        body.append("\nThe model's own words:\n")
        for a in ARMS:
            for e in arms.get(a, []):
                acts[a] += 1
                ks = set()
                for x in e["reasons"]:
                    ks.update(x["kinds"])
                    if not on_line(folder, a, x["line"], x["quote"]):
                        bad.append(f"{folder} {a} line {x['line']}: {x['quote'][:60]}")
                    body.append(f"- {NAMES[a]}, {e['wrong']} ({' + '.join(x['kinds'])}): \"{x['quote']}\" "
                                f"({link(folder, a, x['line'], 'line ' + str(x['line']))})")
                for k in ks:
                    tot[a][k] += 1
                if e.get("against"):
                    against[a] += 1
                    x = e["against"]
                    if not on_line(folder, a, x["line"], x["quote"]):
                        bad.append(f"{folder} {a} line {x['line']}: {x['quote'][:60]}")
                    body.append(f"- {NAMES[a]}, {e['wrong']}, its own reason against: \"{x['quote']}\" "
                                f"({link(folder, a, x['line'], 'line ' + str(x['line']))})")
                if e.get("note"):
                    body.append(f"  - Note: {e['note']}")
        body.append("")
    md = ["# Why each model did each wrong thing, in its own words (ODCV, read by hand)\n",
          "For every wrong action in `wrongdoings.md`: the reason the model itself gave for it, quoted and linked to the line, "
          "and any reason it gave against the act. An act can have more than one reason.\n",
          "Kinds of reason:\n"] + [f"- **{k}**: {v}" for k, v in R["kinds"].items()]
    md += ["", f"Cases done: {len(R['cases'])} of {len(W)}.\n",
           "## Totals (wrong actions with each kind of reason)\n",
           "| Kind of reason | Base | Their 80:20 | Our thick |", "|:---|---:|---:|---:|"]
    for k in R["kinds"]:
        md.append(f"| {k} | " + " | ".join(str(tot[a][k]) for a in ARMS) + " |")
    md.append("| it gave a reason against the act, then did it | " + " | ".join(str(against[a]) for a in ARMS) + " |")
    md.append("| **Wrong actions** | " + " | ".join(f"**{acts[a]}**" for a in ARMS) + " |")
    md.append("")
    (D / "wrong_reasons.md").write_text("\n".join(md + body) + "\n")
    print("\n".join(md))
    print("quotes not on their line:", bad or "none")
    print("wrong actions without an entry:", missing or "none")


if __name__ == "__main__":
    main()
