"""Build the question bank for the practice site.

    python build/make_files.py   # once: copies data + creates DB subsets
    python build/build.py        # computes answers, validates SQL, writes site/data/bank.js

Every SQL reference query is executed here; a query that fails or returns
nothing stops the build. Exams are drawn with a fixed seed, so exam IDs stay
stable between builds (the same exams students practise are used in the exam).
"""
import datetime
import json
import random
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bank_concepts  # noqa: E402
import bank_excel  # noqa: E402
import bank_regression  # noqa: E402
import bank_sql  # noqa: E402
import fingerprint  # noqa: E402
import mistakes_sql  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FILES = ROOT / "site" / "files"

DATASETS = {
    "film": dict(label="NYC film permits", kind="excel", course="Excel Part 1",
                 files=["NYC_Film_Permits.xlsx"],
                 about="33,502 film permits issued by New York City (PwC Excel assignment)."),
    "case1": dict(label="Balance sheet extract (ETL Case 1)", kind="excel", course="Excel Part 2",
                  files=["ETL_Case1_balance_sheets.csv"],
                  about="A messy comma-separated balance sheet extract: units, brackets, duplicates and an unqualified comma."),
    "case2": dict(label="Employee codes (ETL Case 2)", kind="excel", course="Excel Part 2",
                  files=["ETL_Case2_employee_codes.xlsx"],
                  about="597 EmployeeCodes such as JAP1080-19M = Location, EmpID, PlantID, PayPeriod."),
    "case3": dict(label="Messy employee codes (ETL Case 3)", kind="excel", course="Excel Part 2",
                  files=["ETL_Case3_employee_codes_messy.xlsx"],
                  about="The same codes with variable-length locations (US, Canada, Japan), IDs and pay periods (M/Mo, W/We)."),
    "journal": dict(label="Hotel journal entries (ETL Case 4)", kind="excel", course="Excel Part 2",
                    files=["ETL_Case4_journal_entries.xlsx"],
                    about="789 journal entry lines plus business units, chart of accounts, preparers and sources to join."),
    "payroll": dict(label="IntegrateCo payroll 2015/2016", kind="excel", course="Excel Part 3",
                    files=["IntegrateCo_2015payroll.csv", "IntegrateCo_2016payroll.csv",
                           "IntegrateCo_jobcodes.csv", "IntegrateCo_locations.csv"],
                    about="Pipe-delimited payroll from two different systems, job codes and employee locations."),
    "chinook": dict(label="Chinook music store", kind="sqlite", course="SQL Part 1",
                    files=["chinook.db"], about="PwC's Chinook database: customers, invoices, tracks, employees."),
    "songs": dict(label="CS50 songs", kind="sqlite", course="SQL Part 1",
                  files=["songs.db"], about="100 songs and 70 artists."),
    "movies": dict(label="CS50 movies (practice subset)", kind="sqlite", course="SQL Part 1",
                   files=["movies_practice.db"],
                   about="The CS50 movies schema, reduced to the 11,699 movies with at least 5,000 IMDb votes."),
    "pcards": dict(label="OSU P-cards (practice subset)", kind="sqlite", course="SQL Part 2",
                   files=["pcards_practice.db"],
                   about="All transactions 2010–2014 of a fixed 10% sample of OSU cardholders (one table, pcards)."),
    "restaurant": dict(label="Restaurant sales, weather and games", kind="excel", course="Excel Part 4",
                       files=["Restaurant_sales_weather_games.xlsm"],
                       about="Larry's Commissary daily item sales, weather and game days (regression case)."),
}

N_EXAMS = 60
EXAM_SEED = 2026
MIN_MINUTES, MAX_MINUTES = 7, 10


CLAUSES = {
    "filter": "WHERE", "like": "WHERE … LIKE", "in": "WHERE … IN (…)", "null": "IS NULL / IS NOT NULL", "count": "COUNT",
    "distinct": "DISTINCT", "aggregate": "an aggregate (SUM / AVG / MIN / MAX)", "group_by": "GROUP BY", "having": "HAVING",
    "sort": "ORDER BY", "limit": "LIMIT", "join": "JOIN … ON", "left_join": "LEFT JOIN", "subquery": "a subquery",
    "case": "CASE WHEN", "date": "STRFTIME / JULIANDAY", "string": "string functions (SUBSTR, LENGTH, INSTR, TRIM)",
    "expression": "a calculated column", "alias": "table aliases", "refund": "the sign of Amount (returns are negative)",
}


