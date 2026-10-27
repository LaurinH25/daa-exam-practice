"""Excel questions. Students work in Excel on the downloaded file and type one
final value; every expected value below is computed from the same file so the
answers cannot drift from the data.
"""
import csv
import re
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

FILM = "Excel Part 1 · NYC film permits"
ETL = "Excel Part 2 · ETL cases"
PAY = "Excel Part 3 · IntegrateCo payroll"


def num(v, tol=0.01):
    return dict(type="number", value=float(v), tol=tol)


def text(*accept):
    return dict(type="text", accept=[str(a) for a in accept])


def with_mistakes(questions, mistakes):
    """Attach known wrong answers (value, hint) to the questions; the build fingerprints them."""
    by_id = {x["id"]: x for x in questions}
    for qid, items in mistakes.items():
        by_id[qid]["mistakes"] = items
    return questions


def q(id, file, course, topics, minutes, prompt, check, solution):
    return dict(id=id, file=file, subject="Excel", course=course, topics=topics,
                minutes=minutes, prompt=prompt, check=check, solution=solution)


# ---------------------------------------------------------------- film permits
def film_questions(d):
    f = pd.read_excel(d / "NYC_Film_Permits.xlsx")
    sp = f[f.EventType == "Shooting Permit"].copy()
    zip_n = pd.to_numeric(f.ZipCode, errors="coerce")
    missing_zip = int(f.ZipCode.isna().sum())
    invalid_zip = int((f.ZipCode.notna() & ((zip_n < 10000) | (zip_n > 99999) | zip_n.isna())).sum())
    multi_cb = (sp["CommunityBoard(s)"].astype(str).str.contains(",")).mean()
    sp["Year"] = sp.StartDateTime.dt.year
    by = sp.pivot_table(index="Year", columns="Borough", values="EventID", aggfunc="count")
    bk_year = int(by[by.Brooklyn > by.Manhattan].index.min())
    man = sp[sp.Borough == "Manhattan"]
    broadway = man.ParkingHeld.str.upper().str.contains("BROADWAY").mean()
    foreign = int(((sp.Country != "United States of America") & (sp.EnteredOn.dt.year >= 2013)).sum())
    dur_h = (sp.EndDateTime - sp.StartDateTime).dt.total_seconds() / 3600
    shortest_min = (sp.EndDateTime - sp.StartDateTime).dt.total_seconds().min() / 60
    lead = (sp.StartDateTime - sp.EnteredOn).dt.total_seconds().mean() / 86400
    weekday = sp.StartDateTime.dt.day_name().value_counts().idxmax()

    def touches_friday(r):
        days = pd.date_range(r.StartDateTime.normalize(), r.EndDateTime.normalize())
        return any(x.dayofweek == 4 for x in days)
    friday = sp.apply(touches_friday, axis=1).mean()
    tv_sub = sp[sp.Category == "Television"].SubCategoryName.value_counts().idxmax()
    queens = int((sp.Borough == "Queens").sum())
    film_share = (sp.Category == "Film").mean()
    theater_borough = f[f.EventType == "Theater Load in and Load Outs"].Borough.value_counts().idxmax()
    rig_dur = ((f[f.EventType == "Rigging Permit"].EndDateTime - f[f.EventType == "Rigging Permit"].StartDateTime)
               .dt.total_seconds() / 3600).mean()
    y2017 = int((f.StartDateTime.dt.year == 2017).sum())
    oldest = f.EnteredOn.min()

    piv = "Insert ▸ PivotTable"
    only_sp = "Your number uses every event type. The question is about shooting permits only (EventType = Shooting Permit)."
    allf_dur = ((f.EndDateTime - f.StartDateTime).dt.total_seconds() / 3600).mean()
    mistakes = {
        "F04": [(missing_zip + invalid_zip, "Blank ZipCodes are missing values (previous question), not invalid ones.")],
        "F09": [(int((f.Category == "Student").sum()), only_sp)],
        "F10": [(round(f["CommunityBoard(s)"].astype(str).str.contains(",").mean() * 100, 2), only_sp)],
        "F14": [(round(allf_dur * 2) / 2, only_sp)],
        "F16": [(round((f.StartDateTime - f.EnteredOn).dt.total_seconds().mean() / 86400), only_sp)],
        "F20": [(int((f.Borough == "Queens").sum()), only_sp)],
        "F21": [(round((f.Category == "Film").mean() * 100, 2), only_sp)],
    }
    return with_mistakes([
        q("F01", "film", FILM, ["data_profiling"], 1, "How many records (data rows, excluding the header) does the table have?",
          num(len(f), 0), "Select a column and read the Count in the status bar, or =COUNTA(A:A)-1."),
        q("F02", "film", FILM, ["data_profiling"], 0.5, "How many columns does the table have?",
          num(f.shape[1], 0), "Count the header cells, or =COUNTA(1:1)."),
        q("F03", "film", FILM, ["data_quality", "countblank"], 1, "How many records have a missing ZipCode?",
          num(missing_zip, 0), "=COUNTBLANK(N2:N33503), or filter the ZipCode column on (Blanks)."),
        q("F04", "film", FILM, ["data_quality"], 1.5, "How many records have a ZipCode that is present but not a valid five-digit zip code?",
          num(invalid_zip, 0), "Helper column =LEN(N2) and count values that are not 5 and not 0, or sort ZipCode ascending and inspect the smallest values."),
        q("F05", "film", FILM, ["data_profiling"], 1, "Which column has the same value for every record? Give the exact column name.",
          text("EventAgency"), "Use =COUNTA(UNIQUE(range)) per column, or open each filter drop-down: the column you want shows a single entry."),
        q("F06", "film", FILM, ["date", "aggregate"], 1, "In which year was the oldest EnteredOn value entered?",
          num(oldest.year, 0), "=MIN(E2:E33503) and format as a date (or =YEAR(MIN(E:E)))."),
        q("F07", "film", FILM, ["distinct"], 1, "How many different event types are there?",
          num(f.EventType.nunique(), 0), f"{piv} with EventType in Rows, or =COUNTA(UNIQUE(B2:B33503))."),
        q("F08", "film", FILM, ["pivot"], 1.5, "Among shooting permits, what is the most common Category?",
          text(sp.Category.value_counts().idxmax()), f"Filter EventType = Shooting Permit; {piv} with Category in Rows and Count of EventID, sort descending."),
        q("F09", "film", FILM, ["countifs"], 1.5, "How many shooting permits were granted for student films (Category = Student)?",
          num(int((sp.Category == "Student").sum()), 0), '=COUNTIFS(B:B,"Shooting Permit",K:K,"Student")'),
        q("F10", "film", FILM, ["text_functions", "percentage"], 2.5,
          "What percentage of shooting permits involve more than one Community Board? Answer in percent with 2 decimals (e.g. 12.34).",
          num(round(multi_cb * 100, 2), 0.02), 'Helper column =ISNUMBER(SEARCH(",",I2)); count TRUE for shooting permits and divide by the number of shooting permits.'),
        q("F11", "film", FILM, ["date", "pivot"], 2.5, "In which year did the number of shooting permits in Brooklyn first exceed those in Manhattan (use StartDateTime)?",
          num(bk_year, 0), f"Helper column =YEAR(C2); {piv} with Year in Rows, Borough in Columns, filtered to Shooting Permit."),
        q("F12", "film", FILM, ["text_functions", "percentage"], 2.5,
          "What percentage of Manhattan shooting permits take place on or near Broadway (ParkingHeld contains 'BROADWAY')? Round to the nearest whole percent.",
          num(round(broadway * 100), 0), '=COUNTIFS(B:B,"Shooting Permit",H:H,"Manhattan",G:G,"*BROADWAY*") / COUNTIFS(B:B,"Shooting Permit",H:H,"Manhattan")'),
        q("F13", "film", FILM, ["countifs", "date"], 2, "How many shooting permit applications entered in 2013 or later came from a country other than the United States of America?",
          num(foreign, 0), '=COUNTIFS(B:B,"Shooting Permit",M:M,"<>United States of America",E:E,">="&DATE(2013,1,1))'),
        q("F14", "film", FILM, ["date", "duration"], 2.5, "What is the average duration of a shooting permit in hours? Round to the nearest half hour (e.g. 12.5).",
          num(round(dur_h.mean() * 2) / 2, 0), "Helper column =(D2-C2)*24 gives hours; AVERAGE over shooting permits; =MROUND(x,0.5)."),
        q("F15", "film", FILM, ["date", "duration"], 2, "What was the duration of the shortest shooting permit, in minutes?",
          num(round(shortest_min), 0), "Helper column =(D2-C2)*24*60, then MIN for shooting permits."),
        q("F16", "film", FILM, ["date", "duration"], 2, "What is the average lead time in days between EnteredOn and StartDateTime for shooting permits? Round to the nearest day.",
          num(round(lead), 0), "Helper column =C2-E2 (days), AVERAGE for shooting permits, =ROUND(x,0)."),
        q("F17", "film", FILM, ["date", "text_functions"], 2, "On which day of the week do shooting permits most often start? Give the full day name.",
          text(weekday), 'Helper column =TEXT(C2,"dddd"); PivotTable count by day.'),
        q("F18", "film", FILM, ["date", "logic"], 4,
          "What percentage of shooting permits include at least part of a Friday (any day from the start date to the end date is a Friday)? Answer in percent with 2 decimals.",
          num(round(friday * 100, 2), 0.05), "A permit touches a Friday if its date span contains one: e.g. =OR(WEEKDAY(C2,2)=5, INT(D2)-INT(C2) >= MOD(5-WEEKDAY(C2,2),7)). Average the TRUE/FALSE over shooting permits."),
        q("F19", "film", FILM, ["pivot"], 1.5, "For shooting permits in the Television category, which SubCategoryName is most common?",
          text(tv_sub), f"{piv}: filter Shooting Permit and Television, SubCategoryName in Rows, count, sort descending."),
        q("F20", "film", FILM, ["countifs"], 1, "How many shooting permits took place in Queens?",
          num(queens, 0), '=COUNTIFS(B:B,"Shooting Permit",H:H,"Queens")'),
        q("F21", "film", FILM, ["percentage"], 1.5, "What share of shooting permits have Category = Film? Answer in percent with 2 decimals.",
          num(round(film_share * 100, 2), 0.02), '=COUNTIFS(B:B,"Shooting Permit",K:K,"Film")/COUNTIF(B:B,"Shooting Permit")'),
        q("F22", "film", FILM, ["pivot"], 1.5, "Which borough has the most 'Theater Load in and Load Outs' permits?",
          text(theater_borough), f"{piv} with Borough in Rows filtered on that EventType."),
        q("F23", "film", FILM, ["date", "duration"], 2, "What is the average duration in hours of Rigging Permits? Round to 1 decimal.",
          num(round(rig_dur, 1), 0.05), "Helper column =(D2-C2)*24; =AVERAGEIF(B:B,\"Rigging Permit\",helper)."),
        q("F24", "film", FILM, ["date", "countifs"], 1.5, "How many permits (all event types) started in 2017?",
          num(y2017, 0), '=COUNTIFS(C:C,">="&DATE(2017,1,1),C:C,"<"&DATE(2018,1,1))'),
    ], mistakes)


