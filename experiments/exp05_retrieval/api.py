"""API-grammar synthesis: list/int/bool banks + builtin calls + subscript.

Call nodes: sorted, sum, len, min, max, abs. Subscript L[c] with static guard.
Retrieval seeding: corpus fragments enter as size-1 leaves of the right bank
("stitch"); cold runs omit them. The rung measures warm-vs-cold on the same
grammar — retrieval as quantified search-bias, nothing more.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp01_enumeration"))
from synth import ev as _ev0, render, sz  # noqa: E402

CALLS_1 = ["sorted", "sum", "len", "min", "max", "abs"]


class _Skip(Exception):
    pass


def ev(p, env):
    """Self-recursive evaluator: base nodes + call/sub. (Delegating base
    nodes to synth.ev would break: its recursion can't see call/sub
    children. Duplication is the price of a shared-namespace concat.)"""
    t = p[0]
    if t == "v":
        return env[p[1]]
    if t == "c":
        return p[1]
    if t == "u":
        a = ev(p[2], env)
        return (-a) if p[1] == "-" else (not a)
    if t == "b":
        _, op, l, r = p
        a, b = ev(l, env), ev(r, env)
        if op == "and":
            return a and b
        if op == "or":
            return a or b
        if op == "+":
            v = a + b
        elif op == "-":
            v = a - b
        elif op == "*":
            v = a * b
        elif op in ("//", "%"):
            if b == 0:
                raise _Skip()
            v = (a // b) if op == "//" else (a % b)
        elif op == "**":
            if abs(a) > 10 or abs(b) > 6:
                raise _Skip()
            v = a ** b
        elif op == "==":
            v = a == b
        elif op == "!=":
            v = a != b
        elif op == "<":
            v = a < b
        elif op == ">":
            v = a > b
        elif op == "<=":
            v = a <= b
        elif op == ">=":
            v = a >= b
        else:
            raise _Skip()
        if isinstance(v, (int, float)) and abs(v) > 10 ** 6:
            raise _Skip()
        return v
    if t == "if":
        return ev(p[2], env) if ev(p[1], env) else ev(p[3], env)
    if t == "call":
        a = ev(p[2], env)
        try:
            if p[1] == "sorted":
                v = sorted(a)
            elif p[1] == "sum":
                v = sum(a)
            elif p[1] == "len":
                v = len(a)
            elif p[1] == "min":
                v = min(a)
            elif p[1] == "max":
                v = max(a)
            elif p[1] == "abs":
                v = abs(a)
            else:
                raise _Skip()
        except Exception:
            raise _Skip()
        if isinstance(v, list) and len(v) > 64:
            raise _Skip()
        if isinstance(v, int) and abs(v) > 10 ** 6:
            raise _Skip()
        return v
    if t == "sub":
        a, i = ev(p[1], env), ev(p[2], env)
        if not isinstance(a, list) or not isinstance(i, int):
            raise _Skip()
        if not (-len(a) <= i < len(a)):
            raise _Skip()
        return a[i]
    raise _Skip()


def _sz(p):
    t = p[0]
    if t in ("v", "c"):
        return 1
    if t == "u":
        return 1 + _sz(p[2])
    if t == "call":
        return 1 + _sz(p[2])
    if t == "sub":
        return 1 + _sz(p[1]) + _sz(p[2])
    if t == "b":
        return 1 + _sz(p[2]) + _sz(p[3])
    return 1 + _sz(p[1]) + _sz(p[2]) + _sz(p[3])  # if


def render2(p):
    """Recursive renderer for base + call/sub nodes (base render() would
    misread unknown node types as ifexp)."""
    t = p[0]
    if t == "v":
        return p[1]
    if t == "c":
        return repr(p[1])
    if t == "u":
        return f"({p[1]} {render2(p[2])})"
    if t == "b":
        return f"({render2(p[2])} {p[1]} {render2(p[3])})"
    if t == "if":
        return f"({render2(p[2])} if {render2(p[1])} else {render2(p[3])})"
    if t == "call":
        return f"{p[1]}({render2(p[2])})"
    if t == "sub":
        return f"({render2(p[1])}[{render2(p[2])}])"
    raise ValueError(f"bad node {p!r}")


# Corpus: COMPONENTS only. Exact-solution fragments (first_sorted,
# max_gap) were removed after v1 showed whole-solution retrieval is a
# 58x tautology (retrieve-then-verify = memorize-then-check). The honest
# test is composition: retrieve parts, synthesize the glue.
# list_sum/sum(x) stays as the documented exact-match ceiling case.
_X = ("v", "x")
CORPUS = [
    ("sorted_list", ("call", "sorted", _X), "L", {"sort", "order"}),
    ("list_sum", ("call", "sum", _X), "I", {"sum", "total", "add"}),
    ("list_len", ("call", "len", _X), "I", {"len", "length", "count"}),
    ("list_max", ("call", "max", _X), "I", {"max", "largest"}),
    ("list_min", ("call", "min", _X), "I", {"min", "smallest"}),
    ("first_elem", ("sub", _X, ("c", 0)), "I", {"first", "head"}),
]


def retrieve(task_tags, bank, k=2):
    scored = []
    for name, frag, b, tags in CORPUS:
        if b != bank:
            continue
        scored.append((len(set(task_tags) & tags), name, frag))
    scored.sort(reverse=True)
    return [f for s, _, f in scored[:k] if s > 0] or [f for _, _, f in scored[:1]]
