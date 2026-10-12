"""List every action a model took in one ODCV cell, with the reasoning written in the same turn, for labelling
the kind of reason behind each action by hand (see normative_actions.json).

An action is one assistant turn: a tool call (bash or task_complete), or a message with no tool call (which
the harness answers with its automatic "continue" message). The reasoning is everything the model wrote in that
turn before the call.

  python3 actions.py 04_Ai-Healthcare-Administrator__mandated [base|their|thick] [--chars N]
"""
import ast, json, re, sys
from pathlib import Path

D = Path(__file__).resolve().parent / "manual_review"
FILES = {"base": "1_base.md", "their": "2_their_80_20.md", "thick": "3_our_thick.md"}


def actions(folder, arm):
    t = (D / folder / FILES[arm]).read_text()
    out = []
    for blk in re.split(r"\n---\n", t):
        m = re.match(r"\s*## Step (\d+) · assistant\n", blk)
        if not m:
            continue
        body = blk[m.end():]
        calls = re.findall(r"\*\*(bash|task_complete|[\w ()]+):\*\*\n```\w*\n(.*?)```", body, re.S)
        if not calls:
            calls = [("message", body.strip()[-300:])]
        reason = re.split(r"\n\*\*(?:bash|task_complete|call \(raw\)|[\w ]+):\*\*\n```", body)[0].strip()
        out.append({"step": int(m.group(1)), "reason": reason,
                    "calls": [(n, c.strip()) for n, c in calls]})
    return out


if __name__ == "__main__":
    folder, arm = sys.argv[1], sys.argv[2]
    n = int(sys.argv[sys.argv.index("--chars") + 1]) if "--chars" in sys.argv else 1200
    for a in actions(folder, arm):
        print(f"[{a['step']}] REASON: {a['reason'][:n]}")
        for name, c in a["calls"]:
            print(f"      {name}: {c[:160].replace(chr(10), ' ')}")
        print()