# ---------------------------------------------------------------- ETL case 1
def parse_amount(v):
    """Convert the messy Case 1 amounts into plain numbers (dollars)."""
    s = str(v).strip()
    if s in ("", "-", "nan"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace(",", "").replace(" ", "")
    mult = 1
    if s.endswith("M"):
        mult, s = 1_000_000, s[:-1]
    elif s.endswith("K"):
        mult, s = 1_000, s[:-1]
    x = float(s) * mult
    return -x if neg else x


def case1_questions(d):
    # "Apple, Inc." contains an unqualified comma, so those rows have one field
    # too many; rebuild them the way students must in Excel.
    lines = (d / "ETL_Case1_balance_sheets.csv").read_text(encoding="utf-8").splitlines()[1:]
    shifted = sum(1 for r in csv.reader(lines) if len(r) == 9)
    rows = []
    for parts in csv.reader(lines):
        if len(parts) == 9:  # name split by the comma in "Apple, Inc."
            parts = [parts[0], parts[1] + "," + parts[2]] + parts[3:]
        rows.append(parts)
    df = pd.DataFrame(rows, columns=["Ticker", "Name", "Year", "Cash", "AR", "Inv", "TCA", "Dep"])
    dupes = int(df.duplicated().sum())
    clean = df.drop_duplicates().copy()
    clean["CashN"] = clean.Cash.map(parse_amount)
    clean["DepN"] = clean.Dep.map(parse_amount)
    cash2018 = clean[clean.Year == "2018"].CashN.sum()
    bad_ticker = int((clean.Ticker.str.strip() == "").sum() + clean.Ticker.str.contains(" ").sum())
    aal_dep = clean[clean.Ticker == "AAL"].DepN.sum()
    with_dupes = df.assign(CashN=df.Cash.map(parse_amount))
    mistakes = {
        "E104": [(with_dupes[with_dupes.Year == "2018"].CashN.sum(),
                  "Aptevo's 2018 row appears twice. Remove the exact duplicate before summing.")],
        "E105": [(int((clean.Ticker.str.strip() == "").sum()), "Blank tickers are only part of it: 'A M Z N' and 'AM ZN' contain spaces too.")],
    }
    return with_mistakes([
        q("E101", "case1", ETL, ["data_quality", "delimiters"], 1.5,
          "Some rows split into one column too many when the CSV is opened. How many data rows are affected?",
          num(shifted, 0), "The name 'Apple, Inc.' contains a comma but no text qualifier (\"\"), so the comma acts as a delimiter. Fix with Text to Columns / Power Query or by re-joining the two name cells."),
        q("E102", "case1", ETL, ["duplicates"], 1, "How many exact duplicate rows does the file contain?",
          num(dupes, 0), "Data ▸ Remove Duplicates (all columns) and read the message, or COUNTIFS on all columns."),
        q("E103", "case1", ETL, ["units", "transformation"], 2,
          "After converting K (thousands) and M (millions) to full dollars, what is Aehr Test Systems' Cash in 2017, in dollars?",
          num(parse_amount("17800 K"), 0), '=VALUE(SUBSTITUTE(D2," K",""))*1000 for K values; *1000000 for M values.'),
        q("E104", "case1", ETL, ["units", "transformation"], 3,
          "After removing duplicates and converting every Cash value to full dollars, what is the total Cash of all companies in 2018? Answer in dollars.",
          num(cash2018, 1), 'Helper column: =IF(RIGHT(D2)="M",VALUE(LEFT(D2,LEN(D2)-2))*10^6,IF(RIGHT(D2)="K",VALUE(LEFT(D2,LEN(D2)-2))*10^3,VALUE(D2))); then SUMIFS on Year = 2018.'),
        q("E105", "case1", ETL, ["data_quality", "unique_identifier"], 1.5,
          "How many rows (after removing duplicates) have a Ticker that is blank or contains spaces?",
          num(bad_ticker, 0), "Filter the Ticker column for blanks and use =ISNUMBER(SEARCH(\" \",A2)); fix with TRIM/SUBSTITUTE."),
        q("E106", "case1", ETL, ["negative_numbers", "transformation"], 2,
          "Total Depreciation uses brackets for negatives in some rows. What is the sum of American Airlines' Total Depreciation for 2016–2018 as a (negative) number in dollars?",
          num(aal_dep, 1), '=-VALUE(SUBSTITUTE(SUBSTITUTE(H2,"(",""),")","")) when the value is in brackets.'),
    ], mistakes)


# ---------------------------------------------------------------- ETL case 2 & 3
def split_case2(code):
    m = re.fullmatch(r"([A-Z]{3})(\d+)-(\d+)([A-Z])", code)
    return m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)


