# Compute budget ledger — GPU hard cap 2.0 h (Kaggle T4, user-set)

| # | run | purpose | cap | spent | note |
|---|---|---|---|---|---|
| 0 | — | CPU rehearsals (Actions + phone) | 0 | 0 | free, unlimited public |
| 1 | moun-exp04-loops | loop schemas, full budget | CPU kernel | 0 GPU | CPU kernels bill no GPU quota |
| — | reserve | one GPU kernel if a neural rung needs it | 2.0h GPU | 0 | unspent = returned |

Rules: quota checked before AND after every Kaggle run (`kaggle quota`,
refreshes Mon 00:00 UTC). CPU kernels preferred everywhere; GPU only for
work that is actually matrix-bound. The old 15h GPU plan is dead.
