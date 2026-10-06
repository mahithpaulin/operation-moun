# OPERATION MOUN — research report: what actually works in CPU-native synthesis

Constraints (held throughout): no pretrained weights, no GPU training, no
frontier-model APIs. Computer: GitHub Actions CPU (free public tier) +
Kaggle CPU kernels (0.00 GPU-h spent of a 2h cap). Everything deterministic,
seed-pinned, committed as JSON by CI.

## The ladder and its verdicts

| rung | idea | result | verdict |
|---|---|---|---|
| exp01 | bottom-up enumeration + behavioral pruning | 7/8 smoke | ✅ baseline; discovered closed-form `n(n+1)/2` for a "needs loops" task |
| exp02 | CEGIS, persistent bank | 4/8 | ❌ FALSIFIED: guidance loses to pruning power on ev-cost; only query-count wins (4–5 vs 8 examples) |
| exp03 | typed int/bool banks (R1–R5) | 7/8 | ⚠️ ~2× on hard tasks (`max_two` 0.51×, `sum_to_n` 0.46×); 8× worse on `is_even` (small-task luck) |
| exp04 | loop schemas S1/S1b/S2 | **3/4** (sum 73 tries, pow2n 723, fact 6510 via S1b) | ⚠️ schemas crack iteration cheaply; `fib` needs S2 ordering still being tuned (200k-budget shard timed out) |
| exp05 | retrieval-seeded API synthesis | 4/4, warm 0.16–0.56× | ✅ compositional reuse + shorter programs (`min(x)` beats `sorted(x)[0]`) |
| exp06 | library macros from solved tasks | depth 5→3, 12–18× fewer | ✅✅ flagship: knowledge compounds; distractor unused |

## Thesis (earned, not assumed)

1. **Pruning beats guidance.** exp02's mechanism: example count IS pruning
   strength. Fewer examples → bigger banks → more work. Any guided method
   must overcome this tax first.
2. **Types are mild pruning, not magic.** exp03: ~2× where junk dominates.
3. **Schemas beat expressions for iteration.** No expression grammar reaches
   `fib` at any size; a 3-schema library gets 3/4 loop tasks in hundreds
   of tries.
4. **Only accumulated knowledge compounds.** exp05 (retrieve parts, glue)
   and exp06 (macros from solved tasks) are the only rungs with
   order-of-magnitude wins. Everything else is linear. The DreamCoder-lite
   direction (BRAINSTORM.md #1) is where the remaining upside lives:
   anti-unification (compress solutions into parameterized components),
   then re-attack.
5. **Sparse tests are the whole game.** exp01's `not (x // 5)` "solution"
   to is_even (passes 4 tests, nonsense) is the visible/hidden gap in
   miniature. Every rung uses 8 adversarial cases because 4 admit garbage.

## Engineering log (bugs that taught)

- Eager-dict dispatch evaluated `a//b` for every op → ZeroDivisionError
  killed all programs on zero inputs. Lazy chains only.
- Bank appended duplicates → combinatorial explosion; behavioral dedupe is
  load-bearing, not an optimization.
- Sandbox stripped `int`/`range`/`isinstance` → every schema failed silently.
- Var-first pool order buried `fib`'s `i0=0` behind 149M combos; consts-first
  + bound-leads ordering fixed it analytically.
- Two CI bot commits racing → push rejected; fixed with full clone +
  fetch-rebase-retry (then: silent `exit 0` swallowed a real commit;
  commit steps are loud now).

## Cost

~40 Actions runs (free), 0.00 Kaggle GPU-h, ~1.5 Codespaces wall-hours for
kernel pushes. Near-infinite time, near-zero money: the intended regime.

## Next (not done)

- exp06 with anti-unification (parameterized macros, not verbatim).
- Neural guide rung: tiny CPU-trained ranker over enumerator frontier.
- HumanEval slice with per-method ablations + consensus harness.
- `fib` via guided S2 (the open chase).