def split_case3(code):
    m = re.fullmatch(r"([A-Za-z]+)(\d+)-(\d+)([A-Za-z]+)", code)
    pay = "W" if m.group(4).upper().startswith("W") else "M"
    return m.group(1), int(m.group(2)), int(m.group(3)), pay, m.group(4)


def case2_questions(d):
    df = pd.read_excel(d / "ETL_Case2_employee_codes.xlsx", sheet_name="Case 2")
    parts = df.EmployeeCode.map(split_case2)
    df["Loc"], df["Emp"], df["Plant"], df["Pay"] = zip(*parts)
    df["LP"] = df.Loc + "-" + df.Plant.astype(str)
    top_lp = df.LP.value_counts()
    assert top_lp.iloc[0] > top_lp.iloc[1]
    sol = ("Formulas: Location =LEFT(A2,3); EmpID =VALUE(MID(A2,4,4)); PlantID =VALUE(MID(A2,FIND(\"-\",A2)+1,2)); "
           "PayPeriod =RIGHT(A2,1); LocationPlantID =B2&\"-\"&D2 (e.g. USA-12).")
    mistakes = {
        "E205": [(0, "MID returns text, and SUM ignores text: wrap the extraction in VALUE().")],
    }
    return with_mistakes([
        q("E201", "case2", ETL, ["text_functions", "countif"], 1.5, "After splitting EmployeeCode, how many employees work in Germany (GER)?",
          num(int((df.Loc == "GER").sum()), 0), sol),
        q("E202", "case2", ETL, ["text_functions", "countif"], 1.5, "How many employees are paid weekly (PayPeriod = W)?",
          num(int((df.Pay == "W").sum()), 0), sol),
        q("E203", "case2", ETL, ["unique_identifier", "concatenate"], 2.5, "Create LocationPlantID (e.g. USA-12). How many distinct LocationPlantID values are there?",
          num(df.LP.nunique(), 0), sol + " Then =COUNTA(UNIQUE(range)) or a PivotTable."),
        q("E204", "case2", ETL, ["unique_identifier", "pivot"], 2.5, "Which LocationPlantID has the most employees? Answer in the form ABC-12.",
          text(top_lp.index[0]), sol + " PivotTable on LocationPlantID, count, sort descending."),
        q("E205", "case2", ETL, ["text_functions", "value"], 2, "Extract EmpID as a number. What is the sum of all EmpID values?",
          num(int(df.Emp.sum()), 0), sol + " MID returns text: wrap it in VALUE before summing."),
        q("E206", "case2", ETL, ["text_functions", "countifs"], 2, "How many employees work at plant 12 in the USA (LocationPlantID = USA-12)?",
          num(int((df.LP == "USA-12").sum()), 0), sol),
        q("E207", "case2", ETL, ["text_functions", "lookup"], 1.5, "What is the PlantID of the employee with EmpID 1500?",
          num(int(df[df.Emp == 1500].Plant.iloc[0]), 0), sol + " Then filter or XLOOKUP on EmpID 1500."),
    ], mistakes)


