# GPU budget ledger — hard cap 15.0 h/week (Kaggle T4)

| # | run | purpose | cap | spent | note |
|---|---|---|---|---|---|
| 0 | — | CPU rehearsals (Actions) | 0 | 0 | free, unlimited |
| 1 | scout | 5M model, pipeline end-to-end | 1.0h | — | kills: data stream, OOM, verifier |
| 2 | moun-100m-A | 100M LM, ~2B tokens | 10.0h | — | the train |
| 3 | eval | HumanEval + MBPP pass@k | 2.0h | — | includes Phase-B adapter fit |
| — | reserve | retries / ablations | 2.0h | — | unspent = returned, not burned |

Rules: quota checked before AND after every run (`kaggle quota`, refreshes
Mon 00:00 UTC). Any run exceeding its cap is killed, not extended. Failed
runs still bill — so runs 1–3 only launch after their exact config passes
the CPU rehearsal + `CSBT_SMOKE`-style local rehearsal.
