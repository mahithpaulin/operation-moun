"""exp03 driver: typed enumeration vs blind, same tasks."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "exp01_enumeration"))
from tasks import TASKS  # noqa: E402
from sketch import synthesize_typed  # noqa: E402

BASE = HERE.parent.parent / "results" / "exp01.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-size", type=int, default=9)
    ap.add_argument("--max-programs", type=int, default=300000)
    ap.add_argument("--out", default="results/exp03.json")
    args = ap.parse_args()

    base = {r["task"]: r for r in json.loads(BASE.read_text())["rows"]}
    rows = []
    for t in TASKS:
        r = synthesize_typed(t, args.max_size, args.max_programs) or {}
        b = (base[t["name"]].get("detail") or {})
        blind = b.get("tested")
        ratio = (r.get("tested", 0) / blind) if (blind and "prog" in r) else None
        rows.append({"task": t["name"], "solved": "prog" in r,
                     "tested": r.get("tested"), "blind_tested": blind,
                     "ratio": round(ratio, 3) if ratio else None,
                     "prog": r.get("prog")})
        print(f"{t['name']:10s} {'SOLVED' if 'prog' in r else 'miss':6s} "
              f"tested={r.get('tested')} blind={blind} "
              f"ratio={ratio and round(ratio,3)} "
              f"{(r.get('prog') or '')[:55]}", flush=True)
    sol = [x for x in rows if x["solved"]]
    print(f"\n{len(sol)}/{len(rows)} solved")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows}, indent=2))


if __name__ == "__main__":
    main()
