import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import shap

load_dotenv()
ENGINE = create_engine(os.getenv("DATABASE_URL"))

# ---- config
FEATURES = [
    "debt_ratio","pe_ratio","revenue","profit_margin",
    "cash_ratio","interest_coverage",
    "gdp_growth","interest_rate","inflation","credit_spread",
]
SCORE_MIN, SCORE_MAX = 0.0, 100.0

# persistent in-memory model for hackathon run
MODEL = None
EXPLAINER = None

def _fetch_latest_panel():
    with ENGINE.begin() as conn:
        df_fin = pd.read_sql(text("""
            SELECT f.*, c.id as company_id, c.name
            FROM financials f
            JOIN companies c ON c.id=f.company_id
        """), conn)
        df_fin = df_fin.loc[:, ~df_fin.columns.duplicated()]
        df_fin.sort_values(["company_id","report_date"], inplace=True)
        df_fin = df_fin.groupby("company_id").tail(1)  # latest snapshot per company

        df_macro = pd.read_sql(text("""
            SELECT * FROM macro ORDER BY report_date DESC LIMIT 1
        """), conn)
        if df_macro.empty:
            raise ValueError("No macro data found")
        macro = df_macro.iloc[0]
        for col in ["gdp_growth","interest_rate","inflation","credit_spread"]:
            df_fin[col] = macro[col]

    return df_fin

def _normalize_score(y_raw):
    # clamp & scale to 0..100 if needed; here we assume model outputs roughly 0..100
    return float(np.clip(y_raw, SCORE_MIN, SCORE_MAX))

def _event_adjustment(company_id):
    # rule-based: last 14 days events
    with ENGINE.begin() as conn:
        df_ev = pd.read_sql(text("""
            SELECT event_text, sentiment, tags, COALESCE(impact_score,0) AS impact_score
            FROM events
            WHERE company_id=:cid AND event_date >= NOW() - INTERVAL '14 days'
            ORDER BY event_date DESC
        """), conn, params={"cid": company_id})

    if df_ev.empty:
        return 0.0, []

    adj = 0.0
    reasons = []
    for _, r in df_ev.iterrows():
        base = 0.0
        # tag-based rules (fast and transparent)
        tags = set((r["tags"] or []))
        if "debt_restructuring" in tags: base -= 15
        if "default_warning" in tags:     base -= 25
        if "guidance_cut" in tags:        base -= 10
        if "lawsuit" in tags:             base -= 8
        if "bond_issue_success" in tags:  base += 6
        if "guidance_raise" in tags:      base += 8

        # sentiment amplifies +/- up to 5 points
        sent_amp = float(r["sentiment"] or 0.0) * 5.0
        # custom impact_score field (if analyst set it)
        manual = float(r["impact_score"] or 0.0)

        total = base + sent_amp + manual
        if total != 0:
            reasons.append({
                "event": r["event_text"][:180],
                "delta": round(total,2)
            })
        adj += total

    # clamp event adjustment within reasonable bounds
    adj = float(np.clip(adj, -30, 20))
    return adj, reasons

def train_model():
    global MODEL, EXPLAINER
    df = _fetch_latest_panel()

    # For hackathon: fabricate a proxy target if none (e.g., healthier ratios → higher score)
    # In production, replace with labels (PD/LGD or expert score)
    # Simple heuristic label:
    y = (
        (1 - df["debt_ratio"].fillna(0)).clip(0,1)*40 +
        df["profit_margin"].fillna(0).clip(-0.2,0.4)*100*0.25 +
        df["cash_ratio"].fillna(0).clip(0,3)*10 +
        df["interest_coverage"].fillna(0).clip(0,20)*1.5 -
        df["credit_spread"].fillna(0).clip(0,10)*2
    ).fillna(50.0)
    y = y.clip(SCORE_MIN, SCORE_MAX)

    X = df[FEATURES].fillna(df[FEATURES].median())
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42)

    MODEL = XGBRegressor(
        n_estimators=300, max_depth=4, learning_rate=0.07,
        subsample=0.9, colsample_bytree=0.8, random_state=42
    )
    MODEL.fit(Xtr, ytr)

    preds = MODEL.predict(Xte)
    print("R2:", r2_score(yte, preds))
    print("MAE:", mean_absolute_error(yte, preds))

    EXPLAINER = shap.TreeExplainer(MODEL)

def score_company(company_id: int):
    global MODEL, EXPLAINER
    if MODEL is None:
        train_model()

    df = _fetch_latest_panel()
    row = df[df["company_id"] == company_id]
    if row.empty:
        raise ValueError(f"No latest data for company_id={company_id}")

    X = row[FEATURES].fillna(row[FEATURES].median())
    base_pred = float(MODEL.predict(X)[0])
    base_score = _normalize_score(base_pred)

    # SHAP explanation
    shap_vals = EXPLAINER.shap_values(X)
    contribs = dict(zip(FEATURES, np.round(shap_vals[0].tolist(), 3)))

    # event layer
    evt_adj, reasons = _event_adjustment(company_id)
    final_score = _normalize_score(base_score + evt_adj)

    # plain-language explanation
    top_pos = sorted(contribs.items(), key=lambda x: x[1], reverse=True)[:2]
    top_neg = sorted(contribs.items(), key=lambda x: x[1])[:2]
    expl = {
        "base_score": round(base_score,2),
        "event_adjustment": round(evt_adj,2),
        "final_score": round(final_score,2),
        "top_positive_factors": top_pos,
        "top_negative_factors": top_neg,
        "event_reasons": reasons
    }

    # persist
    with ENGINE.begin() as conn:
        conn.execute(text("""
            INSERT INTO scores (company_id, score, base_score, event_adjustment, explanation)
            VALUES (:cid, :score, :base, :adj, :expl)
        """), {
            "cid": company_id,
            "score": final_score,
            "base": base_score,
            "adj": evt_adj,
            "expl": json.dumps(expl)
        })

    return final_score, expl

def what_if(company_id: int, overrides: dict):
    """
    overrides: dict of feature -> new value (e.g., {"debt_ratio":0.4,"gdp_growth":3.0})
    """
    global MODEL, EXPLAINER
    if MODEL is None:
        train_model()

    df = _fetch_latest_panel()
    row = df[df["company_id"] == company_id]
    if row.empty:
        raise ValueError(f"No latest data for company_id={company_id}")

    X = row[FEATURES].fillna(row[FEATURES].median()).copy()
    for k,v in overrides.items():
        if k in X.columns:
            X.iloc[0, X.columns.get_loc(k)] = float(v)

    new_base = float(MODEL.predict(X)[0])
    new_base = _normalize_score(new_base)
    evt_adj, _ = _event_adjustment(company_id)
    final = _normalize_score(new_base + evt_adj)

    shap_vals = EXPLAINER.shap_values(X)
    contribs = dict(zip(FEATURES, np.round(shap_vals[0].tolist(), 3)))

    return {
        "final_score": round(final,2),
        "base_score": round(new_base,2),
        "event_adjustment": round(evt_adj,2),
        "contributions": contribs
    }
