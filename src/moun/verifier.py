"""Symbolic core: syntax gate + sandboxed exec verifier. Ground truth, no learning."""
import ast
import multiprocessing as mp


def syntax_ok(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except Exception:
        return False


def _run(q, code: str, tests: str):
    try:
        ns = {"__builtins__": __builtins__}
        exec(compile(code + "\n" + tests, "<cand>", "exec"), ns)
        q.put((True, ""))
    except AssertionError as e:
        q.put((False, f"assert: {e}"))
    except Exception as e:
        q.put((False, f"{type(e).__name__}: {e}"))


def verify(code: str, tests: str, timeout: int = 5):
    """Returns (passed: bool, trace: str). Never raises."""
    if not syntax_ok(code):
        return False, "SyntaxError"
    q = mp.Queue()
    p = mp.Process(target=_run, args=(q, code, tests))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return False, "Timeout"
    try:
        return q.get_nowait()
    except Exception:
        return False, "Crash"
