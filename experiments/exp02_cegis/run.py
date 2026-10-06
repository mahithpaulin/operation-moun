"""exp02 driver: CEGIS vs blind enumeration, same tasks, honest ratios."""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "exp01_enumeration"))
from tasks import TASKS  # noqa: E402
from cegis import cegis  # noqa: E402

BASE = HERE.parent.parent / "results" / "exp01.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rounds", type=int, default=10)
    ap.add_argument("--per-round", type=int, default=100000)
    ap.add_argument("--max-size", type=int, default=9)
    ap.add_argument("--seed-n", type=int, default=4)
    ap.add_argument("--out", default="results/exp02.json")
    args = ap.parse_args()

    base = {r["task"]: r for r in json.loads(BASE.read_text())["rows"]}
    rows = []
    for t in TASKS:
        r = cegis(t, args.max_rounds, args.per_round, args.max_size, args.seed_n)
        b = (base[t["name"]].get("detail") or {})
        blind = b.get("tested")
        blind_ev = blind * len(t["io"]) if blind else None  # upper bound
        ratio = (r["evcalls"] / blind_ev) if (blind_ev and r["prog"]) else None
        ex_used = args.seed_n + sum(
            1 for tr in r.get("trace", []) if tr["fail"] and tr["fail"] != "compile")
        rows.append({"task": t["name"], "solved": r["prog"] is not None,
                     "rounds": r["rounds"], "evcalls": r["evcalls"],
                     "examples_used": ex_used, "blind_examples": len(t["io"]),
                     "blind_tested": blind, "blind_evcalls_ub": blind_ev,
                     "ratio": round(ratio, 3) if ratio else None,
                     "secs": r["secs"], "prog": r["prog"], "trace": r["trace"]})
        print(f"{t['name']:10s} {'SOLVED' if r['prog'] else 'miss':6s} "
              f"rounds={r['rounds']} ev={r['evcalls']} ex={ex_used}/8 "
              f"blind_ev<={blind_ev} ratio={ratio and round(ratio,3)} "
              f"{(r['prog'] or '')[:50]}", flush=True)

    sol = [r for r in rows if r["solved"]]
    rats = [r["ratio"] for r in sol if r["ratio"]]
    print(f"\n{len(sol)}/{len(rows)} solved; "
          f"median ratio {sorted(rats)[len(rats)//2] if rats else '-'}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows}, indent=2))


if __name__ == "__main__":
    main()
