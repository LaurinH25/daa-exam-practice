"""Data interpretation (regression) exams.

Each exam has four questions, mirroring the restaurant case: a prediction, a
single-variable interpretation, a squared term and an interaction. The two
restaurant exams use models fitted on the course data (Larry's Commissary);
the other contexts use synthetic teaching coefficients in accounting settings.
Model answers are generated from the coefficients so they always match them.
"""
import warnings

import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
ALPHA = 0.05


def fmt(v, d=2):
    s = f"{v:,.{d}f}".rstrip("0").rstrip(".") if d else f"{v:,.0f}"
    return s if s not in ("-0", "") else "0"


def pfmt(p):
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def sig(p):
    return (f"The p-value ({pfmt(p)}) is below 0.05, so the coefficient is statistically significant at the 5% level: "
            "we reject the null hypothesis that the true coefficient is zero."
            if p < ALPHA else
            f"The p-value ({pfmt(p)}) is above 0.05, so the coefficient is not statistically significant at the 5% level: "
            "we cannot rule out that the true coefficient is zero (the effect could be due to chance).")


def coef_table(names, est, ps):
    return [dict(term=n, est=e, p=p) for n, e, p in zip(names, est, ps)]


def make_exam(c):
    """c: context spec. Returns an exam dict with 4 questions and model answers."""
    y, yu = c["y"]
    x, xu, xrange = c["x"]
    dname, d1, d0 = c["dummy"]
    qs = []

    # 1. Prediction with continuous + dummy
    b0, b1, b2 = c["P"]["coefs"]
    xv, dv = c["P"]["at"]
    pred = b0 + b1 * xv + b2 * dv
    qs.append(dict(
        id=c["id"] + "-P", kind="prediction",
        equation=f"Predicted {y} = b0 + b1·[{x}] + b2·[{dname}]",
        coefs=coef_table(["Intercept", x, dname], [b0, b1, b2], c["P"]["p"]),
        prompt=f"Predict {y} ({yu}) when {x} = {fmt(xv)} {xu} for {d1 if dv else d0}.",
        answer=dict(type="number", value=round(pred, 4), tol=max(abs(pred) * 0.005, 0.01)),
        model=(f"Insert the values: {fmt(b0)} + {fmt(b1, 4)} × {fmt(xv)} + {fmt(b2)} × {dv} = {fmt(pred)} {yu}. "
               f"{dname} is a dummy, so it enters as {dv} ({d1 if dv else d0})."),
        points=["Uses every coefficient, including the intercept",
                f"Codes the dummy correctly as {dv}",
                f"Gets {fmt(pred)} {yu} and states the unit"],
    ))

    # 2. Single variable: continuous slope or dummy difference
    a0, a1 = c["S"]["coefs"]
    pa0, pa1 = c["S"]["p"]
    if c["S"]["kind"] == "continuous":
        eq = f"Predicted {y} = a0 + a1·[{x}]"
        names = ["Intercept", x]
        direction = "higher" if a1 > 0 else "lower"
        lo, hi = xrange
        icpt = (f"The intercept ({fmt(a0)}) is the predicted {y} when {x} is 0"
                + (f"; 0 lies outside the range of the data ({fmt(lo)}–{fmt(hi)} {xu}), so it is an extrapolation with little practical meaning."
                   if lo > 0 else "."))
        model = (f"Each additional {xu.rstrip('s') if xu.endswith('s') else xu} of {x} is associated with a {fmt(abs(a1), 4)} {yu} {direction} {y} on average. "
                 f"{sig(pa1)} {icpt} This is an association, not proof of causation.")
        prompt = f"Interpret the coefficient on {x}, including its p-value."
        points = ["Gives size, direction and unit of the slope", "Uses the p-value correctly (5% level)", "Avoids a causal claim"]
    else:
        eq = f"Predicted {y} = a0 + a1·[{dname}]"
        names = ["Intercept", dname]
        direction = "higher" if a1 > 0 else "lower"
        model = (f"The intercept ({fmt(a0)}) is the average {y} for the reference group, {d0}. "
                 f"The coefficient a1 means {d1} have on average {fmt(abs(a1))} {yu} {direction} {y} than {d0} "
                 f"(predicted {fmt(a0 + a1)} vs {fmt(a0)}). {sig(pa1)}")
        prompt = f"Interpret both coefficients of this model."
        points = ["Intercept = mean of the reference group", "Dummy = difference between the groups, with direction and unit", "Uses the p-value correctly"]
    qs.append(dict(id=c["id"] + "-S", kind=c["S"]["kind"], equation=eq,
                   coefs=coef_table(names, [a0, a1], [pa0, pa1]), prompt=prompt, model=model, points=points))

    # 3. Squared term
    c0, c1, c2 = c["Q"]["coefs"]
    pq = c["Q"]["p"]
    turn = -c1 / (2 * c2)
    shape = "an inverted U (concave)" if c2 < 0 else "a U shape (convex)"
    extreme = "maximum" if c2 < 0 else "minimum"
    base = (f"The squared term ({fmt(c2, 4)}) is {'negative' if c2 < 0 else 'positive'}, so the relationship has {shape}: "
            f"the effect of one more unit of {x} gets {'smaller' if c2 < 0 else 'larger'} as {x} increases. ")
    if c["Q"]["ask"] == "turning":
        qs.append(dict(
            id=c["id"] + "-Q", kind="quadratic",
            equation=f"Predicted {y} = c0 + c1·[{x}] + c2·[{x}]²",
            coefs=coef_table(["Intercept", x, f"{x}²"], [c0, c1, c2], pq),
            prompt=f"At what value of {x} ({xu}) is predicted {y} at its {extreme}? Round to 2 decimals.",
            answer=dict(type="number", value=round(turn, 4), tol=max(abs(turn) * 0.005, 0.01)),
            model=base + f"The {extreme} is where the slope c1 + 2·c2·{x} equals zero: {x} = −c1 / (2·c2) = −{fmt(c1, 4)} / (2 × {fmt(c2, 4)}) = {fmt(turn)} {xu}."
                  + (f" Note this lies outside the data range ({fmt(xrange[0])}–{fmt(xrange[1])}), so treat it with caution." if not xrange[0] <= turn <= xrange[1] else ""),
            points=["Recognises the sign of the squared term", "Uses −c1 / (2·c2)", f"Gets {fmt(turn)} {xu}"],
        ))
    else:
        qs.append(dict(
            id=c["id"] + "-Q", kind="quadratic",
            equation=f"Predicted {y} = c0 + c1·[{x}] + c2·[{x}]²",
            coefs=coef_table(["Intercept", x, f"{x}²"], [c0, c1, c2], pq),
            prompt=f"What do you learn from the coefficient and p-value of the {x}² term?",
            model=base + sig(pq[2]) + (" So the data support a curved rather than a straight-line relationship."
                                       if pq[2] < ALPHA else " So the data do not clearly support a curve; a straight line may be adequate."),
            points=["Interprets the sign as curvature", "Uses the p-value of the squared term", "Concludes whether the relationship is non-linear"],
        ))

    # 4. Interaction
    d0_, d1_, d2_, d3_ = c["I"]["coefs"]
    pi = c["I"]["p"]
    model = (f"d0 ({fmt(d0_)}): predicted {y} for {d0} when {x} = 0. "
             f"d1 ({fmt(d1_, 4)}): for {d0}, each additional unit of {x} ({xu}) is associated with {fmt(d1_, 4)} {yu} change in {y}. {sig(pi[1])} "
             f"d2 ({fmt(d2_)}): the difference between {d1} and {d0} when {x} = 0. {sig(pi[2])} "
             f"d3 ({fmt(d3_, 4)}): how much the slope of {x} differs for {d1}; their slope is d1 + d3 = {fmt(d1_ + d3_, 4)} {yu} per unit. {sig(pi[3])}")
    qs.append(dict(
        id=c["id"] + "-I", kind="interaction",
        equation=f"Predicted {y} = d0 + d1·[{x}] + d2·[{dname}] + d3·([{x}]×[{dname}])",
        coefs=coef_table(["Intercept", x, dname, f"{x}×{dname}"], [d0_, d1_, d2_, d3_], pi),
        prompt=f"Interpret all four coefficients in context, including their p-values.",
        model=model,
        points=["Intercept refers to the reference group at 0", "d1 is the slope for the reference group only",
                "d2 is the group difference at 0", "d3 is the change in slope; slope for the other group = d1 + d3",
                "Uses p-values for d1, d2, d3"],
    ))
    return dict(id=c["id"], title=c["title"], context=c["context"], real=c.get("real", False),
                variables=c["variables"], questions=qs)


