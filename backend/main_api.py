import os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from typing import Optional, List, Dict
from backend.model_core import train_model, score_company, what_if

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

app = FastAPI(title="CredTech Explainable Credit Intelligence API")

class CompanyIn(BaseModel):
    name: str
    ticker: Optional[str] = None
    sector: Optional[str] = None

class FinancialIn(BaseModel):
    company_id: int
    report_date: str
    debt_ratio: Optional[float] = None
    pe_ratio: Optional[float] = None
    revenue: Optional[float] = None
    profit_margin: Optional[float] = None
    cash_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None

class MacroIn(BaseModel):
    report_date: str
    gdp_growth: Optional[float] = None
    interest_rate: Optional[float] = None
    inflation: Optional[float] = None
    credit_spread: Optional[float] = None

class EventIn(BaseModel):
    company_id: int
    event_text: str
    sentiment: Optional[float] = 0.0
    tags: Optional[List[str]] = Field(default_factory=list)
    impact_score: Optional[float] = 0.0

class WhatIfIn(BaseModel):
    overrides: Dict

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"ok": True, "msg": "API running"}

@app.post("/company")
def add_company(payload: CompanyIn, db=Depends(get_db)):
    try:
        db.execute(text("""
            INSERT INTO companies(name, ticker, sector) VALUES (:n, :t, :s)
            ON CONFLICT (name) DO NOTHING
        """), {"n": payload.name, "t": payload.ticker, "s": payload.sector})
        db.commit()
        cid = db.execute(text("SELECT id FROM companies WHERE name=:n"), {"n": payload.name}).scalar()
        return {"company_id": cid}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/financials")
def add_financials(payload: FinancialIn, db=Depends(get_db)):
    db.execute(text("""
        INSERT INTO financials(company_id, report_date, debt_ratio, pe_ratio, revenue, profit_margin, cash_ratio, interest_coverage)
        VALUES (:cid, :d, :dr, :pe, :rev, :pm, :cr, :ic)
    """), {
        "cid": payload.company_id, "d": payload.report_date, "dr": payload.debt_ratio,
        "pe": payload.pe_ratio, "rev": payload.revenue, "pm": payload.profit_margin,
        "cr": payload.cash_ratio, "ic": payload.interest_coverage
    })
    db.commit()
    return {"ok": True}

@app.post("/macro")
def add_macro(payload: MacroIn, db=Depends(get_db)):
    db.execute(text("""
        INSERT INTO macro(report_date, gdp_growth, interest_rate, inflation, credit_spread)
        VALUES (:d, :g, :r, :i, :cs)
    """), {
        "d": payload.report_date, "g": payload.gdp_growth, "r": payload.interest_rate,
        "i": payload.inflation, "cs": payload.credit_spread
    })
    db.commit()
    return {"ok": True}

@app.post("/event")
def add_event(payload: EventIn, db=Depends(get_db)):
    db.execute(text("""
        INSERT INTO events(company_id, event_text, sentiment, tags, impact_score)
        VALUES (:cid, :txt, :s, :tags, :imp)
    """), {
        "cid": payload.company_id, "txt": payload.event_text, "s": payload.sentiment,
        "tags": payload.tags, "imp": payload.impact_score
    })
    db.commit()
    return {"ok": True}

@app.post("/train")
def train():
    train_model()
    return {"ok": True, "msg": "Model trained"}

@app.post("/score/{company_id}")
def score(company_id: int):
    try:
        final, expl = score_company(company_id)
        return {"company_id": company_id, "score": final, "explanation": expl}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/whatif/{company_id}")
def whatif(company_id: int, payload: WhatIfIn):
    try:
        res = what_if(company_id, payload.overrides)
        return res
    except Exception as e:
        raise HTTPException(400, str(e))
