"""Python-реализация финмодели. Та же логика, что и формулы в Excel —
build_finmodel.py сверяет результаты пересчёта LibreOffice с этим кодом."""

import math

import assumptions as A


def v(d, key):
    return d[key][0]


# --- Юнит-экономика ------------------------------------------------------------

def unit_a():
    u = A.UNIT_A
    acq = v(A.TAX, "acquiring")
    usn = v(A.TAX, "usn_rate")
    price_m2 = v(u, "price_general_m2") * (1 - v(u, "share_repair")) + v(u, "price_repair_m2") * v(u, "share_repair")
    aov = v(u, "area") * price_m2 + v(u, "upsell")
    labor = aov * v(u, "labor_share")
    fees = aov * acq
    reserve = aov * v(u, "quality_reserve")
    cogs = labor + v(u, "chem") + v(u, "amort") + v(u, "logistics") + fees + reserve
    gm = aov - cogs
    tax = aov * usn
    cm = gm - tax
    return {
        "aov": aov, "price_m2": price_m2, "labor": labor, "chem": v(u, "chem"), "amort": v(u, "amort"),
        "logistics": v(u, "logistics"), "fees": fees, "reserve": reserve, "cogs": cogs,
        "var_ex_tax": cogs, "gm": gm, "gm_pct": gm / aov, "tax": tax, "cm": cm, "cm_pct": cm / aov,
        "labor_per_hour": labor / v(u, "man_hours"), "labor_per_m2": labor / v(u, "area"),
    }


def unit_b():
    u = A.UNIT_B
    acq = v(A.TAX, "acquiring")
    usn = v(A.TAX, "usn_rate")
    price = v(u, "price_single") * (1 - v(u, "sub_discount"))
    labor = price * v(u, "labor_share")
    fees = price * acq
    reserve = price * v(u, "quality_reserve")
    cogs = labor + v(u, "chem") + v(u, "amort") + v(u, "logistics") + fees + reserve
    gm = price - cogs
    tax = price * usn
    cm = gm - tax
    vpm = v(u, "visits_per_month")
    return {
        "price": price, "labor": labor, "chem": v(u, "chem"), "amort": v(u, "amort"),
        "logistics": v(u, "logistics"), "fees": fees, "reserve": reserve, "cogs": cogs,
        "var_ex_tax": cogs, "gm": gm, "gm_pct": gm / price, "tax": tax, "cm": cm, "cm_pct": cm / price,
        "labor_per_hour": labor / v(u, "hours"), "price_m2": price / v(u, "area"),
        "rev_month": price * vpm, "cm_month": cm * vpm,
    }


def ltv_b(churn):
    b = unit_b()
    lifetime = 1 / churn
    return {
        "lifetime": lifetime,
        "ltv_rev": b["rev_month"] * lifetime,
        "ltv_cm": b["cm_month"] * lifetime,
        "cac_max_ltv": b["cm_month"] * lifetime / v(A.TARGETS, "ltv_cac_min"),
        "cac_max_payback": b["cm_month"] * v(A.TARGETS, "payback_months_b"),
    }


def unit_s():
    u = A.UNIT_S
    acq = v(A.TAX, "acquiring")
    usn = v(A.TAX, "usn_rate")
    aov = v(u, "aov")
    labor = aov * v(u, "labor_share")
    fees = aov * acq
    reserve = aov * v(u, "quality_reserve")
    cogs = labor + v(u, "chem") + v(u, "amort") + v(u, "logistics") + fees + reserve
    gm = aov - cogs
    tax = aov * usn
    cm = gm - tax
    return {"aov": aov, "labor": labor, "fees": fees, "reserve": reserve, "cogs": cogs, "var_ex_tax": cogs,
            "gm": gm, "gm_pct": gm / aov, "tax": tax, "cm": cm, "cm_pct": cm / aov}


def unit_b2b():
    cv = v(A.B2B, "contract_value")
    direct = cv * v(A.B2B, "direct_share")
    tax = cv * v(A.TAX, "usn_rate")
    return {"value": cv, "direct": direct, "gm": cv - direct, "tax": tax, "cm": cv - direct - tax,
            "cm_pct": (cv - direct - tax) / cv}


