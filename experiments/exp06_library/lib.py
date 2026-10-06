"""Library learning v1: solved programs become single-node macros.

Teach tasks build the library; test tasks measure cold-vs-warm. Macros are
whole solutions over x, applied as ("m", name) size-1 leaves (hook lives in
synth.MACROS; empty by default so other rungs are unaffected). v1 does no
anti-unification (named future step); even verbatim reuse should compress
search depth measurably. Distractor macro tests negative control.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp01_enumeration"))
import synth  # noqa: E402
from synth import synthesize  # noqa: E402

TEACH = [
    {"name": "sq", "macro": "SQ", "args": ["x"],
     "io": [((3,), 9), ((0,), 0), ((-4,), 16), ((5,), 25),
            ((6,), 36), ((-1,), 1), ((2,), 4), ((-2,), 4)]},
    {"name": "inc", "macro": "INC", "args": ["x"],
     "io": [((3,), 4), ((0,), 1), ((-4,), -3), ((5,), 6),
            ((10,), 11), ((-1,), 0), ((100,), 101), ((-9,), -8)]},
]

TEST = [
    {"name": "sq_inc", "args": ["x"],
     "io": [((3,), 10), ((0,), 1), ((-4,), 17), ((5,), 26),
            ((2,), 5), ((-1,), 2), ((6,), 37), ((-2,), 5)]},
    {"name": "inc_sq", "args": ["x"],
     "io": [((3,), 16), ((0,), 1), ((-4,), 9), ((5,), 36),
            ((2,), 9), ((-1,), 0), ((6,), 49), ((-2,), 1)]},
]

# x+100: valid program, useless here. If warm ever USES it, retrieval
# discrimination failed (it can't — v1 has no retrieval, only the library).
DISTRACTOR = ("b", "+", ("v", "x"), ("c", 100))


def teach(max_size=9, max_programs=300000):
    lib = {}
    for t in TEACH:
        r = synthesize(t, max_size, max_programs)
        assert "prog" in r, f"teach failed on {t['name']}: {r}"
        lib[t["macro"]] = _to_prog(r["prog"])
    lib["FAR"] = DISTRACTOR
    return lib


def _to_prog(src):
    """Render is one-way; re-derive by re-synthesis is wasteful. Instead the
    teach solutions are KNOWN shapes; map via a tiny parser for our grammar.
    Only shapes teach produces are needed (verified by assert)."""
    import ast as _ast
    tree = _ast.parse(src, mode="eval").body
    return _conv(tree)


def _conv(t):
    import ast as _ast
    if isinstance(t, _ast.Name):
        return ("v", t.id)
    if isinstance(t, _ast.Constant):
        return ("c", t.value)
    if isinstance(t, _ast.UnaryOp) and isinstance(t.op, _ast.USub):
        return ("u", "-", _conv(t.operand))
    if isinstance(t, _ast.UnaryOp) and isinstance(t.op, _ast.Not):
        return ("u", "not", _conv(t.operand))
    if isinstance(t, _ast.BinOp):
        op = { _ast.Add: "+", _ast.Sub: "-", _ast.Mult: "*",
               _ast.FloorDiv: "//", _ast.Mod: "%", _ast.Pow: "**"}[type(t.op)]
        return ("b", op, _conv(t.left), _conv(t.right))
    raise ValueError(f"unparsable { _ast.dump(t)}")
