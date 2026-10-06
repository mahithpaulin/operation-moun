"""exp05 driver: warm (retrieval-seeded) vs cold, same grammar."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from tasks import TASKS  # noqa: E402
from synth_api import synthesize_api  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-size", type=int, default=9)
    ap.add_argument("--max-programs", type=int, default=300000)
    ap.add_argument("--out", default="results/exp05.json")
    args = ap.parse_args()

    rows = []
    for t in TASKS:
        cold = synthesize_api(t, seed=False, max_size=args.max_size,
                              max_programs=args.max_programs) or {}
        warm = synthesize_api(t, seed=True, max_size=args.max_size,
                              max_programs=args.max_programs) or {}
        ct, wt = cold.get("tested"), warm.get("tested")
        ratio = (wt / ct) if (ct and wt and "prog" in warm) else None
        rows.append({"task": t["name"],
                     "cold_solved": "prog" in cold, "cold_tested": ct,
                     "cold_prog": cold.get("prog"),
                     "warm_solved": "prog" in warm, "warm_tested": wt,
                     "warm_prog": warm.get("prog"), "ratio": ratio})
        print(f"{t['name']:14s} cold={'Y' if 'prog' in cold else 'n'}:{ct} "
              f"warm={'Y' if 'prog' in warm else 'n'}:{wt} "
              f"ratio={ratio and round(ratio, 3)}", flush=True)
        print(f"   warm: {(warm.get('prog') or '')[:60]}", flush=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows}, indent=2))


if __name__ == "__main__":
    main()
