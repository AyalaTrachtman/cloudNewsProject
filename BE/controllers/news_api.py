import requests
from .firebase_db import save_news, news_exists
from .huggingface_analyzer import analyze_article
import uuid
from transformers import pipeline
import numpy as np
import cloudinary
import cloudinary.uploader
import urllib.parse
from io import BytesIO
from .firebase_db import get_all_news, delete_news


API_KEY = "cf0598a600744dbb8092ef66ea26ae2b"
BASE_URL = "https://newsapi.org/v2/everything"
DEFAULT_IMAGE_URL = "https://example.com/default-image.jpg"
SERP_API_KEY = "your_serpapi_key"

# הגדרות Cloudinary
cloudinary.config(
    cloud_name="dvzpm0jir",
    api_key="431769535972431",
    api_secret="rmagqBMWdt98g57lk84Y5YRvRTk",
    secure=True
)

# נושאים אפשריים
TOPICS = [
    "Politics", "Finance", "Science", "Culture",
    "Sport", "Technology", "Health", "World"
]

# מודל סיווג Hugging Face (Zero-shot)
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)


def upload_to_cloudinary(image_url, public_id=None):
    try:
        result = cloudinary.uploader.upload(image_url, public_id=public_id)
        return result['secure_url']
    except Exception as e:
        print("Cloudinary upload error:", e)
        return image_url  # במקרה של כשל


def classify_article(content):
    if not content:
        return "World"
    try:
        result = classifier(content[:512], TOPICS)
        return result["labels"][0]
    except Exception as e:
        print("Classification error:", e)
        return "World"


def summarize_article(content, max_chars=200):
    if not content:
        return ""
    return content[:max_chars] + "..." if len(content) > max_chars else content


def safe_float(x):
    return float(x) if isinstance(x, (np.float32, np.float64)) else x


def generate_image_bytes(prompt: str) -> BytesIO:
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    response = requests.get(image_url)
    response.raise_for_status()
    image_bytes = BytesIO(response.content)
    return image_bytes


def fetch_and_save_news(category=None, country=None):
    print("fetch_and_save_news התחילה")

    params = {
        "apiKey": API_KEY,
        "language": "en",  # רק באנגלית
        "q": "news",
        "pageSize": 100,
        "sortBy": "publishedAt"
    }

    if category:
        params["q"] = category

    response = requests.get(BASE_URL, params=params)
    print("Response status:", response.status_code)
    print("Response text:", response.text[:500])

    if response.status_code != 200:
        return {"error": f"Failed to fetch news, status: {response.status_code}"}

    data = response.json()
    saved_articles = []
    saved_ids = []

    for article in data.get("articles", []):

        source_name = article.get("source", {}).get("name", "")
    
    # דילוג על כתבות מ-Biztoc.com
        if source_name.strip().lower() == "biztoc.com" or source_name.strip().lower() == "thefly.com":
            print(f"🚫 Skipping article from {source_name}")
            continue

        content = article.get("description") or article.get("content")
        if not content:
            continue

        title = article.get("title", "")
        source = article.get("source", {}).get("name", "")
        url = article.get("url", "")
        published_at = article.get("publishedAt")

        if news_exists(url):
            print(f"⚠ Article already exists: {url}")
            continue

        news_id = str(uuid.uuid4())

        image_url = article.get("urlToImage") or generate_image_bytes(title)
        cloudinary_url = upload_to_cloudinary(image_url, public_id=news_id)

        analysis = analyze_article(title, content)
        entities = analysis.get("entities", [])
        for e in entities:
            if 'score' in e:
                e['score'] = safe_float(e['score'])

        classification = classify_article(content)
        summary = summarize_article(content)

        news_data = {
            "id": news_id,
            "title": title,
            "content": content,
            "summary": summary,
            "url": url,
            "source": source,
            "image_url": cloudinary_url,
            "classification": classification,
            "entities": entities,
            "published_at": published_at
        }

        save_news(news_id, news_data)
        saved_articles.append(news_data)
        saved_ids.append(news_id)

    return {
        "message": f"Saved {len(saved_articles)} articles",
        "articles": saved_articles,
        "ids": saved_ids
    }


if __name__ == "__main__":
   fetch_and_save_news()

