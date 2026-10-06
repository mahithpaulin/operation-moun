"""Three-bank enumerator (int/list/bool) with retrieval seeding."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp01_enumeration"))
from synth import CONSTS  # noqa: E402
from api import ev, render2, retrieve  # noqa: E402

INT_BIN = ["+", "-", "*", "//", "%"]
CMP = ["==", "!=", "<", ">", "<=", ">="]
INT_CONSTS = [c for c in CONSTS if not isinstance(c, bool)]
CALL_L2I = ["sum", "len", "min", "max"]


def synthesize_api(task, seed=True, max_size=9, max_programs=300000):
    envs = [{a: v for a, v in zip(task["args"], ins)} for ins, _ in task["io"]]
    wants = [out for _, out in task["io"]]
    fwants = tuple(("I", w) for w in wants)
    banks = {"I": {}, "L": {}, "B": {}}
    seen = {}
    tested = [0]

    def freeze(v):
        if isinstance(v, list):
            return ("L", tuple(freeze(x) for x in v))
        if isinstance(v, bool):
            return ("B", v)
        return ("I", v)

    def sig(p):
        try:
            return tuple(freeze(ev(p, e)) for e in envs)
        except Exception:
            return None

    def reg(bank_name, size, p):
        """Register prog; returns 'hit' | True (banked) | False (dup/err).

        Hits count only from the int bank (all rung tasks are int-output;
        without this, 1 == True would false-hit bool programs).
        """
        s = sig(p)
        if s is None or s in seen:
            return False
        seen[s] = p
        tested[0] += 1
        if tested[0] >= max_programs:
            raise StopIteration
        banks[bank_name].setdefault(size, []).append(p)
        if bank_name == "I" and s == fwants:
            return "hit"
        return True

    def done(p):
        return {"prog": render2(p), "tested": tested[0]}

    ib, lb, bb = banks["I"], banks["L"], banks["B"]
    try:
        for c in INT_CONSTS:
            if reg("I", 1, ("c", c)) == "hit":
                return done(("c", c))
        if seed:
            for frag in retrieve(task.get("tags", []), "I"):
                if reg("I", 1, frag) == "hit":
                    return done(frag)
        reg("L", 1, ("v", "x"))
        if seed:
            for frag in retrieve(task.get("tags", []), "L"):
                if reg("L", 1, frag) == "hit":
                    return done(frag)
        for c in [True, False]:
            reg("B", 1, ("c", c))

        for s in range(2, max_size + 1):
            if s - 1 in ib:
                for a in list(ib[s - 1]):
                    if reg("I", s, ("u", "-", a)) == "hit":
                        return done(("u", "-", a))
                    if reg("I", s, ("call", "abs", a)) == "hit":
                        return done(("call", "abs", a))
            for l in range(1, s - 1):
                r = s - 1 - l
                if l in ib and r in ib:
                    for op in INT_BIN:
                        for a in list(ib[l]):
                            for b in list(ib[r]):
                                p = ("b", op, a, b)
                                if reg("I", s, p) == "hit":
                                    return done(p)
            if s - 1 in lb:
                for a in list(lb[s - 1]):
                    for op in CALL_L2I:
                        p = ("call", op, a)
                        if reg("I", s, p) == "hit":
                            return done(p)
                    if reg("L", s, ("call", "sorted", a)) == "hit":
                        return done(("call", "sorted", a))
            for l in range(1, s - 1):
                r = s - 1 - l
                if l in lb and r in ib:
                    for a in list(lb[l]):
                        for b in list(ib[r]):
                            p = ("sub", a, b)
                            if reg("I", s, p) == "hit":
                                return done(p)
            for l in range(1, s - 1):
                r = s - 1 - l
                if l in ib and r in ib:
                    for op in CMP:
                        for a in list(ib[l]):
                            for b in list(ib[r]):
                                reg("B", s, ("b", op, a, b))
            for cs in range(1, s - 2):
                for ts in range(1, s - 1 - cs):
                    es = s - 1 - cs - ts
                    if es < 1 or cs not in bb or ts not in ib or es not in ib:
                        continue
                    for c in list(bb[cs]):
                        for t in list(ib[ts]):
                            for e in list(ib[es]):
                                p = ("if", c, t, e)
                                if reg("I", s, p) == "hit":
                                    return done(p)
    except StopIteration:
        pass
    return {"miss": True, "tested": tested[0]}