SYNTHETIC = [
    dict(id="REG03", title="Hotel conference revenue",
         context="A hotel and conference centre (like the one in ETL Case 4) studies daily food-service revenue.",
         y=("daily revenue", "thousand DKK"), x=("occupancy", "percentage points", (20, 100)),
         dummy=("Conference day", "conference days", "days without a conference"),
         variables={"daily revenue": "food-service revenue (thousand DKK)", "occupancy": "share of rooms occupied (0–100 %)",
                    "Conference day": "1 = a conference is held, 0 = no conference"},
         P=dict(coefs=[12.5, 0.42, 18.0], p=[0.004, 0.001, 0.002], at=(70, 1)),
         S=dict(kind="continuous", coefs=[15.2, 0.38], p=[0.010, 0.003]),
         Q=dict(coefs=[-4.0, 1.30, -0.0075], p=[0.42, 0.001, 0.006], ask="turning"),
         I=dict(coefs=[11.0, 0.40, 9.5, 0.15], p=[0.020, 0.001, 0.180, 0.041])),
    dict(id="REG04", title="IntegrateCo overtime",
         context="IntegrateCo examines weekly overtime pay per employee after the system change.",
         y=("overtime pay", "USD per week"), x=("regular hours", "hours", (0, 40)),
         dummy=("Installation job", "installation employees", "other employees"),
         variables={"overtime pay": "overtime pay per employee and week (USD)", "regular hours": "regular hours worked that week (0–40)",
                    "Installation job": "1 = job code 005 Installation, 0 = other job codes"},
         P=dict(coefs=[-35.0, 3.1, 48.0], p=[0.06, 0.001, 0.012], at=(38, 1)),
         S=dict(kind="dummy", coefs=[61.0, 44.5], p=[0.001, 0.027]),
         Q=dict(coefs=[20.0, -2.4, 0.11], p=[0.30, 0.04, 0.003], ask="pvalue"),
         I=dict(coefs=[-30.0, 2.8, 12.0, 1.1], p=[0.09, 0.002, 0.55, 0.21])),
    dict(id="REG05", title="P-card monthly spend",
         context="OSU internal audit models the monthly P-card spend of a department.",
         y=("monthly spend", "thousand USD"), x=("cardholders", "cardholders", (1, 40)),
         dummy=("Fiscal year-end month", "June (fiscal year-end)", "other months"),
         variables={"monthly spend": "total P-card spend in the month (thousand USD)", "cardholders": "number of active cardholders",
                    "Fiscal year-end month": "1 = June, the last month of OSU's fiscal year, 0 = other months"},
         P=dict(coefs=[3.2, 1.85, 9.4], p=[0.11, 0.001, 0.004], at=(12, 1)),
         S=dict(kind="continuous", coefs=[4.1, 1.9], p=[0.05, 0.001]),
         Q=dict(coefs=[1.5, 2.6, -0.021], p=[0.52, 0.001, 0.38], ask="pvalue"),
         I=dict(coefs=[3.0, 1.8, 2.5, 0.42], p=[0.15, 0.001, 0.47, 0.012])),
    dict(id="REG06", title="Film shoots and weather",
         context="New York's film office relates weekly shooting permits to the weather.",
         y=("weekly permits", "permits"), x=("temperature", "°C", (-5, 32)),
         dummy=("Holiday week", "holiday weeks", "regular weeks"),
         variables={"weekly permits": "number of shooting permits starting that week", "temperature": "average weekly temperature (°C)",
                    "Holiday week": "1 = week contains a public holiday, 0 = otherwise"},
         P=dict(coefs=[118.0, 2.6, -21.0], p=[0.001, 0.002, 0.031], at=(18, 0)),
         S=dict(kind="dummy", coefs=[152.0, -24.0], p=[0.001, 0.068]),
         Q=dict(coefs=[105.0, 6.4, -0.14], p=[0.001, 0.001, 0.004], ask="turning"),
         I=dict(coefs=[120.0, 2.5, -12.0, -0.9], p=[0.001, 0.003, 0.29, 0.44])),
    dict(id="REG07", title="Audit fees",
         context="An audit firm explains audit fees with client size.",
         y=("audit fee", "thousand EUR"), x=("total assets", "million EUR", (5, 500)),
         dummy=("Listed client", "listed clients", "unlisted clients"),
         variables={"audit fee": "audit fee (thousand EUR)", "total assets": "client's total assets (million EUR)",
                    "Listed client": "1 = shares listed on a stock exchange, 0 = unlisted"},
         P=dict(coefs=[22.0, 0.31, 35.0], p=[0.001, 0.001, 0.008], at=(120, 1)),
         S=dict(kind="continuous", coefs=[30.5, 0.29], p=[0.001, 0.001]),
         Q=dict(coefs=[15.0, 0.52, -0.0004], p=[0.02, 0.001, 0.009], ask="turning"),
         I=dict(coefs=[25.0, 0.27, 12.0, 0.08], p=[0.001, 0.001, 0.32, 0.027])),
    dict(id="REG08", title="Invoice processing time",
         context="An accounts-payable team measures how long it takes to process supplier invoices.",
         y=("processing time", "minutes"), x=("line items", "line items", (1, 60)),
         dummy=("Manual entry", "manually entered invoices", "electronically received invoices"),
         variables={"processing time": "minutes from receipt to approval", "line items": "number of lines on the invoice",
                    "Manual entry": "1 = keyed in manually, 0 = received electronically (e-invoice)"},
         P=dict(coefs=[4.5, 0.65, 11.0], p=[0.002, 0.001, 0.001], at=(14, 1)),
         S=dict(kind="dummy", coefs=[9.8, 13.6], p=[0.001, 0.001]),
         Q=dict(coefs=[5.0, 0.4, 0.006], p=[0.01, 0.003, 0.048], ask="pvalue"),
         I=dict(coefs=[4.0, 0.35, 6.5, 0.48], p=[0.004, 0.002, 0.041, 0.001])),
    dict(id="REG09", title="Chinook monthly revenue",
         context="The Chinook music store relates monthly revenue to its catalogue additions.",
         y=("monthly revenue", "USD"), x=("new tracks", "tracks", (0, 120)),
         dummy=("Promotion month", "promotion months", "months without a promotion"),
         variables={"monthly revenue": "invoice total for the month (USD)", "new tracks": "tracks added to the catalogue that month",
                    "Promotion month": "1 = price promotion that month, 0 = no promotion"},
         P=dict(coefs=[31.0, 0.12, 6.8], p=[0.001, 0.037, 0.21], at=(40, 1)),
         S=dict(kind="continuous", coefs=[33.0, 0.11], p=[0.001, 0.061]),
         Q=dict(coefs=[30.0, 0.25, -0.0011], p=[0.001, 0.02, 0.13], ask="pvalue"),
         I=dict(coefs=[32.0, 0.09, 2.0, 0.07], p=[0.001, 0.09, 0.62, 0.30])),
    dict(id="REG10", title="Accountant salaries",
         context="A recruitment agency studies starting salaries of accountants.",
         y=("monthly salary", "thousand DKK"), x=("experience", "years", (0, 30)),
         dummy=("Certified", "certified accountants (statsautoriseret)", "non-certified accountants"),
         variables={"monthly salary": "monthly salary (thousand DKK)", "experience": "years of work experience",
                    "Certified": "1 = holds the certification, 0 = does not"},
         P=dict(coefs=[34.0, 1.2, 9.5], p=[0.001, 0.001, 0.001], at=(6, 1)),
         S=dict(kind="dummy", coefs=[41.0, 12.3], p=[0.001, 0.001]),
         Q=dict(coefs=[33.0, 2.1, -0.045], p=[0.001, 0.001, 0.002], ask="turning"),
         I=dict(coefs=[35.0, 1.0, 4.0, 0.55], p=[0.001, 0.001, 0.07, 0.016])),
    dict(id="REG11", title="Inventory shrinkage",
         context="A retailer analyses monthly inventory shrinkage across its stores.",
         y=("shrinkage", "thousand DKK"), x=("inventory value", "million DKK", (1, 25)),
         dummy=("Self-checkout", "stores with self-checkout", "stores without self-checkout"),
         variables={"shrinkage": "unexplained inventory loss per month (thousand DKK)", "inventory value": "average inventory value (million DKK)",
                    "Self-checkout": "1 = store has self-checkout tills, 0 = no self-checkout"},
         P=dict(coefs=[2.1, 1.4, 3.9], p=[0.21, 0.001, 0.019], at=(8.5, 1)),
         S=dict(kind="continuous", coefs=[2.8, 1.35], p=[0.08, 0.001]),
         Q=dict(coefs=[3.5, 0.9, 0.032], p=[0.04, 0.003, 0.11], ask="pvalue"),
         I=dict(coefs=[2.5, 1.2, 0.8, 0.55], p=[0.12, 0.001, 0.71, 0.008])),
    dict(id="REG12", title="Apartment rents",
         context="A property company studies monthly rents of its apartments.",
         y=("monthly rent", "DKK"), x=("floor area", "m²", (30, 150)),
         dummy=("City centre", "city-centre apartments", "apartments outside the centre"),
         variables={"monthly rent": "monthly rent (DKK)", "floor area": "floor area (m²)",
                    "City centre": "1 = located in the city centre, 0 = outside"},
         P=dict(coefs=[2100.0, 82.0, 1450.0], p=[0.001, 0.001, 0.003], at=(65, 1)),
         S=dict(kind="dummy", coefs=[7600.0, 1900.0], p=[0.001, 0.012]),
         Q=dict(coefs=[1500.0, 101.0, -0.12], p=[0.03, 0.001, 0.43], ask="pvalue"),
         I=dict(coefs=[2300.0, 78.0, 600.0, 14.0], p=[0.001, 0.001, 0.45, 0.038])),
]


