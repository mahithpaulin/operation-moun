# EXPERIMENTS ladder — each rung is falsifiable, CPU-only, CI-run

| rung | question it answers | success bar | feeds |
|---|---|---|---|
| exp01 | does bottom-up enumeration + behavioral pruning solve anything? | ≥4/8 smoke tasks, curve of solve-rate vs budget | all later rungs reuse the enumerator |
| exp02 | does CEGIS (fail-case feedback) beat blind enumeration per program-tested? | same solves at ≤1/3 the budget | exp03 repair, exp06 library |
| exp03 | do mined sketches + subtree repair shrink the search? | solve ≥1 task exp01 can't, or 10× fewer programs | agent loop |
| exp04 | does AST evolution solve loop-shaped tasks enumeration can't reach? | ≥1 loop task (fib/sum_to_n) solved | consensus pool |
| exp05 | does retrieval-stitch solve real-library tasks (str/list API)? | ≥2 API-heavy tasks no grammar method solves | consensus pool |
| exp06 | does a learned library compound (solve harder tasks AFTER easy ones)? | tasks unsolvable cold become solvable warm | the paper |
| final | full HumanEval + MBPP, consensus harness, honest pass@1 | report whatever it is; ablation per method | research write-up |

Protocol per rung: fixed task slice (committed), fixed budget (committed),
seed-pinned, results JSON committed by CI. A rung that fails its bar is
REPORTED, then either fixed or cut — no silent goalpost moves. Scale-up to
full HumanEval starts at exp03 (matrix jobs, 164 tasks × timeout).
