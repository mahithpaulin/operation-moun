"""exp04 driver: loop schemas on iteration tasks."""
import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from tasks import TASKS  # noqa: E402
from loop import synthesize_loops  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int,
                    default=int(os.environ.get("EXP04_BUDGET", 2000000)))
    ap.add_argument("--out", default="results/exp04.json")
    args = ap.parse_args()

    rows = []
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for t in TASKS:
        t0 = time.perf_counter()
        r = synthesize_loops(t, args.budget)
        dt = time.perf_counter() - t0
        rows.append({"task": t["name"], "solved": "prog" in r,
                     "tried": r.get("tried"), "secs": round(dt, 2),
                     "prog": r.get("prog")})
        print(f"{t['name']:10s} {'SOLVED' if 'prog' in r else 'miss':6s} "
              f"tried={r.get('tried')} {dt:.1f}s {(r.get('prog') or '')[:60]}",
              flush=True)
        out.write_text(json.dumps({"rows": rows}, indent=2))
    print(f"\n{sum(r['solved'] for r in rows)}/{len(rows)} solved")
    out.write_text(json.dumps({"rows": rows}, indent=2))


if __name__ == "__main__":
    main()