def case3_questions(d):
    df = pd.read_excel(d / "ETL_Case3_employee_codes_messy.xlsx", sheet_name="Case 3 data")
    parts = df.EmployeeCode.map(split_case3)
    df["Loc"], df["Emp"], df["Plant"], df["Pay"], df["PayRaw"] = zip(*parts)
    df["LP"] = df.Loc + "-" + df.Plant.astype(str)
    sol = ("Location has 2–6 letters, so find where the digits start: e.g. first digit position "
           "=MIN(FIND({0,1,2,3,4,5,6,7,8,9},A2&\"0123456789\")); Location =LEFT(A2,pos-1); "
           "EmpID =VALUE(MID(A2,pos,FIND(\"-\",A2)-pos)); PlantID: digits after the hyphen (test ISNUMBER(VALUE(MID(...))) for a second digit); "
           "PayPeriod: letters at the end, normalise Mo→M and We→W with IF. Flash Fill also works for the split.")
    mistakes = {
        "E302": [(int((df.PayRaw == "M").sum()), "'Mo' also means monthly. Normalise M and Mo before counting.")],
        "E305": [(0, "MID returns text, and SUM ignores text: wrap the extraction in VALUE().")],
    }
    return with_mistakes([
        q("E301", "case3", ETL, ["text_functions", "messy_data"], 2, "How many employees work in Canada (location code 'Canada')?",
          num(int((df.Loc == "Canada").sum()), 0), sol),
        q("E302", "case3", ETL, ["text_functions", "messy_data"], 2.5, "After normalising M/Mo to monthly, how many employees are paid monthly?",
          num(int((df.Pay == "M").sum()), 0), sol),
        q("E303", "case3", ETL, ["text_functions", "messy_data"], 2, "How many EmployeeCodes record the monthly pay period with the two-letter variant 'Mo'?",
          num(int((df.PayRaw == "Mo").sum()), 0), sol),
        q("E304", "case3", ETL, ["unique_identifier", "messy_data"], 3.5, "Create LocationPlantID (e.g. US-3). How many distinct LocationPlantID values are there?",
          num(df.LP.nunique(), 0), sol),
        q("E305", "case3", ETL, ["text_functions", "value"], 3, "Extract EmpID as a number. What is the sum of all EmpID values?",
          num(int(df.Emp.sum()), 0), sol),
        q("E306", "case3", ETL, ["text_functions", "countifs"], 3, "How many employees have an EmpID greater than 300 and work in Japan?",
          num(int(((df.Emp > 300) & (df.Loc == "Japan")).sum()), 0), sol),
    ], mistakes)


