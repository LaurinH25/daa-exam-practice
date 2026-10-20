"""Typical wrong approaches to the SQL questions, tied to the traps in the cases.

The build runs each variant on the real database and stores a fingerprint of
its result. If a student's result matches one exactly, the site shows the hint.
Variants that happen to give the correct result on this data are dropped.
"""

BOUNDARY = "Check the boundary: 'greater than' excludes the limit itself, 'or more' includes it."
REFUNDS = "Your result includes refunds. In the P-card data returns are negative amounts (Amount < 0)."
YEAR_2014 = "Your result covers every year. The question only asks about calendar year 2014."
DISTINCT_PEOPLE = "Some people appear more than once (once per movie). Return each person only once."

MISTAKES = {
    "C02": [("SELECT COUNT(*) FROM Invoice WHERE Total >= 20", BOUNDARY)],
    "C03": [("SELECT COUNT(*) FROM Invoice WHERE Total BETWEEN 10 AND 20",
             "BETWEEN includes both limits; the question says greater than 10 and less than 20.")],
    "C05": [("SELECT COUNT(*) FROM Invoice WHERE BillingCountry LIKE '%C%'",
             "'%C%' finds a C anywhere in the name. 'Starts with C' is 'C%'.")],
    "C06": [("SELECT COUNT(*) FROM Customer", "You counted every customer. Keep only rows where Company IS NOT NULL."),
            ("SELECT COUNT(*) FROM Customer WHERE Company = NULL", "Nothing equals NULL, not even NULL. Use IS NULL / IS NOT NULL.")],
    "C09": [("SELECT COUNT(*) FROM Employee WHERE STRFTIME('%w', BirthDate) = '7'", "STRFTIME('%w') numbers the days 0–6 with Sunday = 0."),
            ("SELECT COUNT(*) FROM Employee WHERE STRFTIME('%w', BirthDate) = '1'", "STRFTIME('%w') numbers the days 0–6 with Sunday = 0 (1 is Monday).")],
    "C13": [("SELECT COUNT(UnitPrice) FROM InvoiceLine", "COUNT(UnitPrice) counts every line. Use COUNT(DISTINCT UnitPrice)."),
            ("SELECT COUNT(DISTINCT UnitPrice) FROM Track", "That is the price list of the catalogue (Track). The question asks about InvoiceLine.")],
    "C17": [("SELECT g.Name, COUNT(*) AS n FROM Track t JOIN Genre g ON g.GenreId = t.GenreId GROUP BY g.Name ORDER BY n DESC LIMIT 1",
             "You counted tracks in the catalogue. Popularity here means sold lines in InvoiceLine.")],
    "C18": [("SELECT COUNT(TrackId) FROM InvoiceLine", "That counts lines, not tracks. Use COUNT(DISTINCT TrackId).")],
    "C19": [("SELECT Country, COUNT(*) AS n FROM Customer GROUP BY Country HAVING COUNT(*) >= 3 ORDER BY n DESC, Country", BOUNDARY)],
    "C21": [("SELECT COUNT(*) FROM Track t JOIN InvoiceLine il ON il.TrackId = t.TrackId WHERE il.InvoiceLineId IS NULL",
             "An inner join drops the unsold tracks before you can find them. Use a LEFT JOIN."),
            ("SELECT COUNT(*) FROM Track t LEFT JOIN InvoiceLine il ON il.TrackId = t.TrackId",
             "You counted all joined rows. Keep only tracks without a match: WHERE il.InvoiceLineId IS NULL.")],
    "C28": [("SELECT COUNT(*) FROM Invoice WHERE Total >= (SELECT AVG(Total) FROM Invoice)", BOUNDARY)],
    "S04": [("SELECT name FROM songs WHERE danceability > 0.6 OR energy > 0.6 OR valence > 0.6",
             "All three conditions must hold: use AND, not OR.")],
    "S09": [("SELECT a.name, COUNT(*) AS n FROM songs s JOIN artists a ON a.id = s.artist_id GROUP BY a.id HAVING COUNT(*) >= 2 ORDER BY n DESC, a.name", BOUNDARY)],
    "M04": [("SELECT COUNT(*) FROM ratings WHERE rating >= 9.0", BOUNDARY)],
    "M09": [("SELECT name FROM people JOIN stars ON stars.person_id = people.id JOIN movies ON movies.id = stars.movie_id WHERE year = 2003", DISTINCT_PEOPLE)],
    "M10": [("SELECT name FROM people JOIN directors ON directors.person_id = people.id JOIN ratings ON ratings.movie_id = directors.movie_id WHERE rating >= 9.0", DISTINCT_PEOPLE),
            ("SELECT name FROM people WHERE id IN (SELECT person_id FROM directors JOIN ratings ON ratings.movie_id = directors.movie_id WHERE rating > 9.0)", BOUNDARY)],
    "M13": [("SELECT name FROM people WHERE id IN (SELECT person_id FROM stars WHERE movie_id IN (SELECT movie_id FROM stars WHERE person_id = "
             "(SELECT id FROM people WHERE name = 'Kevin Bacon' AND birth = 1958)))",
             "Kevin Bacon himself should not be in the list."),
            ("SELECT name FROM people WHERE id IN (SELECT person_id FROM stars WHERE movie_id IN (SELECT movie_id FROM stars WHERE person_id IN "
             "(SELECT id FROM people WHERE name = 'Kevin Bacon'))) AND name <> 'Kevin Bacon'",
             "There is more than one Kevin Bacon in the database. Use only the one born in 1958.")],
    "P02": [("SELECT COUNT(*) FROM pcards WHERE Amount > 5000", BOUNDARY)],
    "P03": [("SELECT ROUND(SUM(Amount), 2) FROM pcards WHERE Year = 2014 AND Month BETWEEN 1 AND 3",
             "That is all Q1 spending. Returns are only the negative amounts (Amount < 0)."),
            ("SELECT ROUND(-SUM(Amount), 2) FROM pcards WHERE Year = 2014 AND Month BETWEEN 1 AND 3 AND Amount < 0",
             "Right transactions, but report the total as it is recorded (returns are negative).")],
    "P05": [("SELECT FullName, COUNT(*) AS n FROM pcards WHERE Year = 2014 GROUP BY FullName HAVING COUNT(*) >= 10 ORDER BY n DESC, FullName", BOUNDARY),
            ("SELECT FullName, COUNT(*) AS n FROM pcards GROUP BY FullName HAVING COUNT(*) > 10 ORDER BY n DESC, FullName", YEAR_2014)],
    "P06": [("SELECT FullName, ROUND(SUM(Amount), 2) AS v, COUNT(*) FROM pcards WHERE Year = 2014 AND Amount < 0 GROUP BY FullName HAVING -SUM(Amount) > 1000 ORDER BY v",
             "Report ReturnedGoodsValue as a positive number (e.g. -SUM(Amount) or ABS)."),
            ("SELECT FullName, ROUND(-SUM(Amount), 2) AS v, COUNT(*) FROM pcards WHERE Amount < 0 GROUP BY FullName HAVING -SUM(Amount) > 1000 ORDER BY v DESC", YEAR_2014)],
    "P08": [("SELECT Year, ROUND(SUM(Amount), 2), ROUND(SUM(Amount) * 1.045, 2) FROM pcards GROUP BY Year ORDER BY Year DESC",
             "SalesTaxSaved is the tax itself (total × 0.045), not the total including tax.")],
    "P09": [("SELECT Year, ROUND(SUM(Amount) * 0.3 * 0.045, 2) FROM pcards GROUP BY Year ORDER BY Year DESC",
             "OSU pays tax on 30% of purchases, so it saves tax on the other 70%.")],
    "P10": [("SELECT CASE WHEN Amount >= 1000 THEN 'High' WHEN Amount >= 500 THEN 'Medium' ELSE 'Low' END AS r, COUNT(*) FROM pcards WHERE Year = 2014 AND Amount < 0 GROUP BY r",
             "Returns are negative, so Amount >= 1000 is never true for them. Compare -Amount (or ABS(Amount)).")],
    "P11": [("SELECT ROUND(SUM(CASE WHEN Amount >= 500 THEN Amount * 0.0075 ELSE Amount * 0.005 END), 2) FROM pcards WHERE Year = 2014 AND UPPER(Vendor) LIKE '%AMAZON%'", REFUNDS),
            ("SELECT ROUND(SUM(CASE WHEN Amount >= 500 THEN Amount * 0.75 ELSE Amount * 0.5 END), 2) FROM pcards WHERE Year = 2014 AND Amount > 0 AND UPPER(Vendor) LIKE '%AMAZON%'",
             "0.75% is 0.0075 as a multiplier, not 0.75.")],
    "P12": [("SELECT COUNT(*) FROM pcards WHERE Year = 2014 AND Amount > (SELECT AVG(Amount) FROM pcards)",
             "Compare with the 2014 average, not the average over all years.")],
    "P13": [("SELECT FullName, ROUND(SUM(Amount), 2) AS t FROM pcards GROUP BY FullName HAVING SUM(Amount) > 50000 ORDER BY t DESC", YEAR_2014)],
    "P15": [("SELECT COUNT(*) FROM pcards WHERE Year = 2014 AND Amount >= 5000", BOUNDARY),
            ("SELECT COUNT(*) FROM pcards WHERE Amount > 5000", YEAR_2014)],
    "P17": [("SELECT COUNT(*) FROM (SELECT 1 FROM pcards WHERE Year = 2014 GROUP BY TransactionDate, Vendor, FullName, Amount HAVING COUNT(*) >= 2)", REFUNDS),
            ("SELECT SUM(n) FROM (SELECT COUNT(*) n FROM pcards WHERE Year = 2014 AND Amount > 0 GROUP BY TransactionDate, Vendor, FullName, Amount HAVING COUNT(*) >= 2)",
             "You counted the transactions. The question asks for the number of duplicate groups.")],
    "P19": [("SELECT SUBSTR(CAST(Amount AS TEXT), 1, 1) AS d, ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM pcards WHERE Year = 2014), 3) FROM pcards "
             "WHERE Year = 2014 AND Amount >= 1 GROUP BY d ORDER BY d",
             "Use the same population in the denominator: only 2014 transactions with Amount ≥ 1.")],
    "P22": [("SELECT Year, ROUND((COUNT(*) - (SELECT COUNT(*) FROM pcards WHERE Year = 2010)) * 100.0 / (SELECT COUNT(*) FROM pcards WHERE Year = 2010), 2) "
             "FROM pcards WHERE Year IN (2012, 2013, 2014) GROUP BY Year ORDER BY Year",
             "The base year is 2011, not 2010."),
            ("SELECT Year, ROUND((COUNT(*) - (SELECT COUNT(*) FROM pcards WHERE Year = 2011)) / (SELECT COUNT(*) FROM pcards WHERE Year = 2011) * 100, 2) "
             "FROM pcards WHERE Year IN (2012, 2013, 2014) GROUP BY Year ORDER BY Year",
             "Integer division: COUNT(*) / COUNT(*) is a whole number in SQLite. Multiply by 100.0 first.")],
    "P25": [("SELECT COUNT(FullName) FROM pcards WHERE Year = 2014", "That counts transactions. Use COUNT(DISTINCT FullName).")],
}
