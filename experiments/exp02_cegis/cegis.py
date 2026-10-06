"""CEGIS v2: persistent-bank counterexample-guided synthesis.

Nothing is ever re-enumerated: banked programs extend signatures with one
ev-call per new example. Cost unit = ev-calls (every program-on-input eval).
Blind baseline (exp01) is reported in the same unit as tested*8 (upper
bound; exceptions abort blind sigs early). Wall-time ratio also reported.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp01_enumeration"))
from synth import CegisEnum, BudgetOut, render  # noqa: E402


def first_failure(prog_src, task):
    fn_src = f"def f({', '.join(task['args'])}):\n    return {prog_src}\n"
    try:
        ns = {}
        exec(compile(fn_src, "<cegis>", "exec"), ns)
        f = ns["f"]
    except Exception as e:
        return ("compile", f"{type(e).__name__}")
    for ins, want in task["io"]:
        try:
            got = f(*ins)
        except Exception as e:
            return ((ins, want), f"raised {type(e).__name__}")
        if isinstance(want, bool):
            if not isinstance(got, bool) or got != want:
                return ((ins, want), f"got {got!r}")
        elif got != want:
            return ((ins, want), f"got {got!r}")
    return None


def cegis(task, max_rounds=10, per_round=100000, max_size=9, seed_n=4):
    en = CegisEnum(task["args"])
    en.add_examples(task["io"][:seed_n])
    t0, rounds, trace = time.perf_counter(), 0, []
    while rounds < max_rounds:
        rounds += 1
        cand = en.current_hit()
        if cand is None:
            try:
                cand = en.generate_until_hit(max_size, en.evcalls + per_round)
            except BudgetOut:
                cand = None
            if cand is None:
                return {"prog": None, "rounds": rounds, "evcalls": en.evcalls,
                        "secs": round(time.perf_counter() - t0, 2), "trace": trace}
        fail = first_failure(render(cand), task)
        trace.append({"round": rounds, "prog": render(cand),
                      "evcalls": en.evcalls, "fail": str(fail[0]) if fail else None})
        if fail is None:
            return {"prog": render(cand), "rounds": rounds, "evcalls": en.evcalls,
                    "secs": round(time.perf_counter() - t0, 2), "trace": trace}
        if fail[0] == "compile":
            return {"prog": None, "rounds": rounds, "evcalls": en.evcalls,
                    "secs": round(time.perf_counter() - t0, 2), "trace": trace}
        if fail[0] not in task["io"]:
            return {"prog": None, "rounds": rounds, "evcalls": en.evcalls,
                    "secs": round(time.perf_counter() - t0, 2), "trace": trace}
        en.add_examples([fail[0]])
    return {"prog": None, "rounds": rounds, "evcalls": en.evcalls,
            "secs": round(time.perf_counter() - t0, 2), "trace": trace}
