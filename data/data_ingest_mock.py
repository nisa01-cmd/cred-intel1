import os, random, datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

companies = [
    ("Acme Steel", "ACME", "Materials"),
    ("Nova Retail", "NOVA", "Consumer"),
    ("ZenTech Systems", "ZENT", "Technology")
]

with engine.begin() as conn:
    for n,t,s in companies:
        conn.execute(text("""
            INSERT INTO companies(name,ticker,sector) VALUES (:n,:t,:s)
            ON CONFLICT (name) DO NOTHING
        """), {"n":n,"t":t,"s":s})

    # macro snapshot
    today = datetime.date.today().isoformat()
    conn.execute(text("""
        INSERT INTO macro(report_date, gdp_growth, interest_rate, inflation, credit_spread)
        VALUES (:d, :g, :r, :i, :cs)
    """), {"d":today, "g":5.9, "r":6.5, "i":4.1, "cs":2.3})

    # simple financials
    ids = conn.execute(text("SELECT id,name FROM companies")).fetchall()
    for cid, name in ids:
        payload = {
            "cid": cid, "d": today,
            "dr": round(random.uniform(0.2,0.8),2),
            "pe": round(random.uniform(8,35),1),
            "rev": round(random.uniform(500,5000),2),
            "pm": round(random.uniform(-0.05,0.25),3),
            "cr": round(random.uniform(0.2,2.5),2),
            "ic": round(random.uniform(0.5,15.0),2),
        }
        conn.execute(text("""
            INSERT INTO financials(company_id, report_date, debt_ratio, pe_ratio, revenue, profit_margin, cash_ratio, interest_coverage)
            VALUES (:cid, :d, :dr, :pe, :rev, :pm, :cr, :ic)
        """), payload)

    # one negative event for demo
    conn.execute(text("""
        INSERT INTO events(company_id, event_text, sentiment, tags, impact_score)
        SELECT id, 'Debt restructuring announced', -0.6, ARRAY['debt_restructuring'], 0 FROM companies WHERE name='Acme Steel'
    """))
    # one positive
    conn.execute(text("""
        INSERT INTO events(company_id, event_text, sentiment, tags, impact_score)
        SELECT id, 'Raised guidance for Q3', 0.5, ARRAY['guidance_raise'], 0 FROM companies WHERE name='ZenTech Systems'
    """))

print("Seeded demo data ✅")
