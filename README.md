# DAA Exam Practice

A practice website for the oral exam in **Data Analytics in Accounting**. Students practise the same
exams they can get at the exam: a **data manipulation** exam (2 Excel + 3 SQL tasks on two course
data sets) and a **data interpretation** exam (four regression outputs).

Everything is built only from the course cases in `../materials`:

| Course part | Data set | Questions |
|---|---|---|
| Excel Part 1 | NYC film permits (PwC) | 24 |
| Excel Part 2 | ETL Cases 1–4 (balance sheets, employee codes, messy codes, hotel journal entries) | 29 |
| Excel Part 3 | IntegrateCo payroll 2015/2016 | 18 |
| SQL Part 1 | Chinook (PwC), CS50 songs, CS50 movies | 32 + 12 + 16 |
| SQL Part 2 | OSU P-cards | 25 |
| Excel Part 4 | Restaurant regression case | 2 exams fitted on the course data + 10 synthetic contexts |

Plus 20 concept checks (ETL overview, joins, four V's, PwC SQL slides, P-card controls).

## Control-total feedback (the improvement over the reference site)

The exams are reused at the real exam, so the site **checks answers without containing them**:

* **Fingerprints, not answers.** The build stores only PBKDF2 fingerprints of each Excel answer
  and of each SQL result (per column, the full row set and the row order). The page source holds
  no answers and no reference queries; the site fingerprints the student's answer and compares.
* **Feedback like control totals.** An SQL result is reconciled step by step: columns, row count
  (direction only: too many / too few), column totals (which of the student's columns match),
  how values combine into rows, and the order when a sort is asked for. Column names and column
  order do not matter; numbers are compared at 2 decimals.
* **Targeted hints for the traps in the cases.** For each question the build also runs typical
  wrong approaches (refunds included in P-card totals, PreparerID matched without the business
  unit, job code 001 turned into 1, K/M units not converted, Mo not read as monthly, boundary
  errors, a missing year filter, …) and stores their fingerprints. If a student's result matches
  one exactly, the site shows that hint. Sign and unit slips (×100, ×1,000) are detected for every
  numeric answer. Mistake variants that happen to give the correct result are dropped.
* **No solutions.** After three failed checks a method note appears (formula approach for Excel,
  the clauses needed for SQL); the answer itself is never shown.
* **Exam mode.** During a timed exam there is no feedback, as at the real exam. *Finish exam*
  reconciles every answer at once; after that, checking is switched on for that exam.

The fingerprints slow down guessing but are not encryption: a determined student could brute-force
a small integer. The real safeguard is that the exam is oral and the examiner watches the work.

Regression predictions are still checked against plain values, because the interpretation
exams show a model answer anyway.

## Excel workbook upload

Excel answers are checked by uploading the workbook; the file is read in the browser (SheetJS) and
never sent to a server.

* **Final-value questions:** the answer goes in cell A1 (or B1 next to a label) of a sheet named
  after the question, e.g. `E302` — the cases' own convention for answer tabs (`P4_Q1`). The site
  checks the value and whether it is calculated with a formula. Typing the value is still possible
  in practice mode.
* **Column tasks** (`X201`–`X502`, practice only): the student builds the columns of ETL Cases 2–4
  and the IntegrateCo job codes; the site finds each column anywhere in the workbook (header and
  position don't matter), reconciles its values, flags pasted values instead of formulas, and gives
  hints for known mistakes. Case 4's PreparerName is left out because 148 journal lines have a
  PreparerID/business unit pair that is not in PreparerInfo.
* **Exam mode:** one workbook for all Excel questions of the exam, checked at *Finish exam*.

## AI feedback on written interpretations (optional)

`worker/` holds a Cloudflare Worker that asks Google Gemini (free tier) to compare a student's written interpretation
with the model answer and checklist. It deploys from GitHub Actions once the secrets are set and is
switched on by `site/assets/config.js`. Setup and cost: [worker/README.md](worker/README.md).

No answer in the bank is typed by hand: `build/build.py` computes every value from the data,
runs every reference SQL query and mistake variant, and stops if a query fails, returns nothing,
or if a method note would reveal its answer.

## Project layout

```
build/make_files.py   copies the course data into site/files, builds the movie and P-card subsets
build/build.py        computes answers, validates SQL, draws 60 fixed exams -> site/data/bank.js
build/bank_*.py       the questions (Excel, SQL, regression, concepts)
site/                 the static website (index.html, assets/, data/, files/)
```

The two large databases are cut to practice subsets so they load in a browser: movies with at
least 5,000 IMDb votes (2 MB) and all P-card transactions of a fixed 10% sample of cardholders (8 MB).

## Build and run

```bash
python build/make_files.py
python build/build.py
python -m http.server 8765 --directory site
```

Then open http://localhost:8765. Requires Python 3 with pandas, openpyxl and statsmodels.

## Deploy

`site/` is a plain static folder (largest file 8.4 MB), so it can be published as-is on GitHub
Pages, Cloudflare Pages or Netlify. Exam IDs are drawn with a fixed seed, so they stay stable
between builds.
