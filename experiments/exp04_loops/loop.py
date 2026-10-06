"""Loop-schema synthesis: fixed control skeletons, enumerated hole exprs.

Schemas (holes from behaviorally-deduped expr pools, size<=3):
  S1  acc-loop 0-based: acc=<I0>; for i in range(<B>): acc=<U>; return acc
  S1b acc-loop 1-based: acc=<I0>; for i in range(1,<B>): acc=<U>; return acc
  S2  pair-loop: a,b=<I0>,<I1>; for _ in range(<B>): a,b=<U0>,<U1>; return <R>
Combos are EXECUTED: bounds capped at 40, bodies straight-line, exceptions
reject the combo. Pools are deduped by behavior on the task inputs
(x+0 dies so (x+1) is found sooner). Claim: schemas crack iteration tasks
that pure expression grammars cannot express at any size.
"""
CONSTS = [0, 1, 2, -1, 3, 5, 10]
ARITH = ["+", "-", "*"]
MAX_ITER = 40
CAP = 10 ** 6


def pool(args, extra_vars, envs, size_cap=3):
    """Small exprs over args+extra_vars, ONE per behavior on envs.

    Leaves ordered consts-first: inits/first-holes are almost always small
    constants (0/1); vars come after. (A var-first order buries fib's i0=0
    behind 54 i0s x full subspaces each.)
    """
    leaves = [repr(c) for c in CONSTS] + list(args) + list(extra_vars)
    kept, seen, by_size = [], set(), {1: []}
    for l in leaves:
        s = _sig(l, envs)
        if s is not None and s not in seen:
            seen.add(s)
            kept.append(l)
            by_size[1].append(l)
    for s in range(2, size_cap + 1):
        cur = []
        for l in range(1, s - 1):
            r = s - 1 - l
            if l not in by_size or r not in by_size:
                continue
            for op in ARITH:
                for a in by_size[l]:
                    for b in by_size[r]:
                        cur.append(f"({a} {op} {b})")
        if s - 1 in by_size:
            for a in by_size[s - 1]:
                cur.append(f"(- {a})")
        sized = []
        for e in cur:
            g = _sig(e, envs)
            if g is not None and g not in seen:
                seen.add(g)
                kept.append(e)
                sized.append(e)
        by_size[s] = sized
    return kept, list(by_size[1])


def _sig(src, envs):
    try:
        code = compile(src, "<pool>", "eval")
    except Exception:
        return None
    out = []
    for e in envs:
        try:
            v = eval(code, {"__builtins__": {}}, dict(e))
        except Exception:
            return None
        if isinstance(v, bool) or not isinstance(v, int) or abs(v) > CAP:
            return None
        out.append(v)
    return tuple(out)


_SAFE_BUILTINS = {"isinstance": isinstance, "range": range, "int": int}


def run_schema(src, args, ins):
    ns = dict(zip(args, ins))
    try:
        exec(compile(src, "<loop>", "exec"),
             {"__builtins__": _SAFE_BUILTINS}, ns)
    except Exception:
        return None
    return ns.get("__out__", None)


def _guard(bound):
    return (f"range(__b if isinstance(__b, int) and 0 <= __b <= {MAX_ITER} "
            f"else 0)")


def s1_source(i0, b, u):
    return (f"__b = ({b})\nacc = ({i0})\n"
            f"for i in {_guard('__b')}:\n    acc = ({u})\n__out__ = acc")


def s1b_source(i0, b, u):
    return (f"__b = ({b})\nacc = ({i0})\n"
            f"for i in range(1, (__b if isinstance(__b, int) and 1 <= __b <= {MAX_ITER + 1} else 1)):\n"
            f"    acc = ({u})\n__out__ = acc")


def s2_source(i0, i1, b, u0, u1, ret):
    return (f"__b = ({b})\na = ({i0})\nb = ({i1})\n"
            f"for _ in {_guard('__b')}:\n    a, b = ({u0}), ({u1})\n"
            f"__out__ = ({ret})")


def check(src, task):
    for ins, want in task["io"]:
        got = run_schema(src, task["args"], ins)
        if got != want or isinstance(got, bool):
            return False
    return True


def synthesize_loops(task, budget=3000000):
    envs = [{a: v for a, v in zip(task["args"], ins)} for ins, _ in task["io"]]
    p1, l1 = pool(task["args"], [], envs)
    # Inits and pair-updates are leaves in every solved instance so far
    # (0/1/x/a/b); bounds and accumulators need full exprs. Capping the
    # former cuts S2's inner product ~40x. Documented bet, not theorem.
    i0s = list(l1)
    bs = [e for e in p1 if "x" in e]
    tried = [0]
    # hole envs bind loop vars to sample values (i/x kept distinct so they
    # never merge under dedupe). Dedupe is relative to these samples.
    henvs = [{task["args"][0]: xv, "acc": av, "i": iv, "a": av, "b": iv}
             for xv in (0, 1, 5) for av in (0, 1, 5) for iv in (0, 2, 7)]

    def over():
        tried[0] += 1
        return tried[0] > budget

    # --- S1 (0-based) ---
    acc_all, acc_leaves = pool(task["args"], ["acc", "i"], henvs)
    leaf_us = [e for e in acc_leaves if "acc" in e]
    us = leaf_us + [e for e in acc_all if "acc" in e and e not in leaf_us]
    for i0 in i0s:
        for b in bs:
            for u in us:
                if over():
                    return {"miss": True, "tried": tried[0]}
                if check(s1_source(i0, b, u), task):
                    return {"prog": f"S1 acc={i0} range({b}) acc={u}",
                            "tried": tried[0]}
    # --- S1b (1-based) ---
    for i0 in i0s:
        for b in bs:
            for u in us:
                if over():
                    return {"miss": True, "tried": tried[0]}
                if check(s1b_source(i0, b, u), task):
                    return {"prog": f"S1b acc={i0} range1({b}) acc={u}",
                            "tried": tried[0]}
    # --- S2 (pair) ---
    # Updates that ignore both state vars are pointless (constant assignment
    # inside a loop). Mention-filter cuts the S2 inner product ~10x.
    ab, ab1 = pool(task["args"], ["a", "b"], henvs)
    ab_use = [e for e in ab if "a" in e or "b" in e]
    ab1_use = [e for e in ab1 if "a" in e or "b" in e]
    # Loop order b,i0,i1,u0,u1,ret: bounds almost always mention x (idx0),
    # so the bound leads; the old i0-first order burned 138k tries inside
    # (i0=0,i1=0) before ever advancing.
    for b in bs:
        for i0 in i0s:
            for i1 in i0s:
                for u0 in ab1_use:
                    for u1 in ab_use:
                        for ret in ("a", "b"):
                            if over():
                                return {"miss": True, "tried": tried[0]}
                            if check(s2_source(i0, i1, b, u0, u1, ret), task):
                                return {"prog": f"S2 a,b={i0},{i1} range({b}) "
                                                f"a,b={u0},{u1} ret={ret}",
                                        "tried": tried[0]}
    return {"miss": True, "tried": tried[0]}
