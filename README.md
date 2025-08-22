# 📊 CredTech — Explainable Credit Intelligence Platform

> ⚡ Real-time creditworthiness scoring, powered by data + AI + explainability.
> Built for **CredTech Hackathon 2025**, IIT Kanpur.
> **Developed by Team Firewolf 🐺**

---

## 🌟 Why We Built This

Traditional credit ratings are:
❌ Slow to update
❌ Opaque (black box)
❌ Lag behind real events

Our solution: **CredTech** → a real-time, explainable, analyst-friendly platform that:
✅ Continuously ingests **financial + macro + news data**
✅ Generates **creditworthiness scores in real-time**
✅ Explains **“WHY” the score changed** in plain language
✅ Provides **interactive dashboard & what-if simulations**

---

## 🏆 Key Features

1. **📥 Multi-Source Data Ingestion**

   * Structured: financial ratios (debt, P/E, revenue), macro data (GDP, interest rates)
   * Unstructured: news events + sentiment

2. **🤖 Adaptive Scoring Engine**

   * XGBoost model trained on financial + macro data
   * SHAP values for feature importance
   * Rule-based + sentiment event adjustments

3. **🔎 Explainability Layer**

   * Feature contributions (positive & negative)
   * Event-driven adjustments (*“Debt restructuring → -15 points”*)
   * Plain-language explanations

4. **📈 Analyst Dashboard (Streamlit)**

   * Score trends over time
   * Factor breakdown (visualized)
   * Event feed (“Why this score?”)
   * **What-if Simulator**: tweak variables → see instant impact

5. **⚡ End-to-End Deployment**

   * Backend: FastAPI (REST API)
   * Database: PostgreSQL (Supabase/Render)
   * Frontend: Streamlit Dashboard
   * Containerized: Docker + Docker Compose

---

## 🏗 System Architecture

```
        ┌──────────────────┐
        │  Data Sources     │
        │  (Finance + News) │
        └─────────┬────────┘
                  │
                  ▼
        ┌──────────────────┐
        │   PostgreSQL DB   │
        │ (companies, data) │
        └─────────┬────────┘
                  │
                  ▼
        ┌──────────────────┐
        │  Scoring Engine   │
        │  (FastAPI + ML)   │
        └─────────┬────────┘
                  │
                  ▼
        ┌──────────────────┐
        │ Explainability    │
        │ (SHAP + Events)   │
        └─────────┬────────┘
                  │
                  ▼
        ┌──────────────────┐
        │ Analyst Dashboard │
        │ (Streamlit)       │
        └──────────────────┘
```

---

## 📂 Project Structure

```
cred-intel1/
│── README.md             # Documentation
│── requirements.txt      # Dependencies
│── .env                  # Environment variables (DB URL, API keys)
│── db_schema.sql         # Postgres schema
│
├── backend/              # FastAPI + ML engine
│   │── main_api.py       # API endpoints
│   │── model_core.py     # Scoring + explainability
│
├── data/                 # Data ingestion
│   │── data_ingest_mock.py # Seeds demo data
│   │── yahoo_ingest.py     # (optional) Yahoo 
│   │── news_ingest.py      # (optional) News 
│   │── Fred_ingest.py      # (optional)  
│
├── dashboard/
│   │── streamlit_app.py  # Analyst dashboard
│
├── deploy/               # Deployment configs
│   │── Dockerfile
│   │── docker-compose.yml
│
└── docs/
    │── architecture.png  # System diagram (future)
    │── slides/           # Hackathon slides (future)
    │── demo_video.mp4    # Walkthrough video(future)
```

---

## ⚙️ Setup & Run (Local)

### 1️⃣ Clone Repo

```bash
git clone https://github.com/firewolf/cred-intel1.git
cd cred-intel1
```

### 2️⃣ Install Requirements

```bash
pip install -r requirements.txt
```

### 3️⃣ Setup Database

* Use **Supabase** (recommended) or local Postgres.
* Create a `.env` file:

  ```
  DATABASE_URL=postgresql://user:password@host:5432/credintel
  ```
* Run schema:

  ```bash
  psql "$DATABASE_URL" -f db_schema.sql
  ```

### 4️⃣ Seed Demo Data

```bash
python data/data_ingest_mock.py
```

### 5️⃣ Start API

```bash
uvicorn backend.main_api:app --reload
```

👉 API: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6️⃣ Start Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

👉 Dashboard: [http://localhost:8501](http://localhost:8501)

---

## 🚀 One-Click Run with Docker

```bash
docker-compose up --build
```

* API: [http://localhost:8000](http://localhost:8000)
* Dashboard: [http://localhost:8501](http://localhost:8501)

---

## 🎥 Demo Preview

* **Dashboard** → Credit score trends, event-driven explainability, what-if simulator
* **API** → Swagger docs to test endpoints

---

## 🏅 Hackathon Deliverables

1. **GitHub Repo** (this project)
2. **Deployed App** (Supabase + Render/Streamlit Cloud)
3. **Slides (PDF/PPT)** – `/docs/slides/`
4. **Demo Video (5–7 min)** – `/docs/demo_video.mp4`

---

## 👩‍💻 Team Firewolf

* **Data Pipeline** → ingestion & processing
* **Model & Explainability** → ML + SHAP + event rules
* **Frontend Dashboard** → Streamlit + Plotly
* **Deployment** → Docker + Cloud hosting

---

✨ *With CredTech, Firewolf makes credit ratings faster, fairer, and explainable.*