def restaurant_exams(files_dir):
    x = pd.read_excel(files_dir / "Restaurant_sales_weather_games.xlsm", sheet_name=None)
    s, w, g = x["salesData"], x["weatherData"], x["gameData"]
    d = s.groupby("date", as_index=False)[["netTotal", "netTotal_364", "netTotal_7"]].sum()
    d = d.merge(w, on="date", how="left").merge(g, on="date", how="left")
    d[["gameDay", "homeGame"]] = d[["gameDay", "homeGame"]].fillna(0)

    def fit(f):
        m = smf.ols(f, d).fit()
        return [float(f"{v:.4g}") for v in m.params], [round(v, 4) for v in m.pvalues], m

    variables = {"daily sales": "sum of netTotal over all menu items that day (USD)",
                 "sales 7 days ago": "daily sales one week earlier (USD)", "sales 364 days ago": "daily sales on the same weekday last year (USD)",
                 "max temperature": "tmax, the day's maximum temperature (°F)", "Game day": "1 = university football game that day, 0 = no game"}
    ctx = ("Larry's Commissary (the restaurant case). Item-level sales were aggregated to daily totals and merged with the weather "
           "and game-day sheets; the models below were estimated on that merged data (312 days of 2018).")
    p1, pp1, _ = fit("netTotal ~ netTotal_7 + gameDay")
    s1, ps1, _ = fit("netTotal ~ tmax")
    q1, pq1, _ = fit("netTotal ~ tmax + I(tmax**2)")
    i1, pi1, _ = fit("netTotal ~ netTotal_364 * gameDay")
    p2, pp2, _ = fit("netTotal ~ netTotal_364 + gameDay")
    s2, ps2, _ = fit("netTotal ~ gameDay")
    q2, pq2, _ = fit("netTotal ~ netTotal_7 + I(netTotal_7**2)")
    i2, pi2, _ = fit("netTotal ~ tmax * gameDay")
    e1 = make_exam(dict(id="REG01", title="Restaurant sales I (course data)", context=ctx, real=True, variables=variables,
                        y=("daily sales", "USD"), x=("max temperature", "°F", (0, 100)),
                        dummy=("Game day", "game days", "days without a game"),
                        P=dict(coefs=p1, p=pp1, at=(3500, 1)), S=dict(kind="continuous", coefs=s1, p=ps1),
                        Q=dict(coefs=q1, p=pq1, ask="turning"), I=dict(coefs=i1, p=pi1)))
    # The prediction and interaction use other regressors than temperature: relabel them.
    e1["questions"][0].update(_relabel_prediction(e1["questions"][0], p1, pp1, "sales 7 days ago", 3500))
    e1["questions"][3] = _restaurant_interaction("REG01-I", i1, pi1, "sales 364 days ago", "USD")
    e2 = make_exam(dict(id="REG02", title="Restaurant sales II (course data)", context=ctx, real=True, variables=variables,
                        y=("daily sales", "USD"), x=("sales 7 days ago", "USD", (0, 8000)),
                        dummy=("Game day", "game days", "days without a game"),
                        P=dict(coefs=p2, p=pp2, at=(3000, 1)), S=dict(kind="dummy", coefs=s2, p=ps2),
                        Q=dict(coefs=q2, p=pq2, ask="pvalue"), I=dict(coefs=i2, p=pi2)))
    e2["questions"][0].update(_relabel_prediction(e2["questions"][0], p2, pp2, "sales 364 days ago", 3000))
    e2["questions"][3] = _restaurant_interaction("REG02-I", i2, pi2, "max temperature", "°F")
    return [e1, e2]


