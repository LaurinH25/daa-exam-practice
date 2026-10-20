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


def validate_sql(questions):
    cons = {}
    for qn in questions:
        db = FILES / DATASETS[qn["file"]]["files"][0]
        con = cons.setdefault(qn["file"], sqlite3.connect(db))
        rows = con.execute(qn["check"]["sql"]).fetchall()
        if not rows or (len(rows) == 1 and all(v is None for v in rows[0])):
            raise SystemExit(f"{qn['id']}: reference query returns no data")
        qn["check"]["rows"] = len(rows)
        qn["solution"] = qn["check"]["sql"]
        # Preview of the expected result: shown after the student checks or reveals.
        qn["check"]["preview"] = [list(r) for r in rows[:8]]
    for c in cons.values():
        c.close()


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
    validate_sql(sql_q)
    excel_q = bank_excel.build(FILES)
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
    out = ROOT / "site" / "data" / "bank.js"
    out.write_text("window.BANK = " + json.dumps(bank, ensure_ascii=False, default=float) + ";\n", encoding="utf-8")
    print(f"{len(questions)} manipulation questions ({len(excel_q)} Excel, {len(sql_q)} SQL), "
          f"{len(bank['exams'])} exams, {len(regression)} interpretation exams, {len(bank['concepts'])} concept checks")
    print(f"wrote {out} ({out.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
