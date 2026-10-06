"""exp01 driver: synthesize each smoke task, report solve-rate vs budget."""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tasks import TASKS
from synth import synthesize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-size", type=int, default=9)
    ap.add_argument("--max-programs", type=int, default=300000)
    ap.add_argument("--out", default="results/exp01.json")
    args = ap.parse_args()

    rows = []
    for t in TASKS:
        t0 = time.perf_counter()
        try:
            r = synthesize(t, args.max_size, args.max_programs)
        except Exception as e:
            r = {"error": f"{type(e).__name__}: {e}"}
        dt = time.perf_counter() - t0
        rows.append({"task": t["name"], "solved": r is not None and "prog" in r,
                     "detail": r, "secs": round(dt, 2)})
        flag = "SOLVED" if rows[-1]["solved"] else "miss"
        print(f"{t['name']:10s} {flag:6s} {dt:6.2f}s "
              f"{(r or {}).get('prog', '')[:70]}", flush=True)

    solved = sum(r["solved"] for r in rows)
    print(f"\n{ solved}/{len(rows)} solved")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"solved": solved, "total": len(rows),
                               "rows": rows}, indent=2))
    # exit 0: misses are data. Harness errors (no rows at all) would raise above.


if __name__ == "__main__":
    main()
