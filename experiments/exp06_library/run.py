"""exp06 driver: teach library, then cold-vs-warm on test tasks."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "exp01_enumeration"))
import synth  # noqa: E402
from synth import synthesize  # noqa: E402
from lib import TEACH, TEST, DISTRACTOR, teach  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-size", type=int, default=9)
    ap.add_argument("--max-programs", type=int, default=300000)
    ap.add_argument("--out", default="results/exp06.json")
    args = ap.parse_args()

    lib = teach(args.max_size, args.max_programs)
    print("library:", {k: synth.render(v) for k, v in lib.items()}, flush=True)

    rows = []
    for t in TEST:
        synth.MACROS = {}
        cold = synthesize(t, args.max_size, args.max_programs) or {}
        synth.MACROS = dict(lib)
        warm = synthesize(t, args.max_size, args.max_programs) or {}
        synth.MACROS = {}
        ct = cold.get("tested")
        ratio = (warm.get("tested", 0) / ct) if (ct and "prog" in warm) else None
        rows.append({"task": t["name"],
                     "cold_solved": "prog" in cold, "cold_size": cold.get("size"),
                     "cold_tested": ct, "cold_prog": cold.get("prog"),
                     "warm_solved": "prog" in warm, "warm_size": warm.get("size"),
                     "warm_tested": warm.get("tested"),
                     "warm_prog": warm.get("prog"), "ratio": ratio})
        print(f"{t['name']:10s} cold={'Y' if 'prog' in cold else 'n'}:"
              f"{cold.get('size')}/{ct} {(cold.get('prog') or '')[:30]}",
              flush=True)
        print(f"{'':10s} warm={'Y' if 'prog' in warm else 'n'}:"
              f"{warm.get('size')}/{warm.get('tested')} "
              f"{(warm.get('prog') or '')[:30]} ratio={ratio and round(ratio, 3)}",
              flush=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"library": {k: synth.render(v) for k, v in lib.items()},
                               "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
