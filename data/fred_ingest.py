import requests
import os
import pg8000
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not FRED_API_KEY:
    raise RuntimeError("❌ Missing FRED_API_KEY in .env")
if not DATABASE_URL:
    raise RuntimeError("❌ Missing DATABASE_URL in .env")


def get_connection():
    url = urlparse(DATABASE_URL.replace("postgresql+pg8000", "postgresql"))
    return pg8000.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        database=url.path[1:],
    )


FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

# Mapping of FRED series → macro table columns
SERIES = {
    "GDP": ("GDP", "gdp_growth"),
    "FEDFUNDS": ("FEDFUNDS", "interest_rate"),
    "CPIAUCSL": ("CPIAUCSL", "inflation"),
    "BAA10YM": ("BAA10YM", "credit_spread"),
}


def fetch_and_store_fred():
    conn = get_connection()
    cursor = conn.cursor()

    for name, (series_id, column) in SERIES.items():
        url = f"{FRED_URL}?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
        response = requests.get(url)
        data = response.json()

        if "observations" not in data:
            raise RuntimeError(f"❌ Unexpected response from FRED for {series_id}")

        for obs in data["observations"]:
            if obs["value"] == ".":
                continue

            cursor.execute(
                f"""
                INSERT INTO macro (report_date, {column})
                VALUES (%s, %s)
                ON CONFLICT (report_date) DO UPDATE
                SET {column} = EXCLUDED.{column}
                """,
                (obs["date"], float(obs["value"]))
            )

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ FRED data ingested successfully!")


if __name__ == "__main__":
    fetch_and_store_fred()