def _relabel_prediction(q, coefs, ps, xname, xv):
    b0, b1, b2 = coefs
    pred = b0 + b1 * xv + b2
    return dict(
        equation=f"Predicted daily sales = b0 + b1·[{xname}] + b2·[Game day]",
        coefs=coef_table(["Intercept", xname, "Game day"], coefs, ps),
        prompt=f"Bob expects a game day, and {xname} were {fmt(xv)} USD. Predict daily sales (USD).",
        answer=dict(type="number", value=round(pred, 4), tol=max(abs(pred) * 0.005, 0.01)),
        model=f"{fmt(b0)} + {fmt(b1, 4)} × {fmt(xv)} + {fmt(b2)} × 1 = {fmt(pred)} USD. Game day is a dummy, so it enters as 1.",
    )


def _restaurant_interaction(qid, c, p, xname, xunit):
    d0, d1, d2, d3 = c
    return dict(
        id=qid, kind="interaction",
        equation=f"Predicted daily sales = d0 + d1·[{xname}] + d2·[Game day] + d3·([{xname}]×[Game day])",
        coefs=coef_table(["Intercept", xname, "Game day", f"{xname}×Game day"], c, p),
        prompt="Interpret all four coefficients in context, including their p-values. What does this tell Bob?",
        model=(f"d0 ({fmt(d0)}): predicted sales on a non-game day when {xname} is 0 (an extrapolation). "
               f"d1 ({fmt(d1, 4)}): on non-game days, one more {xunit} of {xname} goes with {fmt(d1, 4)} USD higher sales. {sig(p[1])} "
               f"d2 ({fmt(d2)}): the game-day difference when {xname} is 0. {sig(p[2])} "
               f"d3 ({fmt(d3, 4)}): how the slope of {xname} changes on game days (game-day slope = {fmt(d1 + d3, 4)}). {sig(p[3])} "
               "With the interaction included, the separate game-day effect is hard to pin down because game days are rare (13 days)."),
        points=["Intercept = non-game day at 0, an extrapolation", "d1 = slope on non-game days", "d2 = game-day shift at 0",
                "d3 = change in slope on game days", "Uses all p-values; notes few game days"],
    )


def build(files_dir):
    return restaurant_exams(files_dir) + [make_exam(c) for c in SYNTHETIC]
