import requests
import os
import pg8000
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not NEWS_API_KEY:
    raise RuntimeError("❌ Missing NEWSAPI_KEY in .env")
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


NEWS_URL = f"https://newsapi.org/v2/everything?q=credit+risk&language=en&apiKey={NEWS_API_KEY}"


def fetch_and_store_news():
    response = requests.get(NEWS_URL)
    data = response.json()

    if "articles" not in data:
        raise RuntimeError("❌ Unexpected response from News API")

    conn = get_connection()
    cursor = conn.cursor()

    for article in data["articles"]:
        cursor.execute(
            """
            INSERT INTO news_headlines (company_id, headline, published_at)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                None,  # You don’t have company mapping yet
                article["title"],
                article["publishedAt"],
            ),
        )

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ News data ingested successfully!")


if __name__ == "__main__":
    fetch_and_store_news()
