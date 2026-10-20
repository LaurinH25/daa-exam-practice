"""Step 1 of the build: copy the course data files into site/files.

Small files are copied as they are. The two large SQLite databases are cut down
to practice subsets so they can be downloaded quickly and opened in the browser:

* movies: every movie with at least 5,000 IMDb votes, plus the people linked to it.
* pcards: all transactions of a fixed, deterministic sample of cardholders
  (every year is kept, so year-over-year questions still work).

Run from anywhere:  python build/make_files.py
"""
import hashlib
import os
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT.parent / "materials"
OUT = ROOT / "site" / "files"
OUT.mkdir(parents=True, exist_ok=True)

COPIES = {
    "NYC_Film_Permits.xlsx": "1. Excel Part 1/PWC Excel Assignment/NYC_Film_Permits.xlsx",
    "ETL_Case1_balance_sheets.csv": "1. Excel part 2/ETL Assignment/data/case 1/Analytics_mindset_case_studies_ETL_Case1.csv",
    "ETL_Case2_employee_codes.xlsx": "1. Excel part 2/ETL Assignment/data/case 2/Analytics_mindset_case_studies_ETL_Case2_Excel.xlsx",
    "ETL_Case3_employee_codes_messy.xlsx": "1. Excel part 2/ETL Assignment/data/case 3/Analytics_mindset_case_studies_ETL_Case3_Excel.xlsx",
    "ETL_Case4_journal_entries.xlsx": "1. Excel part 2/ETL Assignment/data/case 4/Analytics_mindset_case_studies_ETL_Case4_Excel.xlsx",
    "IntegrateCo_2015payroll.csv": "1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_2015payroll.csv",
    "IntegrateCo_2016payroll.csv": "1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_2016payroll.csv",
    "IntegrateCo_jobcodes.csv": "1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_jobcodes.csv",
    "IntegrateCo_locations.csv": "1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_locations.csv",
    "Restaurant_sales_weather_games.xlsm": "1. Excel part 4/Regression Assignment/Restaurant/data.xlsm",
    "chinook.db": "2. SQL part 1/Assignments/pwc assignment/Chinook_Sqlite.sqlite",
    "songs.db": "2. SQL part 1/Assignments/cs50 assignment/songs/songs.db",
}


def copy_small():
    for name, rel in COPIES.items():
        shutil.copyfile(MAT / rel, OUT / name)


def fresh(path):
    if path.exists():
        path.unlink()
    return sqlite3.connect(path)


def movies_subset():
    dst = OUT / "movies_practice.db"
    con = fresh(dst)
    con.execute(f"ATTACH DATABASE '{MAT / '2. SQL part 1/Assignments/cs50 assignment/movies/movies.db'}' AS src")
    # Same schema as the CS50 database, so the course queries run unchanged.
    con.executescript("""
    CREATE TABLE movies (id INTEGER, title TEXT NOT NULL, year NUMERIC, PRIMARY KEY(id));
    CREATE TABLE people (id INTEGER, name TEXT NOT NULL, birth NUMERIC, PRIMARY KEY(id));
    CREATE TABLE stars (movie_id INTEGER NOT NULL, person_id INTEGER NOT NULL,
        FOREIGN KEY(movie_id) REFERENCES movies(id), FOREIGN KEY(person_id) REFERENCES people(id));
    CREATE TABLE directors (movie_id INTEGER NOT NULL, person_id INTEGER NOT NULL,
        FOREIGN KEY(movie_id) REFERENCES movies(id), FOREIGN KEY(person_id) REFERENCES people(id));
    CREATE TABLE ratings (movie_id INTEGER NOT NULL, rating REAL NOT NULL, votes INTEGER NOT NULL,
        FOREIGN KEY(movie_id) REFERENCES movies(id));
    INSERT INTO movies SELECT m.* FROM src.movies m JOIN src.ratings r ON r.movie_id = m.id WHERE r.votes >= 5000;
    INSERT INTO ratings SELECT r.* FROM src.ratings r WHERE r.movie_id IN (SELECT id FROM movies);
    INSERT INTO stars SELECT s.* FROM src.stars s WHERE s.movie_id IN (SELECT id FROM movies);
    INSERT INTO directors SELECT d.* FROM src.directors d WHERE d.movie_id IN (SELECT id FROM movies);
    INSERT INTO people SELECT p.* FROM src.people p
        WHERE p.id IN (SELECT person_id FROM stars UNION SELECT person_id FROM directors);
    """)
    con.commit()
    con.execute("DETACH DATABASE src")
    con.execute("VACUUM")
    con.close()


def pcards_subset(keep_one_in=10):
    src = sqlite3.connect(MAT / "2. SQL part 2/Pcards Assignment/pcards.db")
    names = [r[0] for r in src.execute("SELECT DISTINCT FullName FROM pcards")]
    keep = sorted(n for n in names
                  if int(hashlib.md5((n or "").encode()).hexdigest(), 16) % keep_one_in == 0)
    src.close()
    dst = OUT / "pcards_practice.db"
    con = fresh(dst)
    con.execute(f"ATTACH DATABASE '{MAT / '2. SQL part 2/Pcards Assignment/pcards.db'}' AS src")
    con.execute("CREATE TABLE keep (FullName TEXT PRIMARY KEY)")
    con.executemany("INSERT INTO keep VALUES (?)", [(n,) for n in keep])
    con.execute("CREATE TABLE pcards AS SELECT p.* FROM src.pcards p WHERE p.FullName IN (SELECT FullName FROM keep) ORDER BY p.ID")
    con.execute("DROP TABLE keep")
    con.commit()
    con.execute("DETACH DATABASE src")
    con.execute("VACUUM")
    con.close()


if __name__ == "__main__":
    copy_small()
    movies_subset()
    pcards_subset()
    for f in sorted(OUT.iterdir()):
        print(f"{f.stat().st_size / 1e6:8.2f} MB  {f.name}")
