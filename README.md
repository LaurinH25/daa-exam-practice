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

## How answers are checked

* **SQL**: the student's query runs in the browser (sql.js) on the same database they can download.
  Its result is compared with the reference query's result: column names and column order are
  ignored, numbers are compared at 2 decimals, and row order only counts when the question asks
  for a sort. Feedback says what differs (column count, row count, values, order).
* **Excel**: students work in Excel and type one final value; it is compared with a value
  computed from the same file by the build script (with a tolerance for rounding).
* **Regression**: predictions and turning points are checked numerically; written
  interpretations are compared with a generated model answer and a checklist.

No answer in the bank is typed by hand: `build/build.py` computes every value from the data,
runs every reference SQL query and stops if one fails or returns nothing.

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