def secure_sql(questions):
    """Replace each reference query by a fingerprint of its result, plus hints for known mistakes."""
    cons = {}
    for qn in questions:
        db = FILES / DATASETS[qn["file"]]["files"][0]
        con = cons.setdefault(qn["file"], sqlite3.connect(db))
        rows = con.execute(qn["check"]["sql"]).fetchall()
        if not rows or (len(rows) == 1 and all(v is None for v in rows[0])):
            raise SystemExit(f"{qn['id']}: reference query returns no data")
        ref = fingerprint.result_fingerprint(qn["id"], rows)
        mistakes = []
        for sql, hint in mistakes_sql.MISTAKES.get(qn["id"], []):
            got = con.execute(sql).fetchall()
            mf = fingerprint.result_fingerprint(qn["id"], got) if got else None
            if mf is None or mf["setHash"] == ref["setHash"]:
                print(f"  note: mistake variant for {qn['id']} gives the correct or an empty result; dropped")
                continue
            mistakes.append(dict(fp=mf["setHash"], hint=hint))
        qn["check"] = dict(type="sql", ordered=qn["check"]["ordered"], **ref, mistakes=mistakes)
        qn["method"] = "You will need: " + ", ".join(dict.fromkeys(CLAUSES[t] for t in qn["topics"] if t in CLAUSES)) + "."
    for c in cons.values():
        c.close()


AUTO_HINTS = [
    (lambda v: -v, "Right size, wrong sign: check whether the value should be negative or positive."),
    (lambda v: v * 100, "Check the units: the question asks for a percent (e.g. 12.34), not a share."),
    (lambda v: v / 100, "Check the units: give the percent (e.g. 12.34), not a share (0.1234)."),
    (lambda v: v * 1000, "Off by a factor of 1,000: check K/M units or thousands."),
    (lambda v: v / 1000, "Off by a factor of 1,000: check K/M units or thousands."),
]


def secure_typed(questions):
    """Replace Excel answers by fingerprints; keep the method text (it never contains the answer)."""
    leaks = []
    for qn in questions:
        c, qid = qn["check"], qn["id"]
        if c["type"] == "columns":
            cols = []
            for column in c["columns"]:
                right = fingerprint.column_fingerprint(qid, column["values"])
                wrong = []
                for values, hint in column["mistakes"]:
                    h = fingerprint.column_fingerprint(qid, values)
                    if h != right:
                        wrong.append(dict(fp=h, hint=hint))
                cols.append(dict(name=column["name"], rows=len(column["values"]), fp=right, mistakes=wrong))
            qn["check"] = dict(type="columns", columns=cols)
            qn["method"] = qn.pop("solution")
            continue
        mistakes = []
        if c["type"] == "number":
            v = c["value"]
            secured = fingerprint.number_fingerprint(qid, v, c["tol"])
            d = secured["decimals"]
            candidates = [(val, hint) for val, hint in qn.pop("mistakes", [])]
            if v != 0:
                candidates += [(f(v), hint) for f, hint in AUTO_HINTS]
            for val, hint in candidates:
                h = fingerprint.number_mistake(qid, float(val), d)
                if h not in secured["accept"] and h not in [m["fp"] for m in mistakes]:
                    mistakes.append(dict(fp=h, hint=hint))
            shown = fingerprint.round_to(v, d)
            if shown in qn["solution"] and len(shown) >= 3:
                leaks.append(qid)
        else:
            secured = fingerprint.text_fingerprint(qid, c["accept"])
            for a in c["accept"]:
                if a.isdigit() and a.startswith("0"):
                    mistakes.append(dict(fp=fingerprint.text_mistake(qid, a.lstrip("0")),
                                         hint="Keep the leading zeros: job codes are text (001, not 1)."))
            for val, hint in qn.pop("mistakes", []):
                mistakes.append(dict(fp=fingerprint.text_mistake(qid, val), hint=hint))
            if any(a.lower() in qn["solution"].lower() for a in c["accept"] if len(a) > 3):
                leaks.append(qid)
        qn["check"] = dict(secured, mistakes=mistakes)
        qn["method"] = qn.pop("solution")
    if leaks:
        raise SystemExit(f"method text reveals the answer for: {', '.join(leaks)}")


