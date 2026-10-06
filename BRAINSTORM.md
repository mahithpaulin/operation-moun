# BRAINSTORM — novel coding architectures that don't need scale

Premise: we cannot out-train frontier labs (no GPU, no data moat). So every
direction below competes on an axis where scale is NOT the decider: **search
+ verification + accumulated knowledge**. The verifier (tests) is free ground
truth — the model proposes, reality disposes. A 0.1M-symbolic system with a
perfect filter can beat a 27B model that can't check its own work.

Scoring: N = novelty (1–5), C = CPU/CI-fit (1–5), L = HumanEval leverage
(1–5). Built first = highest N×C×L with lowest risk.

## 1. DreamCoder-lite: library-learning enumerative synthesis ★ BUILD FIRST
Wake–sleep loop over a Python-subset grammar: enumerate programs bottom-up
with observational-equivalence pruning → solve easy tasks → **compress
solutions into reusable components (library)** via anti-unification →
re-enumerate with the grown library → harder tasks fall. The library is the
"learning"; it compounds across tasks, unlike LLM sampling which forgets
everything. Fully CPU. This is the flagship: genuine learning, zero gradient.
N5 C5 L4.

## 2. CEGIS over Python (counterexample-guided inductive synthesis)
Classic formal-methods loop, underused on HumanEval: guess program from a
few inputs → verify against full tests → feed the failing case back as a new
constraint → repeat. Each round strictly shrinks the candidate space. Novel
twist: the guesser is the enumerator from (1), the verifier is exec, and the
"spec miner" synthesizes properties (e.g. output ranges) from passing runs.
N4 C5 L4. Merges into exp02/03.

## 3. Test-driven AST evolution (modern genetic programming)
Population of ASTs grown from the function stub; operators: subtree
mutation, crossover between passing candidates, simplification pressure
(parsimony vs tests-passed fitness). 2020s GPs died because fitness was
weak — here fitness is exact (hidden-test proxy + visible tests). Add
**island model + novelty search** to escape local optima. N3 C5 L3. exp04.

## 4. Retrieval-stitch synthesis
Vendor a permissively-licensed function corpus; retrieve by test-signature
(input/output types + behavior probes); **stitch** fragments with
symbolic glue (arg-mapping, constant-fitting by mini-search) and verify.
Nobody ships this because LLMs made retrieval look dumb — but with a
verifier, dumb retrieval + smart glue is exact. Needs corpus infra. N4 C4
L4. exp05.

## 5. Type-directed sketch + hole-fill
Symbolically generate typed skeletons from the signature + docstring nouns
(e.g. `def f(xs): return <list-expr over xs>`), leaving holes; fill holes by
enumerative search 10–100× smaller than full-program search. Types prune
exponentially. Novel bit: **sketch mining from failing candidates** — a
candidate that passes 3/5 tests donates its skeleton. N4 C5 L3. exp03.

## 6. Execution-trace backpropagation (no neural net)
Treat the interpreter as differentiable-by-search: run candidate, find the
first diverging operation vs expected output, backtrack the AST to the
responsible node, mutate ONLY that node. Credit assignment without a single
weight. N5 C4 L3. Later.

## 7. Adversarial test co-evolution
Two populations: programs vs generated test cases. Tests evolve to break
programs; programs evolve to pass tests. Survivors are robust beyond the
given visible tests → higher hidden-test pass rate. Directly attacks the
visible/hidden gap. N4 C4 L4 (as a booster for 1–3). Later.

## 8. Proof-carrying patches (repair as search, not sampling)
Given a failing candidate: localize fault by delta-debugging the AST
(remove subtrees until tests flip), then synthesize ONLY the replacement
subtree under the inferred local spec. Repair search space ≪ generation
space. N3 C5 L3. Folds into agent loop now.

## 9. Cross-task analogy engine (PAHO lineage, symbolic)
Store solved tasks as (abstracted problem, abstracted solution) pairs;
abstract = replace identifiers/constants with roles. New problem → find
analogous abstraction → replay the transformation. This is case-based
reasoning with teeth (verifier checks the replay). The fewshot-lab PAHO
idea, minus the network. N4 C5 L3. exp06.

## 10. Consensus of weak synthesizers
Run 1–5 in parallel with disjoint biases; majority vote on behavior (not
text) over generated inputs; return the candidate surviving all others'
tests. Ensemble works when errors are uncorrelated — symbolic methods with
different grammars are maximally uncorrelated. The harness, not a method.
N2 C5 L4. Final assembly.

## Rejected (honestly)
- Tiny-LM + verifier sampling: still needs GPU training; loses to (1) per
  CI-hour. Shelved, not dead.
- LLM API distillation: depends on someone else's frontier model; not
  self-contained research. No.
- Full formal verification (SMT for all of Python): intractable; CEGIS
  uses SMT nowhere — exec is the solver.

## Order of battle
exp01 enumeration+pruning (calibration) → exp02 CEGIS loop → exp03
sketch/hole + repair → exp04 evolution → exp05 retrieval-stitch →
exp06 analogy + library learning (the DreamCoder-lite core) → consensus
harness + full HumanEval reporting.
