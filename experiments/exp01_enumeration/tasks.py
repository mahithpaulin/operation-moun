"""exp01 smoke tasks: 6 solvable by expression grammar, 2 need loops (expect fail).

NOTE (lesson from first run): 4 examples admit overfit garbage, e.g.
`is_even` "solved" by `not (x // 5)`, `max_two` by `y % (y + 1)` — both pass
4 tests and are nonsense. So every task carries 8 cases incl. adversarial
values. Sparse tests are the visible/hidden gap in miniature.
"""
TASKS = [
    {"name": "add", "args": ["x", "y"],
     "io": [((1, 2), 3), ((0, 0), 0), ((-4, 7), 3), ((10, -3), 7),
            ((100, 200), 300), ((-1, -1), -2), ((0, 5), 5), ((-8, 8), 0)]},
    {"name": "mul", "args": ["x", "y"],
     "io": [((3, 4), 12), ((0, 9), 0), ((-2, 5), -10), ((7, 7), 49),
            ((11, 11), 121), ((-3, -3), 9), ((1, -1), -1), ((6, 0), 0)]},
    {"name": "is_even", "args": ["x"],
     "io": [((4,), True), ((7,), False), ((0,), True), ((-3,), False),
            ((10,), True), ((11,), False), ((100,), True), ((-100,), True)]},
    {"name": "max_two", "args": ["x", "y"],
     "io": [((1, 2), 2), ((5, 5), 5), ((-1, -9), -1), ((0, 4), 4),
            ((3, 3), 3), ((-5, 2), 2), ((100, -100), 100), ((-7, -2), -2)]},
    {"name": "abs_val", "args": ["x"],
     "io": [((3,), 3), ((-3,), 3), ((0,), 0), ((-11,), 11),
            ((-7,), 7), ((9,), 9), ((1,), 1), ((-1,), 1)]},
    {"name": "pow2", "args": ["x"],
     "io": [((3,), 9), ((0,), 0), ((-4,), 16), ((5,), 25),
            ((6,), 36), ((-1,), 1), ((2,), 4), ((-2,), 4)]},
    # boundary: need loops — grammar cannot express; expect FAIL (data, not bug)
    {"name": "sum_to_n", "args": ["x"],
     "io": [((3,), 6), ((0,), 0), ((5,), 15), ((10,), 55),
            ((1,), 1), ((7,), 28), ((2,), 3), ((20,), 210)]},
    {"name": "fib", "args": ["x"],
     "io": [((0,), 0), ((1,), 1), ((6,), 8), ((9,), 34),
            ((2,), 1), ((5,), 5), ((10,), 55), ((12,), 144)]},
]
