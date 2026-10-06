"""Typed enumerator: int-bank and bool-bank generated separately.

Restrictions (all principled, documented):
  R1 comparisons take int-bank operands only (no bool chains).
  R2 and/or/not take bool-bank operands only.
  R3 arithmetic takes int-bank operands only (no bool arithmetic).
  R4 ifexp conditions come from the bool bank only.
  R5 root must match task output type (bool task -> bool bank).
Bool consts live in the bool bank; int consts in the int bank.
Untyped solutions using bool-in-arith (e.g. x*(-1**(x<0))) are inexpressible
here, but ifexp forms cover the same tasks (abs = x if x>=0 else -x).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp01_enumeration"))
from synth import ev, render, sz, CONSTS, BINOPS, BOOLOPS, UNOPS, CAP  # noqa: E402

INT_BIN = ["+", "-", "*", "//", "%", "**"]
CMP = ["==", "!=", "<", ">", "<=", ">="]
INT_CONSTS = [c for c in CONSTS if not isinstance(c, bool)]


def synthesize_typed(task, max_size=9, max_programs=300000):
    envs = [{a: v for a, v in zip(task["args"], ins)} for ins, _ in task["io"]]
    wants = [out for _, out in task["io"]]
    want_bool = all(isinstance(w, bool) for w in wants)
    ib, bb = {}, {}      # size -> [distinct progs]
    seen_i, seen_b = {}, {}
    tested = [0]

    def sig(p):
        try:
            return tuple(ev(p, e) for e in envs)
        except Exception:
            return None

    def check(p, want_b):
        s = sig(p)
        if s is None:
            return False, False
        seen = seen_b if want_b else seen_i
        if s in seen:
            return False, False
        seen[s] = p
        tested[0] += 1
        if tested[0] >= max_programs:
            raise StopIteration
        ok = all(w == v and (not isinstance(w, bool) or isinstance(v, bool))
                 for w, v in zip(wants, s))
        return True, ok

    def bank_int(s, prog, is_hit_bank):
        new, hit = check(prog, False)
        if new:
            is_hit_bank.append(prog)
        return hit

    def bank_bool(s, prog, is_hit_bank):
        new, hit = check(prog, True)
        if new:
            is_hit_bank.append(prog)
        return hit

    ib[1], bb[1] = [], []
    try:
        for a in task["args"]:
            if bank_int(1, ("v", a), ib[1]) and not want_bool:
                return {"prog": render(("v", a)), "size": 1, "tested": tested[0]}
        for c in INT_CONSTS:
            if bank_int(1, ("c", c), ib[1]) and not want_bool:
                return {"prog": render(("c", c)), "size": 1, "tested": tested[0]}
        for c in [True, False]:
            if bank_bool(1, ("c", c), bb[1]) and want_bool:
                return {"prog": render(("c", c)), "size": 1, "tested": tested[0]}

        for s in range(2, max_size + 1):
            ni, nb = [], []
            # int: unary -, arith, ifexp(bool,int,int)
            if s - 1 in ib:
                for a in ib[s - 1]:
                    if bank_int(s, ("u", "-", a), ni) and not want_bool:
                        return {"prog": render(("u", "-", a)), "size": s,
                                "tested": tested[0]}
            for l in range(1, s - 1):
                r = s - 1 - l
                if l in ib and r in ib:
                    for op in INT_BIN:
                        for a in ib[l]:
                            for b in ib[r]:
                                p = ("b", op, a, b)
                                if bank_int(s, p, ni) and not want_bool:
                                    return {"prog": render(p), "size": s,
                                            "tested": tested[0]}
            # bool: not, comparisons, and/or, ifexp(bool,bool,bool)
            if s - 1 in bb:
                for a in bb[s - 1]:
                    if bank_bool(s, ("u", "not", a), nb) and want_bool:
                        return {"prog": render(("u", "not", a)), "size": s,
                                "tested": tested[0]}
            for l in range(1, s - 1):
                r = s - 1 - l
                if l in ib and r in ib:
                    for op in CMP:
                        for a in ib[l]:
                            for b in ib[r]:
                                p = ("b", op, a, b)
                                if bank_bool(s, p, nb) and want_bool:
                                    return {"prog": render(p), "size": s,
                                            "tested": tested[0]}
                if l in bb and r in bb:
                    for op in BOOLOPS:
                        for a in bb[l]:
                            for b in bb[r]:
                                p = ("b", op, a, b)
                                if bank_bool(s, p, nb) and want_bool:
                                    return {"prog": render(p), "size": s,
                                            "tested": tested[0]}
            for cs in range(1, s - 2):
                for ts in range(1, s - 1 - cs):
                    es = s - 1 - cs - ts
                    if es < 1 or cs not in bb:
                        continue
                    if ts in ib and es in ib:
                        for c in bb[cs]:
                            for t in ib[ts]:
                                for e in ib[es]:
                                    p = ("if", c, t, e)
                                    if bank_int(s, p, ni) and not want_bool:
                                        return {"prog": render(p), "size": s,
                                                "tested": tested[0]}
                    if want_bool and ts in bb and es in bb:
                        for c in bb[cs]:
                            for t in bb[ts]:
                                for e in bb[es]:
                                    p = ("if", c, t, e)
                                    if bank_bool(s, p, nb) and want_bool:
                                        return {"prog": render(p), "size": s,
                                                "tested": tested[0]}
            ib[s], bb[s] = ni, nb
    except StopIteration:
        pass
    return {"miss": True, "tested": tested[0]}