def file_meta():
    out = {}
    for k, v in DATASETS.items():
        out[k] = dict(v, sizes=[(FILES / f).stat().st_size for f in v["files"]])
    return out


def make_exams(questions):
    """Each exam: one Excel dataset + one SQL database, 2 Excel + 3 SQL questions.
    Draws favour questions that have been used least, so the whole bank is covered."""
    rng = random.Random(EXAM_SEED)
    by_file = {}
    for qn in questions:
        if not qn.get("practiceOnly"):
            by_file.setdefault(qn["file"], []).append(qn)
    excel_files = [k for k, v in DATASETS.items() if v["kind"] == "excel" and k in by_file]
    sql_files = [k for k, v in DATASETS.items() if v["kind"] == "sqlite" and k in by_file]
    used = Counter()
    exams = []
    for i in range(N_EXAMS):
        ef = excel_files[i % len(excel_files)]
        sf = sql_files[(i // len(excel_files) + i) % len(sql_files)]

        # Draw the least-used questions, re-drawing until the exam fits the time budget.
        ex_pool = sorted(by_file[ef], key=lambda q: (used[q["id"]], rng.random()))
        sq_pool = sorted(by_file[sf], key=lambda q: (used[q["id"]], rng.random()))
        for attempt in range(2000):
            # Start with the least-used questions and widen the pool if nothing fits.
            ex = rng.sample(ex_pool[:min(len(ex_pool), 4 + attempt // 50)], 2)
            sq = rng.sample(sq_pool[:min(len(sq_pool), 6 + attempt // 50)], 3)
            total = sum(q["minutes"] for q in ex + sq)
            if MIN_MINUTES <= total <= MAX_MINUTES:
                break
        else:
            raise SystemExit(f"no exam within the time budget for {ef} + {sf}")
        qs = ex + sq
        for q in qs:
            used[q["id"]] += 1
        exams.append(dict(id=f"E{i + 1:03d}", files=[ef, sf], questions=[q["id"] for q in qs],
                          minutes=round(sum(q["minutes"] for q in qs) * 2) / 2))
    return exams


def main():
    sql_q = bank_sql.QUESTIONS
    unknown = set(mistakes_sql.MISTAKES) - {q["id"] for q in sql_q}
    assert not unknown, unknown
    secure_sql(sql_q)
    excel_q = bank_excel.build(FILES)
    secure_typed(excel_q)
    for qn in excel_q:
        if qn["file"] in ("pay15", "pay16"):
            qn["file"] = "payroll"
    questions = excel_q + sql_q
    ids = [q["id"] for q in questions]
    dupes = [i for i, n in Counter(ids).items() if n > 1]
    assert not dupes, dupes
    for q in questions:
        assert q["file"] in DATASETS, q["id"]
    regression = bank_regression.build(FILES)
    bank = dict(
        built=datetime.date.today().isoformat(),
        datasets=file_meta(),
        questions=questions,
        exams=make_exams(questions),
        regression=regression,
        concepts=bank_concepts.CONCEPTS,
    )
    # The feedback Worker only accepts a question ID, so it carries its own copy of the
    # interpretation questions and model answers.
    worker_data = {q["id"]: dict(title=r["title"], context=r["context"], variables=r["variables"], kind=q["kind"],
                                 equation=q["equation"], coefs=q["coefs"], prompt=q["prompt"], model=q["model"], points=q["points"])
                   for r in regression for q in r["questions"]}
    (ROOT / "worker" / "src" / "regression.json").write_text(json.dumps(worker_data, ensure_ascii=False, indent=1), encoding="utf-8")
    out = ROOT / "site" / "data" / "bank.js"
    out.write_text("window.BANK = " + json.dumps(bank, ensure_ascii=False, default=float) + ";\n", encoding="utf-8")
    print(f"{len(questions)} manipulation questions ({len(excel_q)} Excel, {len(sql_q)} SQL), "
          f"{len(bank['exams'])} exams, {len(regression)} interpretation exams, {len(bank['concepts'])} concept checks")
    print(f"wrote {out} ({out.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
