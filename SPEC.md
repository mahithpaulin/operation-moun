# MOUN architecture spec (v0.1 — from scratch)

## 1. Neural core: micro-decoder (random init, no pretraining)

Decoder-only Transformer, byte-level vocab (512: 256 bytes + specials):

| config | layers | d_model | heads | params | role |
|---|---|---|---|---|---|
| smoke | 2 | 64 | 2 | ~0.1M | CPU/Actions rehearsal |
| scout | 6 | 256 | 4 | ~5M | 1h GPU pipeline smoke |
| moun-100m | 12 | 768 | 12 | ~100M | 10h main train, ~2B tokens |

RoPE + SwiGLU + RMSNorm (modern, cheap). Context 1024 (code functions are
short; HumanEval fits). Objective: next-byte prediction on raw Python files.

## 2. PAHO-lineage fast memory (trained jointly, from scratch)

Not a prompt trick — a trained module:

1. Episodic memory stores solved (problem-sketch, solution) pairs as vectors
   from the decoder's own mean-pooled states (no external encoder).
2. For a new problem: retrieve top-k prototype exemplars by cosine,
   task vector `z = MLP(mean(prototypes))`.
3. Per-task adapter: hypernetwork `H([proto; z])` emits a low-rank delta
   applied to the decoder's final layers (rank 8 — tiny, T4-friendly).
4. Learned gate `g(z)` decides: answer directly vs spend repair rounds.

This is the "1–2 strong examples" mechanism from the fewshot lab, scaled to
code: the model extracts the task's shape from retrieved exemplars instead
of re-learning syntax every problem.

## 3. Symbolic core (no learning, no mercy)

- **Syntax gate**: `ast.parse` rejects garbage before exec (cost ~0).
- **Exec verifier**: candidate runs against visible tests in a subprocess
  with timeout + restricted builtins. A candidate either passes or dies —
  the verifier is ground truth, not a learned reward model.
- **Repair search**: best-first over (candidate, error-trace) pairs.
  Error messages are fed back verbatim as conditioning for the next
  generation round (max R rounds, budgeted).

## 4. Agent loop (coding only — refuses everything else)

```
solve(problem, tests):
  exemplars = memory.retrieve(problem, k=2)
  z, adapter, g = memory.condition(exemplars)
  beam = decoder.sample(problem, adapter, n=N)
  for candidate in rank(beam):
    if syntax_ok and verifier.passes(candidate, tests): return candidate
  for r in range(R):
    trace = verifier.error_trace(best_so_far)
    beam = decoder.repair(problem, trace, adapter, n=N//2)
    ... same check ...
  return best_so_far  # failed, logged as failed — never faked
```

The agent has no chat, no tools besides the verifier, no other domain.
It codes or it reports failure.

## 5. Training (from scratch, token-budgeted)

- Data: streamed open Python files (HF, language-filtered) + small
  instruction set for the repair format. Raw bytes in, no tokenizer
  training, no pretrained anything. Exact manifest pinned in train.py.
- Phase A (10h): next-byte LM on ~2B tokens, moun-100m.
- Phase B (inside eval budget): freeze decoder, train ONLY memory +
  hyperadapter + gate on repair traces (episodic, PAHO-style objective).
  If Phase B fails, ship Phase A + symbolic-only harness (ablation).

## 6. Evaluation

HumanEval (164) + MBPP sanitized (500), Python, pass@1 / pass@10 with the
verifier disallowed from seeing hidden tests (visible-test filtering only
where the bench protocol allows; reported per-protocol). Baselines:
decoder-only (no memory, no repair) vs full MOUN — the ablation IS the
paper. Success = full MOUN beats decoder-only by a margin, reported with
the absolute numbers whatever they are.
