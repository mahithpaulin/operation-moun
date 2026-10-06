"""Loop-schema synthesis: fixed control skeletons, enumerated hole exprs.

Schemas (holes filled from a small typed expr pool, size<=4):
  S1 acc-loop : acc=<I0>; for i in range(<B>): acc=<U(acc,i,x)>; return acc
  S2 pair-loop: a,b=<I0>,<I1>; for _ in range(<B>): a,b=<U0>,<U1>; return <R>
Combos are EXECUTED (not symbolically reasoned): bound values capped, straight
line bodies, exceptions -> combo rejected. Novel bits: none of the machinery
is new; the claim is only that schemas crack what pure expressions cannot.
"""
import itertools

CONSTS = [0, 1, 2, -1, 3, 5, 10]
ARITH = ["+", "-", "*"]
MAX_ITER = 40


def pool(args, extra_vars, size_cap=4):
    """All small exprs over args+extra_vars. Returns {source: evaluator}."""
    leaves = list(args) + list(extra_vars) + [repr(c) for c in CONSTS]
    exprs = {l: l for l in leaves}
    by_size = {1: list(leaves)}
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
        # unary minus
        if s - 1 in by_size:
            for a in by_size[s - 1]:
                cur.append(f"(- {a})")
        by_size[s] = cur
        for e in cur:
            exprs.setdefault(e, e)
    return exprs


def run_schema(src, args, ins, cap_iter=MAX_ITER):
    ns = dict(zip(args, ins))
    try:
        exec(compile(src, "<loop>", "exec"), {"__builtins__": {}}, ns)
    except Exception as e:
        return None, f"{type(e).__name__}"
    return ns.get("__out__", None), None


def s1_source(i0, b, u, args):
    x = args[0]
    return (f"__b = ({b})\n"
            f"__out__ = None\n"
            f"acc = ({i0})\n"
            f"__n = 0\n"
            f"for i in range(__b if isinstance(__b, int) and 0 <= __b <= {MAX_ITER} else 0):\n"
            f"    acc = ({u})\n"
            f"    __n += 1\n"
            f"__out__ = acc")


def s2_source(i0, i1, b, u0, u1, ret, args):
    return (f"__b = ({b})\n"
            f"a = ({i0})\n"
            f"b = ({i1})\n"
            f"for _ in range(__b if isinstance(__b, int) and 0 <= __b <= {MAX_ITER} else 0):\n"
            f"    a, b = ({u0}), ({u1})\n"
            f"__out__ = ({ret})")


def check(src, task):
    for ins, want in task["io"]:
        got, _ = run_schema(src, task["args"], ins)
        if isinstance(want, bool):
            if not isinstance(got, bool) or got != want:
                return False
        elif got != want or isinstance(got, bool):
            return False
    return True


def synthesize_loops(task, budget=2000000):
    p1 = pool(task["args"], [], 4)
    tried = 0
    # init/bound holes must not reference loop vars (unbound at that point);
    # bounds must scale with the input (constant bounds can't generalize).
    i0s = list(p1)
    bs = [e for e in p1 if "x" in e]
    # --- S1 ---
    acc_pool = pool(task["args"], ["acc", "i"], 4)
    us = [e for e in acc_pool if "acc" in e]
    for i0 in i0s:
        for b in bs:
            for u in us:
                tried += 1
                if tried > budget:
                    return {"miss": True, "tried": tried}
                if check(s1_source(i0, b, u, task["args"]), task):
                    return {"prog": f"S1 acc={i0} range({b}) acc={u}",
                            "tried": tried}
    # --- S2 ---
    r_pool = ["a", "b"]
    ab_pool = pool(task["args"], ["a", "b"], 4)
    for i0 in i0s:
        for i1 in i0s:
            for b in bs:
                for u0 in ab_pool:
                    for u1 in ab_pool:
                        for ret in r_pool:
                            tried += 1
                            if tried > budget:
                                return {"miss": True, "tried": tried}
                            if check(s2_source(i0, i1, b, u0, u1, ret,
                                               task["args"]), task):
                                return {"prog": f"S2 a,b={i0},{i1} range({b}) "
                                                f"a,b={u0},{u1} ret={ret}",
                                        "tried": tried}
    return {"miss": True, "tried": tried}