def cac_max_a():
    a = unit_a()
    target = v(A.TARGETS, "target_margin_a")
    cac = a["cm"] - target * a["aov"]
    return {"cac_max": cac, "cac_breakeven": a["cm"], "cpl_max": cac * v(A.TARGETS, "lead_to_order_a")}


def fix_base():
    return sum(x for _, x in A.FIX_ITEMS)


def capex_total(items):
    return sum(q * p for _, q, p in items)


def prelaunch_total():
    return sum(x for _, x in A.PRELAUNCH_ITEMS)


# --- Текущий прайс проекта (сиды) ------------------------------------------------

def current_tariffs():
    o = A.CURRENT_OBJECT
    out = {}
    for t, (base, room, bath, mb, mr, mbath) in A.CURRENT_TARIFFS.items():
        out[t] = {
            "price": base + o["rooms"] * room + o["bathrooms"] * bath,
            "hours": (mb + o["rooms"] * mr + o["bathrooms"] * mbath) / 60,
        }
    return out


def _cm(price, labor, chem, amort, logistics, reserve_rate):
    acq = v(A.TAX, "acquiring")
    usn = v(A.TAX, "usn_rate")
    return price - labor - chem - amort - logistics - price * (acq + reserve_rate + usn)


def current_units():
    """Юнит-экономика A и B на текущем прайсе сайта в двух режимах оплаты клинеров:
    share — та же доля от чека (клинер получает меньше в час),
    market — та же оплата в рублях, что в рекомендуемой модели (рыночная ставка за час)."""
    ct = current_tariffs()
    ua, ub = unit_a(), unit_b()
    a_share = v(A.UNIT_A, "share_repair")
    aov_a = ct["general"]["price"] * (1 - a_share) + ct["post_renovation"]["price"] * a_share + v(A.UNIT_A, "upsell")
    price_b = ct["maintenance"]["price"] * (1 - v(A.UNIT_B, "sub_discount"))
    res = {"tariffs": ct, "aov_a": aov_a, "price_b": price_b}
    for mode in ("share", "market"):
        lab_a = aov_a * v(A.UNIT_A, "labor_share") if mode == "share" else ua["labor"]
        lab_b = price_b * v(A.UNIT_B, "labor_share") if mode == "share" else ub["labor"]
        cm_a = _cm(aov_a, lab_a, v(A.UNIT_A, "chem"), v(A.UNIT_A, "amort"), v(A.UNIT_A, "logistics"),
                   v(A.UNIT_A, "quality_reserve"))
        cm_b = _cm(price_b, lab_b, v(A.UNIT_B, "chem"), v(A.UNIT_B, "amort"), v(A.UNIT_B, "logistics"),
                   v(A.UNIT_B, "quality_reserve"))
        res[mode] = {
            "labor_a": lab_a, "labor_share_a": lab_a / aov_a, "hourly_a": lab_a / v(A.UNIT_A, "man_hours"),
            "cm_a": cm_a, "cm_pct_a": cm_a / aov_a,
            "labor_b": lab_b, "labor_share_b": lab_b / price_b, "hourly_b": lab_b / v(A.UNIT_B, "hours"),
            "cm_b": cm_b, "cm_pct_b": cm_b / price_b, "cm_month_b": cm_b * v(A.UNIT_B, "visits_per_month"),
        }
    return res


def current_price_scenario(mode, code="R"):
    """Прогон сценария на текущем прайсе: подменяем цены (и долю ФОТ в режиме market)."""
    import copy
    saved_a, saved_b = copy.deepcopy(A.UNIT_A), copy.deepcopy(A.UNIT_B)
    cu = current_units()
    ct = cu["tariffs"]
    area = v(A.UNIT_A, "area")
    try:
        A.UNIT_A = dict(A.UNIT_A)
        A.UNIT_B = dict(A.UNIT_B)
        A.UNIT_A["price_general_m2"] = (ct["general"]["price"] / area, "")
        A.UNIT_A["price_repair_m2"] = (ct["post_renovation"]["price"] / area, "")
        A.UNIT_B["price_single"] = (ct["maintenance"]["price"], "")
        A.UNIT_A["labor_share"] = (cu[mode]["labor_share_a"], "")
        A.UNIT_B["labor_share"] = (cu[mode]["labor_share_b"], "")
        return summary(code)
    finally:
        A.UNIT_A, A.UNIT_B = saved_a, saved_b


