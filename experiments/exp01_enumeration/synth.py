"""Bottom-up enumerative synthesizer with observational-equivalence pruning.

Programs are tuples; banked by node-count size. Two programs with identical
behavior on the task inputs share a signature — only the smallest survives.
First program matching ALL outputs wins.
"""
import itertools

CONSTS = [0, 1, 2, -1, 3, 5, 10, True, False]
BINOPS = ["+", "-", "*", "//", "%", "**",
          "==", "!=", "<", ">", "<=", ">="]
BOOLOPS = ["and", "or"]
UNOPS = ["-", "not"]
CAP = 10 ** 6


class Skip(Exception):
    pass


def ev(p, env):
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
                raise Skip()
            v = (a // b) if op == "//" else (a % b)
        elif op == "**":
            if abs(a) > 10 or abs(b) > 6:
                raise Skip()
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
            raise Skip()
        if isinstance(v, (int, float)) and abs(v) > CAP:
            raise Skip()
        return v
    if t == "if":
        return ev(p[2], env) if ev(p[1], env) else ev(p[3], env)
    raise Skip()


def sz(p):
    t = p[0]
    if t in ("v", "c"):
        return 1
    if t == "u":
        return 1 + sz(p[2])
    if t == "b":
        return 1 + sz(p[2]) + sz(p[3])
    return 1 + sz(p[1]) + sz(p[2]) + sz(p[3])


def render(p):
    t = p[0]
    if t == "v":
        return p[1]
    if t == "c":
        return repr(p[1])
    if t == "u":
        return f"({p[1]} {render(p[2])})"
    if t == "b":
        return f"({render(p[2])} {p[1]} {render(p[3])})"
    return f"({render(p[2])} if {render(p[1])} else {render(p[3])})"


class BudgetOut(Exception):
    pass


def synthesize(task, max_size=9, max_programs=300000):
    envs = [{a: v for a, v in zip(task["args"], ins)} for ins, _ in task["io"]]
    wants = [out for _, out in task["io"]]
    bank = {}          # size -> [progs with DISTINCT behaviors only]
    seen = {}          # sig -> prog (global smallest wins)
    tested = 0

    def sig_of(p):
        try:
            return tuple(ev(p, e) for e in envs)
        except Exception:
            return None

    def consider(p):
        """hit = solves task; True = new behavior banked; False = dup/err."""
        nonlocal tested
        if tested >= max_programs:
            raise BudgetOut()
        s = sig_of(p)
        if s is None or s in seen:
            return False
        seen[s] = p
        tested += 1
        ok = all(w == v and (not isinstance(w, bool) or isinstance(v, bool))
                 for w, v in zip(wants, s))
        return "hit" if ok else True

    # size 1
    bank[1] = []
    for a in task["args"]:
        p = ("v", a)
        if consider(p) == "hit":
            return {"prog": render(p), "size": 1, "tested": tested}
        bank[1].append(p)
    for c in CONSTS:
        p = ("c", c)
        st = consider(p)
        if st == "hit":
            return {"prog": render(p), "size": 1, "tested": tested}
        if st is True:
            bank[1].append(p)

    try:
        for s in range(2, max_size + 1):
            bank[s] = []
            # unary
            if s - 1 in bank:
                for op in UNOPS:
                    for a in bank[s - 1]:
                        p = ("u", op, a)
                        st = consider(p)
                        if st == "hit":
                            return {"prog": render(p), "size": s, "tested": tested}
                        if st is True:
                            bank[s].append(p)
            # binary splits
            for l in range(1, s - 1):
                r = s - 1 - l
                if l not in bank or r not in bank:
                    continue
                for op in BINOPS + BOOLOPS:
                    for a in bank[l]:
                        for b in bank[r]:
                            p = ("b", op, a, b)
                            st = consider(p)
                            if st == "hit":
                                return {"prog": render(p), "size": s,
                                        "tested": tested}
                            if st is True:
                                bank[s].append(p)
            # ifexp splits: 1 + c + t + e = s
            for cs in range(1, s - 2):
                for ts in range(1, s - 1 - cs):
                    es = s - 1 - cs - ts
                    if es < 1 or cs not in bank or ts not in bank or es not in bank:
                        continue
                    for c in bank[cs]:
                        for t in bank[ts]:
                            for e in bank[es]:
                                p = ("if", c, t, e)
                                st = consider(p)
                                if st == "hit":
                                    return {"prog": render(p), "size": s,
                                            "tested": tested}
                                if st is True:
                                    bank[s].append(p)
    except BudgetOut:
        pass
    return None
