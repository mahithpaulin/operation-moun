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
    return {"miss": True, "tested": tested}


class CegisEnum:
    """Persistent-bank enumerator for CEGIS.

    Key property: every program is fully evaluated ONCE, ever. When examples
    grow, banked programs extend their signatures with ONE ev-call each
    instead of being re-enumerated from scratch. Cost unit = ev-calls.
    dbank holds behaviorally-distinct programs only (pruning is
    example-relative); by_sig tracks current signatures for dedupe/hits.
    """

    def __init__(self, args):
        self.args = args
        self.dbank = {}      # size -> [behaviorally-DISTINCT progs]
        self.by_sig = {}     # sig -> prog (current examples)
        self.prog_sig = {}   # prog -> sig
        self.envs = []
        self.wants = []
        self.evcalls = 0
        self.done_size = 0

    def _ev(self, p, e):
        self.evcalls += 1
        return ev(p, e)

    def _full_sig(self, p):
        try:
            return tuple(self._ev(p, e) for e in self.envs)
        except Exception:
            return None

    def _matches(self, s):
        return (len(s) == len(self.wants) and all(
            w == v and (not isinstance(w, bool) or isinstance(v, bool))
            for w, v in zip(self.wants, s)))

    def _register(self, p, size):
        s = self._full_sig(p)
        if s is None or s in self.by_sig:
            return None
        self.by_sig[s] = p
        self.prog_sig[p] = s
        self.dbank.setdefault(size, []).append(p)
        return p if self._matches(s) else None

    def add_examples(self, ios):
        for ins, want in ios:
            e = {a: v for a, v in zip(self.args, ins)}
            self.envs.append(e)
            self.wants.append(want)
            new_by, dead = {}, []
            for p, s in self.prog_sig.items():
                try:
                    v = self._ev(p, e)
                except Exception:
                    dead.append(p)
                    continue
                ns = s + (v,)
                if ns in new_by:
                    old = new_by[ns]
                    if sz(p) < sz(old):
                        dead.append(old)
                        new_by[ns] = p
                    else:
                        dead.append(p)
                else:
                    new_by[ns] = p
            dead_set = set(dead)
            for p in dead:
                self.prog_sig.pop(p, None)
            for lst in self.dbank.values():
                lst[:] = [p for p in lst if p not in dead_set]
            self.by_sig = new_by
            self.prog_sig = {p: s for s, p in new_by.items()}

    def current_hit(self):
        for s, p in self.by_sig.items():
            if self._matches(s):
                return p
        return None

    def gen_size(self, s, allowance):
        def over():
            if self.evcalls >= allowance:
                raise BudgetOut()
        if s == 1:
            for a in self.args:
                if self._register(("v", a), 1) is not None:
                    return ("v", a)
            for c in CONSTS:
                st = self._register(("c", c), 1)
                if st is not None:
                    return st
            return None
        if s - 1 in self.dbank:
            for op in UNOPS:
                for a in list(self.dbank[s - 1]):
                    over()
                    p = ("u", op, a)
                    if self._register(p, s) is not None:
                        return p
        for l in range(1, s - 1):
            r = s - 1 - l
            if l not in self.dbank or r not in self.dbank:
                continue
            for op in BINOPS + BOOLOPS:
                for a in list(self.dbank[l]):
                    for b in list(self.dbank[r]):
                        over()
                        p = ("b", op, a, b)
                        if self._register(p, s) is not None:
                            return p
        for cs in range(1, s - 2):
            for ts in range(1, s - 1 - cs):
                es = s - 1 - cs - ts
                if es < 1 or cs not in self.dbank \
                        or ts not in self.dbank or es not in self.dbank:
                    continue
                for c in list(self.dbank[cs]):
                    for t in list(self.dbank[ts]):
                        for e in list(self.dbank[es]):
                            over()
                            p = ("if", c, t, e)
                            if self._register(p, s) is not None:
                                return p
        return None

    def generate_until_hit(self, max_size, allowance):
        if self.done_size == 0:
            hit = self.gen_size(1, allowance)
            self.done_size = 1
            if hit is not None:
                return hit
        while self.done_size < max_size:
            self.done_size += 1
            hit = self.gen_size(self.done_size, allowance)
            if hit is not None:
                return hit
        return None