# --- Помесячная модель ---------------------------------------------------------

def calendar(m):
    idx = A.START_MONTH - 1 + (m - 1)
    return A.START_YEAR + idx // 12, idx % 12 + 1


def ramp(m, start, m6, growth):
    if m <= 6:
        return start + (m6 - start) * (m - 1) / 5
    return m6 * (1 + growth) ** (m - 6)


def run(code):
    i = A.SCENARIO_CODES.index(code)
    s = {k: val[1 + i] for k, val in A.SCENARIOS.items()}
    ua, ub, us, ub2b = unit_a(), unit_b(), unit_s(), unit_b2b()
    usn = v(A.TAX, "usn_rate")
    vat_rate = v(A.TAX, "vat_rate")
    vat_thr = v(A.TAX, "vat_threshold")
    fb = fix_base()
    rows = []
    active = 0.0
    capex0 = capex_total(A.CAPEX_ITEMS) + prelaunch_total()
    cum = -capex0
    for m in range(1, A.HORIZON + 1):
        year, month = calendar(m)
        season = A.SEASONALITY[month]
        a_orders = min(s["a_cap"], ramp(m, s["a_start"], s["a_m6"], s["a_growth"]) * season)
        new_subs = ramp(m, s["s_start"], s["s_m6"], s["s_growth"])
        active = active * (1 - s["churn"]) + new_subs
        visits = active * v(A.UNIT_B, "visits_per_month")
        spec = a_orders * s["spec_ratio"]
        contracts = min(s["b2b_max"], (m - s["b2b_start"]) // s["b2b_step"] + 1) if m >= s["b2b_start"] else 0
        rev = a_orders * ua["aov"] + visits * ub["price"] + spec * us["aov"] + contracts * ub2b["value"]
        var = (a_orders * ua["var_ex_tax"] + visits * ub["var_ex_tax"] + spec * us["var_ex_tax"]
               + contracts * ub2b["direct"])
        mkt = a_orders * s["cac_a"] + new_subs * s["cac_b"] + spec * s["cac_s"]
        fix = fb + v(A.FIX_STEP, "step_cost") * math.floor(rev / v(A.FIX_STEP, "rev_step"))
        prev_year_rev = sum(r["rev"] for r in rows if r["year"] == year - 1)
        ytd_before = sum(r["rev"] for r in rows if r["year"] == year)
        vat_on = 1 if (prev_year_rev > vat_thr or ytd_before > vat_thr) else 0
        vat = rev * vat_rate / (1 + vat_rate) * vat_on
        usn_tax = (rev - vat) * usn
        profit = rev - vat - var - mkt - fix - usn_tax
        capex = capex_total(A.CAPEX2_ITEMS) if m == s["capex2_month"] else 0
        cf = profit - capex
        cum += cf
        fte = ((a_orders * v(A.UNIT_A, "man_hours") + visits * v(A.UNIT_B, "hours")
                + spec * v(A.UNIT_S, "man_hours")) / v(A.STAFF, "hours_per_fte")
               + contracts * v(A.STAFF, "b2b_fte"))
        rows.append(dict(m=m, year=year, month=month, season=season, a=a_orders, new_subs=new_subs,
                         active=active, visits=visits, spec=spec, contracts=contracts, rev=rev, var=var,
                         mkt=mkt, fix=fix, vat_on=vat_on, vat=vat, usn=usn_tax, profit=profit,
                         capex=capex, cf=cf, cum=cum, fte=fte))
    return rows


def summary(code):
    rows = run(code)
    capex0 = capex_total(A.CAPEX_ITEMS) + prelaunch_total()
    op_cum, min_op_cum = 0.0, 0.0
    for r in rows:
        op_cum += r["cf"]
        min_op_cum = min(min_op_cum, op_cum)
    sustained = None
    for r in rows:
        if all(x["profit"] >= 0 for x in rows if x["m"] >= r["m"]):
            sustained = r["m"]
            break
    payback = next((r["m"] for r in rows if r["cum"] >= 0), None)
    return {
        "rows": rows,
        "rev_12": sum(r["rev"] for r in rows[:12]),
        "rev_24": sum(r["rev"] for r in rows),
        "profit_12": sum(r["profit"] for r in rows[:12]),
        "profit_24": sum(r["profit"] for r in rows),
        "rev_m12": rows[11]["rev"], "rev_m24": rows[23]["rev"],
        "profit_m12": rows[11]["profit"], "profit_m24": rows[23]["profit"],
        "max_gap": -min_op_cum,
        "breakeven_month": sustained,
        "payback_month": payback,
        "min_cum": min(r["cum"] for r in rows),
        "capex0": capex0,
        "vat_from": next((r["m"] for r in rows if r["vat_on"]), None),
    }


def start_capital():
    capex = capex_total(A.CAPEX_ITEMS)
    pre = prelaunch_total()
    gap_p = summary("P")["max_gap"]
    reserve = gap_p * A.RESERVE_SAFETY[0]
    return {"capex": capex, "prelaunch": pre, "reserve": reserve, "total": capex + pre + reserve}


def breakeven_orders():
    fb = fix_base()
    a, b = unit_a(), unit_b()
    out = {}
    for code in A.SCENARIO_CODES:
        i = A.SCENARIO_CODES.index(code)
        cac_a = A.SCENARIOS["cac_a"][1 + i]
        out[code] = {
            "a_only": fb / (a["cm"] - cac_a),
            "b_visits_only": fb / b["cm"],
        }
    return out


if __name__ == "__main__":
    a, b, s = unit_a(), unit_b(), unit_s()
    print("A", {k: round(x, 1) for k, x in a.items()})
    print("B", {k: round(x, 1) for k, x in b.items()})
    print("S", {k: round(x, 1) for k, x in s.items()})
    print("B2B", unit_b2b())
    print("CAC A", cac_max_a())
    for c in (0.12, 0.09, 0.07):
        print("LTV", c, {k: round(x) for k, x in ltv_b(c).items()})
    print("FIX", fix_base(), "CAPEX", capex_total(A.CAPEX_ITEMS), "CAPEX2", capex_total(A.CAPEX2_ITEMS),
          "PRE", prelaunch_total())
    print("BEP", breakeven_orders())
    for code in A.SCENARIO_CODES:
        sm = summary(code)
        print(code, {k: (round(x) if isinstance(x, float) else x) for k, x in sm.items() if k != "rows"})
        for r in sm["rows"]:
            print("  M%02d %d-%02d A=%5.1f subs=%6.1f vis=%6.1f spec=%5.1f b2b=%d rev=%9.0f var=%9.0f mkt=%7.0f fix=%7.0f vat=%7.0f usn=%7.0f P=%9.0f cum=%10.0f fte=%4.1f" % (
                r["m"], r["year"], r["month"], r["a"], r["active"], r["visits"], r["spec"], r["contracts"],
                r["rev"], r["var"], r["mkt"], r["fix"], r["vat"], r["usn"], r["profit"], r["cum"], r["fte"]))
    print("START CAPITAL", start_capital())
    cu = current_units()
    print("CURRENT", {k: x for k, x in cu.items() if k in ("tariffs", "aov_a", "price_b")})
    for mode in ("share", "market"):
        print(" ", mode, {k: round(x, 2) for k, x in cu[mode].items()})
        sm = current_price_scenario(mode)
        print("  scenario R:", {k: (round(x) if isinstance(x, float) else x) for k, x in sm.items() if k != "rows"})