# ---------------------------------------------------------------- ETL case 4
def case4_questions(d):
    x = pd.read_excel(d / "ETL_Case4_journal_entries.xlsx", sheet_name=None)
    je = x["JELineItems"].copy()
    coa = x["ChartOfAccounts"].iloc[:, :4].copy()
    prep = x["PreparerInfo"].copy()
    bu = x["BusinessUnits"]
    src = x["Source"].drop_duplicates("SourceID")
    je["GLn"] = je.GLAccountNumber.astype(str).str.strip()
    coa["GLn"] = coa.GLAccountNumber.astype(str).str.strip()
    m = (je.merge(coa[["GLn", "GLAccountName", "AccountType", "AccountClass"]], on="GLn", how="left")
           .merge(bu, on="BusinessUnitID", how="left")
           .merge(prep, on=["PreparerID", "BusinessUnitID"], how="left")
           .merge(src, on="SourceID", how="left"))
    assert len(m) == len(je)
    m["Prep"] = m.PreparerName.astype(str).str.split("|").str[0].str.strip()
    m["Debit"] = pd.to_numeric(m.Debit, errors="coerce").fillna(0)
    m["Credit"] = pd.to_numeric(m.Credit, errors="coerce").fillna(0)
    assert not m.AccountType.isna().any()
    cogs = int((m.GLAccountName.astype(str).str.strip() == "Cost of Goods Sold").sum())
    types = m.AccountType.dropna().astype(str).str.strip()
    rev_lines = int(types.str.lower().str.startswith("revenue").sum())
    sol_lookup = ("Build the flat file with lookups: =INDEX(BusinessUnits!B:B, MATCH(C2, BusinessUnits!A:A, 0)) (or XLOOKUP) for BusinessUnit; "
                  "the same for the chart of accounts and Source.")
    sol_prep = ("PreparerID is only unique together with BusinessUnitID: =INDEX(PreparerInfo!A:A, MATCH(D2&\"|\"&C2, PreparerInfo!B:B&\"|\"&PreparerInfo!C:C, 0)) "
                "as an array formula (or XLOOKUP with two conditions). The name is the text before '|'.")
    first = m.iloc[0]
    carolyn_units = prep[prep.PreparerName.astype(str).str.startswith("Carolyn Slater")]
    by_id_only = int(je.PreparerID.isin(carolyn_units.PreparerID).sum())
    mistakes = {
        "E403": [(by_id_only, "PreparerID alone is not unique: IDs restart in every business unit. Match on PreparerID and BusinessUnitID together.")],
        "E402": [(int(coa.AccountType.astype(str).str.strip().str.lower().eq("revenue").sum()),
                  "That is the number of revenue accounts in the chart. Count the journal lines that post to them.")],
        "E401": [(round(m[m.BusinessUnit == "HOTEL"].Amount.sum(), 2), "Use the Debit column only; Amount nets debits and credits.")],
    }
    return with_mistakes([
        q("E401", "journal", ETL, ["lookup", "sumifs"], 2.5, "What is the total of the Debit column for business unit HOTEL? Round to 2 decimals.",
          num(round(m[m.BusinessUnit == "HOTEL"].Debit.sum(), 2)), sol_lookup + ' Then =SUMIFS(Debit, BusinessUnit, "HOTEL").'),
        q("E402", "journal", ETL, ["lookup", "countifs"], 2.5, "How many journal entry line items post to accounts with AccountType Revenue?",
          num(rev_lines, 0), sol_lookup + " Look up AccountType from ChartOfAccounts and count."),
        q("E403", "journal", ETL, ["composite_key", "lookup"], 3, "How many line items were prepared by Carolyn Slater?",
          num(int((m.Prep == "Carolyn Slater").sum()), 0), sol_prep),
        q("E404", "journal", ETL, ["composite_key", "lookup"], 2.5, f"Who prepared the first line of journal entry {int(first.JENumber)}? Give the person's name only.",
          text(first.Prep), sol_prep),
        q("E405", "journal", ETL, ["lookup", "countifs"], 2, "How many line items have Source = PURCHASE CARD?",
          num(int((m.Source == "PURCHASE CARD").sum()), 0), sol_lookup),
        q("E406", "journal", ETL, ["lookup", "sumifs"], 2.5, "What is the total of the Credit column (as a negative number) for Source = PAYROLL JV? Round to 2 decimals.",
          num(round(m[m.Source == "PAYROLL JV"].Credit.sum(), 2)), sol_lookup),
        q("E407", "journal", ETL, ["distinct"], 1, "How many distinct journal entries (JENumber) are there?",
          num(je.JENumber.nunique(), 0), "=COUNTA(UNIQUE(A2:A790))"),
        q("E408", "journal", ETL, ["data_formats", "lookup"], 2.5,
          "Most GLAccountNumbers are numbers, but Cost of Goods Sold uses text codes (70300-FS, 70300-HP). How many line items post to Cost of Goods Sold?",
          num(cogs, 0), sol_lookup + " A numeric lookup value will not match a text key: make both sides text (e.g. =B2&\"\") before matching."),
        q("E409", "journal", ETL, ["lookup", "sumifs"], 2.5, "What is the total Amount posted to accounts whose AccountClass is Cash? Round to 2 decimals.",
          num(round(m[m.AccountClass.astype(str).str.strip() == "Cash"].Amount.sum(), 2)), sol_lookup),
        q("E410", "journal", ETL, ["validation"], 1, "Do the journal entries balance? Give the sum of the Amount column (rounded to 2 decimals).",
          num(round(je.Amount.sum(), 2)), "=ROUND(SUM(J2:J790),2): debits are positive and credits negative, so a balanced ledger sums to 0."),
    ], mistakes)


