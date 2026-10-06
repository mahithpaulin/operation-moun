# OPERATION MOUN — specialist coding agent, no giant models

**Direction v0.2 (active): CI-native program-synthesis research.**
No fine-tuning, no pretrained weights, no GPU training. We compete where
scale doesn't matter: search + verification + accumulated knowledge.
Start at [`BRAINSTORM.md`](BRAINSTORM.md) (10 novel directions, scored),
then [`EXPERIMENTS.md`](EXPERIMENTS.md) (the falsifiable ladder).
First blood: `experiments/exp01_enumeration` — bottom-up enumeration with
behavioral pruning solved **7/8 smoke tasks**, including discovering the
closed form `n(n+1)/2` for a task designed to need loops.

**Direction v0.1 (shelved): from-scratch micro-decoder + 15h Kaggle train.**
Kept in `src/moun/` + `SPEC.md` + `BUDGET.md` for the eventual neural-guide
rungs (a tiny CPU-trained guide for the enumerator needs no GPU). The box
stays stopped; GitHub Actions is the computer.

## Honest framing

15 T4-hours ≈ 1e21 FLOPs ≈ 100M params × ~2B tokens. That cannot touch 27B
frontier models. The winnable game: **best possible tiny from-scratch coder**
+ execution-verified agent loop, with every number reported as-is. Any claim
otherwise would be fiction.

## System (see SPEC.md)

```
problem → memory retrieval (prototype exemplars) → task vector
  → conditioned micro-decoder → candidates
  → symbolic verifier (syntax + exec tests) → repair search → final code
```

- `src/moun/tokenizer.py` — byte-level tokenizer, zero training, vocab 256+K
- `src/moun/model.py` — decoder-only Transformer, configured by size
- `src/moun/memory.py` — PAHO-lineage prototype memory → per-task vector
- `src/moun/verifier.py` — sandboxed exec test runner (the symbolic core)
- `src/moun/agent.py` — generate → verify → repair loop (coding only)
- `src/moun/train.py` — from-scratch LM loop, HF-streamed code, token budget
- `src/moun/eval.py` — HumanEval/MBPP-style pass@k runner

## Budget (see BUDGET.md)

15.0 GPU-h cap: 1h pipeline smoke + 10h main train + 2h eval + 2h reserve.
Failed runs still bill — every kernel is rehearsed on CPU first.

## Layout

- `SPEC.md` — architecture
- `BUDGET.md` — spend ledger (updated per run)
- `problems/` — smoke problems for CPU dry-runs
- `tools/build_kernel.py` — concatenates `src/moun/*` into one Kaggle file
  (script kernels upload `code_file` ONLY)
- `kaggle/` — kernel metadata template + run log
