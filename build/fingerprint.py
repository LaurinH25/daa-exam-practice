"""Answer fingerprints: the site can confirm an answer without containing it.

Every fingerprint is PBKDF2-SHA256(text, salt = SALT + question id). The slow
hash does not make answers secret (a determined student can still brute-force a
small integer), but the page source no longer shows any answer or reference
query, and guessing becomes far slower than solving the question.

The normalisation here must stay identical to assets/app.js (normCell,
roundTo, sortKey and the separators).
"""
import hashlib
import math
import re

SALT = "daa-practice/"
ITERATIONS = 20000
CELL_SEP = "\x1f"
ROW_SEP = "\x1e"
NUMERIC = re.compile(r"[-+]?\d+(\.\d+)?([eE][-+]?\d+)?")


def fp(qid, text):
    return hashlib.pbkdf2_hmac("sha256", text.encode("utf-8"), (SALT + qid).encode("utf-8"), ITERATIONS).hex()[:32]


def round_to(x, d):
    """Round half up like JS Math.round, formatted with d decimals."""
    r = math.floor(x * 10 ** d + 0.5) / 10 ** d
    s = f"{r:.{d}f}"
    return s[1:] if s.startswith("-") and float(s) == 0 else s


def decimals_of(v):
    s = repr(float(v))
    if "e" in s:
        return 0
    frac = s.split(".")[1].rstrip("0")
    return len(frac)


# ------------------------------------------------------------------ SQL results
def norm_cell(v):
    if v is None:
        return "∅"
    if isinstance(v, bytes):
        v = v.decode("utf-8", "replace")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return "#" + round_to(float(v), 2)
    s = str(v).strip()
    if NUMERIC.fullmatch(s):
        return "#" + round_to(float(s), 2)
    return s.lower()


def sort_key(s):
    # JS sorts strings by UTF-16 code units; match that exactly.
    return s.encode("utf-16-be")


def result_fingerprint(qid, rows):
    """rows: list of tuples from sqlite. Returns the structure the site compares against."""
    norm = [[norm_cell(c) for c in r] for r in rows]
    ncols = len(rows[0]) if rows else 0
    col_hashes = [fp(qid, "col" + CELL_SEP.join(sorted((r[j] for r in norm), key=sort_key))) for j in range(ncols)]
    order = sorted(range(ncols), key=lambda j: col_hashes[j])
    canon = [CELL_SEP.join(r[j] for j in order) for r in norm]
    return dict(
        cols=ncols,
        rows=len(rows),
        colHashes=col_hashes,
        setHash=fp(qid, "set" + ROW_SEP.join(sorted(canon, key=sort_key))),
        seqHash=fp(qid, "seq" + ROW_SEP.join(canon)),
    )


# ------------------------------------------------------------------ typed answers
def norm_text(s):
    return " ".join(str(s).lower().split()).strip("\"'")


def number_fingerprint(qid, value, tol):
    d = min(decimals_of(value), 4)
    step = 10 ** -d
    k = int(math.floor(tol / step + 1e-9))
    accepted = sorted({fp(qid, "num" + round_to(value + i * step, d)) for i in range(-k, k + 1)})
    out = dict(type="number", decimals=d, accept=accepted)
    if d >= 1:
        out["near"] = fp(qid, "near" + round_to(value, d - 1))
    return out


def number_mistake(qid, value, d):
    return fp(qid, "num" + round_to(value, d))


def text_fingerprint(qid, accept):
    return dict(type="text", accept=sorted({fp(qid, "txt" + norm_text(a)) for a in accept}))


def text_mistake(qid, value):
    return fp(qid, "txt" + norm_text(value))


def column_fingerprint(qid, values):
    """A workbook column: the multiset of its values, independent of order and header."""
    norm = sorted((norm_cell(v) for v in values), key=sort_key)
    return fp(qid, "col" + CELL_SEP.join(norm))