# ---------------------------------------------------------------- IntegrateCo
def job_code(job):
    m = re.match(r"\d{2}[HS]?(\d{3})", str(job))
    return m.group(1) if m else None


def payroll_questions(d):
    p15 = pd.read_csv(d / "IntegrateCo_2015payroll.csv", sep="|", dtype={"Job": str})
    p16 = pd.read_csv(d / "IntegrateCo_2016payroll.csv", sep="|", dtype={"Project": str})
    jobs = pd.read_csv(d / "IntegrateCo_jobcodes.csv", sep="|", dtype=str)
    loc = pd.read_csv(d / "IntegrateCo_locations.csv", sep="|")
    p15["Code"] = p15.Job.map(job_code)
    p16["Code"] = p16.Project.map(job_code)
    p15["Gross"] = p15.Reg_Pay + p15.OT_Pay
    p15["Name"] = p15.First_Name + " " + p15.Last_Name
    p15["Month"] = pd.to_datetime(p15.Pay_Date).dt.month
    g15 = p15.groupby("Code").Gross.sum()
    g16 = p16.groupby("Code").Gross_Wages.sum()
    both = (g16 - g15).dropna()
    valid = set(jobs.Job_Code)
    big_inc = both[both.index.isin(valid)].idxmax()
    phantom = p16[p16.Employee_Number.isna()]
    ot = p15.groupby("Name").OT_Pay.sum().sort_values(ascending=False)
    ot_job = p15[p15.Code.isin(valid)].groupby("Code").OT_Pay.sum().sort_values(ascending=False)
    cost16 = (p16.Gross_Wages + p16.SocSec_Medicare + p16.FUTA + p16.SUTA + p16.Work_Comp).sum()
    month = p15.groupby("Month").Gross.sum()
    per = p15.groupby(["Name", "Pay_Date"])[["Reg_Hrs", "OT_Hrs"]].sum()
    early_ot = int(((per.Reg_Hrs < 40) & (per.OT_Hrs > 0)).sum())
    m16 = p16.merge(loc, on="Employee_Name", how="left")
    hours_loc1 = (m16[m16.Location == 1].Hours + m16[m16.Location == 1].OT_Hours).sum()
    j1 = p16[p16.Code == "001"]
    rate001 = j1.Gross_Wages.sum() / (j1.Hours.sum() + j1.OT_Hours.sum())
    invalid15 = int((~p15.Code.isin(valid)).sum())
    pct_jan = month.loc[1] / month.sum()
    sol_code = ("Job code = the three digits after the 2-digit year and the optional H/S department letter: "
                "=MID(H2, IF(ISNUMBER(VALUE(MID(H2,3,1))), 3, 4), 3). Keep it as text so 001 stays 001.")
    ot_hint = "Include overtime: hours are Reg_Hrs + OT_Hrs (Hours + OT_Hours in 2016)."
    mistakes = {
        "I01": [(round(p15.Reg_Pay.sum(), 2), "Gross pay is Reg_Pay + OT_Pay; you only used regular pay.")],
        "I03": [(round(p15[p15.Code == "005"].Reg_Hrs.sum(), 2), ot_hint)],
        "I10": [(round(p16.Gross_Wages.sum(), 2), "Employee cost also includes SocSec_Medicare, FUTA, SUTA and Work_Comp.")],
        "I13": [(round(m16[m16.Location == 1].Hours.sum(), 2), ot_hint)],
        "I14": [(round(j1.Gross_Wages.sum() / j1.Hours.sum(), 2), ot_hint)],
        "I17": [(len(p15), "That counts rows. Each employee has many rows (one per job and pay date): count distinct Emp_No.")],
        "I06": [(round(p16.Gross_Wages.sum(), 2), "That is all 2016 wages. Keep only rows with a blank Employee_Number.")],
    }
    return with_mistakes([
        q("I01", "pay15", PAY, ["aggregate"], 1, "What was total gross pay (Reg_Pay + OT_Pay) in the first six months of 2015? Round to 2 decimals.",
          num(round(p15.Gross.sum(), 2)), "Import with Text to Columns (delimiter |), add Gross = K2+L2, =SUM."),
        q("I02", "pay16", PAY, ["aggregate"], 1, "What was total Gross_Wages in the first six months of 2016? Round to 2 decimals.",
          num(round(p16.Gross_Wages.sum(), 2)), "Import with delimiter |; =SUM(G:G)."),
        q("I03", "pay15", PAY, ["text_functions", "sumifs"], 3, "Total hours (Reg_Hrs + OT_Hrs) recorded on job code 005 (Installation) in 2015? Round to 2 decimals.",
          num(round((p15[p15.Code == "005"].Reg_Hrs + p15[p15.Code == "005"].OT_Hrs).sum(), 2)), sol_code + ' Then =SUMIFS on the new code column = "005".'),
        q("I04", "pay16", PAY, ["text_functions", "pivot"], 4,
          "Which job code had the largest increase in gross pay from 2015 to 2016? Give the three-digit code.",
          text(big_inc), sol_code + " Build a PivotTable per year by job code (2015 gross = Reg_Pay + OT_Pay) and subtract."),
        q("I05", "pay16", PAY, ["data_quality", "countblank"], 1.5, "How many 2016 rows have no employee number ('phantom' entries)?",
          num(len(phantom), 0), "Filter Employee_Number on (Blanks), or =COUNTBLANK(C2:C805)."),
        q("I06", "pay16", PAY, ["data_quality", "sumifs"], 2, "What is the total Gross_Wages of the 2016 phantom entries (no employee number)? Round to 2 decimals.",
          num(round(phantom.Gross_Wages.sum(), 2)), '=SUMIFS(G:G, C:C, "")'),
        q("I07", "pay15", PAY, ["concatenate", "pivot"], 2.5, "Which employee earned the most overtime pay in 2015? Give 'First Last'.",
          text(ot.index[0]), "Combine names with =F2&\" \"&G2; PivotTable of OT_Pay by name, sort descending."),
        q("I08", "pay15", PAY, ["concatenate", "pivot"], 2.5, "How much overtime pay did the top overtime earner receive in 2015? Round to 2 decimals.",
          num(round(ot.iloc[0], 2)), "PivotTable of OT_Pay by employee name, sorted descending."),
        q("I09", "pay15", PAY, ["text_functions", "pivot"], 3, "Which valid job code (001–012) had the most overtime pay in 2015? Give the three-digit code.",
          text(ot_job.index[0]), sol_code + " PivotTable OT_Pay by job code."),
        q("I10", "pay16", PAY, ["expression", "aggregate"], 1.5,
          "Total 2016 employee cost = Gross_Wages + SocSec_Medicare + FUTA + SUTA + Work_Comp. Round to 2 decimals.",
          num(round(cost16, 2)), "=SUM(G:K) over the cost columns."),
        q("I11", "pay15", PAY, ["date", "pivot"], 2, "In which month of 2015 (1–6) was gross pay highest?",
          num(int(month.idxmax()), 0), "Month =MONTH(A2) (after the text dates are recognised as dates), PivotTable of gross pay by month."),
        q("I12", "pay15", PAY, ["group_by", "logic"], 4,
          "Treat all pay on the same Pay_Date as one pay period. For how many employee–pay date combinations was overtime recorded although regular hours were below 40?",
          num(early_ot, 0), "PivotTable with Name and Pay_Date in Rows, sum of Reg_Hrs and OT_Hrs; then count rows with Reg < 40 and OT > 0 (COUNTIFS on a copied value table)."),
        q("I13", "pay16", PAY, ["lookup", "sumifs"], 3, "Using the locations file, what were the total 2016 hours (Hours + OT_Hours) of employees at location 1? Round to 2 decimals.",
          num(round(hours_loc1, 2)), "Import the locations file (| delimited), =XLOOKUP(D2, Locations!A:A, Locations!B:B) on Employee_Name, then SUMIFS."),
        q("I14", "pay16", PAY, ["text_functions", "ratio"], 3,
          "What was the 2016 gross pay per hour for job code 001 (Gross_Wages / (Hours + OT_Hours))? Round to 2 decimals.",
          num(round(rate001, 2)), sol_code + " Then SUMIFS of wages divided by SUMIFS of hours."),
        q("I15", "pay15", PAY, ["data_quality", "text_functions"], 3,
          "How many 2015 rows have a job code outside the valid range 001–012?",
          num(invalid15, 0), sol_code + " Then =COUNTIF on a check column such as =ISNA(MATCH(code, JobCodes!A:A, 0))."),
        q("I16", "pay15", PAY, ["date", "percentage"], 2.5,
          "What percentage of the first-half 2015 gross pay was paid in January? Answer in percent with 2 decimals.",
          num(round(pct_jan * 100, 2), 0.02), "Gross pay by month (PivotTable), January divided by the six-month total."),
        q("I17", "pay15", PAY, ["distinct"], 1, "How many distinct employees (Emp_No) were paid in 2015?",
          num(p15.Emp_No.nunique(), 0), "=COUNTA(UNIQUE(C2:C4982))"),
        q("I18", "pay15", PAY, ["distinct"], 1, "How many separate payroll runs (distinct Payroll_ID) were there in 2015?",
          num(p15.Payroll_ID.nunique(), 0), "=COUNTA(UNIQUE(B2:B4982))"),
    ], mistakes)


