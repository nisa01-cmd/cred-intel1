import os, json, pandas as pd, plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

st.set_page_config(page_title="Explainable Credit Scorecard", layout="wide")
st.title("🔎 Explainable Credit Intelligence")

companies = pd.read_sql("SELECT id,name,sector FROM companies ORDER BY name", engine)
choice = st.selectbox("Select Company", companies["name"])
cid = int(companies.loc[companies["name"]==choice, "id"].iloc[0])

col1, col2 = st.columns([2,1], gap="large")

with col1:
    scores = pd.read_sql(text("SELECT score_date, score, base_score, event_adjustment, explanation FROM scores WHERE company_id=:cid ORDER BY score_date"), engine, params={"cid":cid})
    if scores.empty:
        st.info("No scores yet. Click **Run Score**.")
    else:
        fig = px.line(scores, x="score_date", y="score", title="Score over time")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Base vs event-adjusted")
        st.dataframe(scores[["score_date","base_score","event_adjustment"]].tail(10), use_container_width=True)

with col2:
    st.subheader("Run")
    if st.button("Train Model"):
        import requests
        requests.post("http://127.0.0.1:8000/train")
        st.success("Trained!")
    if st.button("Run Score"):
        import requests
        res = requests.post(f"http://127.0.0.1:8000/score/{cid}").json()
        st.success(f"Score: {res.get('score')}")
        st.session_state["explanation"] = res.get("explanation")

st.divider()
st.subheader("Why this score?")
expl = None
if "explanation" in st.session_state:
    expl = st.session_state["explanation"]
else:
    # last explanation in DB
    last = pd.read_sql(text("SELECT explanation FROM scores WHERE company_id=:cid ORDER BY score_date DESC LIMIT 1"), engine, params={"cid":cid})
    if not last.empty:
        expl = json.loads(last.iloc[0]["explanation"])

if expl:
    c1, c2, c3 = st.columns(3)
    c1.metric("Final", expl["final_score"])
    c2.metric("Base", expl["base_score"])
    c3.metric("Event Δ", expl["event_adjustment"])
    st.write("**Top positive factors**:", expl["top_positive_factors"])
    st.write("**Top negative factors**:", expl["top_negative_factors"])
    st.write("**Event reasons**:")
    for r in expl["event_reasons"]:
        st.markdown(f"- {r['event']}  *(Δ {r['delta']})*")

st.divider()
st.subheader("What-If Simulator")
with st.form("whatif"):
    dr = st.number_input("Debt Ratio", min_value=0.0, max_value=1.0, value=0.4, step=0.01)
    ic = st.number_input("Interest Coverage", min_value=0.0, max_value=50.0, value=8.0, step=0.5)
    ir = st.number_input("Interest Rate", min_value=0.0, max_value=15.0, value=6.5, step=0.1)
    submitted = st.form_submit_button("Simulate")
    if submitted:
        import requests
        res = requests.post(f"http://127.0.0.1:8000/whatif/{cid}", json={"overrides":{"debt_ratio":dr,"interest_rate":ir,"interest_coverage":ic}}).json()
        st.success(f"New Score: {res['final_score']}")
        st.write("Contributions:", res["contributions"])