# ---------------------------------------------------------------- workbook column tasks
# The student builds the columns in Excel and uploads the workbook; the site finds
# each column (any sheet, any position, any header) and reconciles its values.
# These tasks are practice-only, so the exam draw is not affected.
def col(name, values, mistakes=()):
    return dict(name=name, values=list(values), mistakes=[(list(v), hint) for v, hint in mistakes])


def column_task(id, file, course, topics, minutes, prompt, columns, solution):
    return dict(id=id, file=file, subject="Excel", course=course, topics=topics, minutes=minutes, prompt=prompt,
                practiceOnly=True, check=dict(type="columns", columns=columns), solution=solution)


def column_tasks(d):
    c2 = pd.read_excel(d / "ETL_Case2_employee_codes.xlsx", sheet_name="Case 2")
    loc2, emp2, plant2, pay2 = zip(*c2.EmployeeCode.map(split_case2))
    lp2 = [f"{a}-{b}" for a, b in zip(loc2, plant2)]

    c3 = pd.read_excel(d / "ETL_Case3_employee_codes_messy.xlsx", sheet_name="Case 3 data")
    loc3, emp3, plant3, pay3, raw3 = zip(*c3.EmployeeCode.map(split_case3))
    lp3 = [f"{a}-{b}" for a, b in zip(loc3, plant3)]

    x = pd.read_excel(d / "ETL_Case4_journal_entries.xlsx", sheet_name=None)
    je = x["JELineItems"].copy()
    coa = x["ChartOfAccounts"].iloc[:, :4].copy()
    bu = x["BusinessUnits"]
    src = x["Source"].drop_duplicates("SourceID")
    je["GLk"] = je.GLAccountNumber.astype(str).str.strip()
    coa["GLk"] = coa.GLAccountNumber.astype(str).str.strip()
    # PreparerName is left out: 148 lines have a PreparerID/BusinessUnitID pair that is not in
    # PreparerInfo, and the case does not say what the flat file should show for them.
    m = (je.merge(coa[["GLk", "GLAccountName", "AccountType", "AccountClass"]], on="GLk", how="left")
           .merge(bu[["BusinessUnitID", "BusinessUnit"]], on="BusinessUnitID", how="left")
           .merge(src, on="SourceID", how="left"))
    assert len(m) == len(je) and not m[["GLAccountName", "Source", "BusinessUnit"]].isna().any().any()
    gl_numeric_only = [n if str(k).isdigit() else "#N/A" for n, k in zip(m.GLAccountName, m.GLk)]

    p15 = pd.read_csv(d / "IntegrateCo_2015payroll.csv", sep="|", dtype={"Job": str})
    p16 = pd.read_csv(d / "IntegrateCo_2016payroll.csv", sep="|", dtype={"Project": str})
    code15, code16 = p15.Job.map(job_code), p16.Project.map(job_code)
    fixed_mid = "Not every code has a department letter: =MID(Job,3,3) breaks on codes like 14H002. Start at position 4 when the third character is a letter."

    upload = " Then upload your workbook (.xlsx) here."
    formulas = " Use formulas so the template is repeatable."
    return [
        column_task("X201", "case2", ETL, ["text_functions", "unique_identifier", "workbook"], 8,
                    "Split EmployeeCode into Location, EmpID, PlantID and PayPeriod, and build LocationPlantID (e.g. USA-12) for all 597 employees." + formulas + upload,
                    [col("Location", loc2), col("EmpID", emp2),
                     col("PlantID", plant2, [([f"{p}{q}" for p, q in zip(plant2, pay2)], "Your PlantID still contains the pay-period letter. Take only the digits between the hyphen and the last letter.")]),
                     col("PayPeriod", pay2),
                     col("LocationPlantID", lp2, [([f"{a}{b}" for a, b in zip(loc2, plant2)], "Join Location and PlantID with a hyphen: USA-12, not USA12.")])],
                    "LEFT for Location, MID for EmpID, MID with FIND(\"-\") for PlantID, RIGHT for PayPeriod, then Location&\"-\"&PlantID."),
        column_task("X301", "case3", ETL, ["text_functions", "messy_data", "workbook"], 12,
                    "The messy codes: split EmployeeCode into Location, EmpID, PlantID and PayPeriod (normalised to M or W), and build LocationPlantID (e.g. US-3) for all 597 employees." + formulas + upload,
                    [col("Location", loc3, [([str(c)[:3] for c in c3.EmployeeCode], "Location codes are not always three characters here (US, Canada, Japan). Take the letters before the first digit.")]),
                     col("EmpID", emp3), col("PlantID", plant3),
                     col("PayPeriod", pay3, [(raw3, "Normalise the pay period: Mo means M and We means W.")]),
                     col("LocationPlantID", lp3)],
                    "Find the first digit with MIN(FIND({0,…,9}, code&\"0123456789\")); LEFT before it is the Location, MID up to the hyphen is EmpID; normalise the pay period with IF."),
        column_task("X401", "journal", ETL, ["lookup", "composite_key", "workbook"], 12,
                    "Build the flat file: for every journal entry line add BusinessUnit, GLAccountName, AccountType, AccountClass and Source." + formulas + upload,
                    [col("BusinessUnit", m.BusinessUnit),
                     col("GLAccountName", m.GLAccountName, [(gl_numeric_only, "Two Cost of Goods Sold accounts use text codes (70300-FS, 70300-HP), so a numeric lookup returns #N/A. Make both sides text before matching.")]),
                     col("AccountType", m.AccountType), col("AccountClass", m.AccountClass),
                     col("Source", m.Source)],
                    "INDEX/MATCH or XLOOKUP into each master tab (BusinessUnits, ChartOfAccounts, Source); GLAccountNumber mixes numbers and text codes."),
        column_task("X501", "payroll", PAY, ["text_functions", "expression", "workbook"], 8,
                    "In the 2015 payroll, add JobCode (the three-digit job code from Job) and GrossPay (Reg_Pay + OT_Pay) for every row." + upload,
                    [col("JobCode", code15, [(p15.Job.str[2:5], fixed_mid)]),
                     col("GrossPay", (p15.Reg_Pay + p15.OT_Pay).round(2), [(p15.Reg_Pay, "Gross pay is Reg_Pay + OT_Pay; you only used regular pay.")])],
                    "JobCode =MID(H2, IF(ISNUMBER(VALUE(MID(H2,3,1))), 3, 4), 3) kept as text; GrossPay =K2+L2."),
        column_task("X502", "payroll", PAY, ["text_functions", "workbook"], 5,
                    "In the 2016 payroll, add JobCode: the three-digit job code taken from Project, for every row." + upload,
                    [col("JobCode", code16, [(p16.Project.str[2:5], fixed_mid)])],
                    "Same rule as 2015: =MID(A2, IF(ISNUMBER(VALUE(MID(A2,3,1))), 3, 4), 3)."),
    ]


def build(files_dir):
    return (film_questions(files_dir) + case1_questions(files_dir) + case2_questions(files_dir)
            + case3_questions(files_dir) + case4_questions(files_dir) + payroll_questions(files_dir)
            + column_tasks(files_dir))
