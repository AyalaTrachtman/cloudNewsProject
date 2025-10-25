import requests
from .firebase_db import save_news
from .huggingface_analyzer import analyze_article
import uuid
from transformers import pipeline
import numpy as np
import cloudinary
import cloudinary.uploader

API_KEY = "cf0598a600744dbb8092ef66ea26ae2b"
BASE_URL = "https://newsapi.org/v2/top-headlines"
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

# מודל Hugging Face מתאים לסיווג נושאים (Zero-shot)
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

def upload_to_cloudinary(image_url, public_id=None):
    try:
        result = cloudinary.uploader.upload(image_url, public_id=public_id)
        return result['secure_url']  # זה הקישור של התמונה ב-Cloudinary
    except Exception as e:
        print("Cloudinary upload error:", e)
        return image_url  # במקרה של כשל, נשאר עם הקישור המקורי


def classify_article(content):
    if not content:
        return "World"
    try:
        result = classifier(content[:512], TOPICS)
        label = result["labels"][0]
        return label
    except Exception as e:
        print("Classification error:", e)
        return "World"
    
# בדיקת סיווג ישירה
if _name_ == "_main_":
    test_text = "The government announced new economic reforms and tax cuts today."
    print("Testing classification on sample text:")
    print(classify_article(test_text))


def summarize_article(content, max_chars=200):
    if not content:
        return ""
    return content[:max_chars] + "..." if len(content) > max_chars else content

def safe_float(x):
    return float(x) if isinstance(x, (np.float32, np.float64)) else x

def fetch_image_from_google(query):
    try:
        params = {
            "q": query,
            "tbm": "isch",
            "ijn": "0",
            "api_key": SERP_API_KEY
        }
        response = requests.get("https://serpapi.com/search.json", params=params)
        data = response.json()
        images = data.get("images_results", [])
        if images:
            return images[0].get("original")
        return DEFAULT_IMAGE_URL
    except Exception as e:
        print("Error fetching image:", e)
        return DEFAULT_IMAGE_URL

def fetch_and_save_news(country="us", category=None):
    print("fetch_and_save_news התחילה")
    params = {
        "apiKey": API_KEY,
        "country": country
    }
    if category:
        params["category"] = category

    response = requests.get(BASE_URL, params=params)
    print("Response status:", response.status_code)
    print("Response text:", response.text[:500])
    if response.status_code != 200:
        return {"error": f"Failed to fetch news, status: {response.status_code}"}

    data = response.json()
    saved_articles = []
    saved_ids = []

    for article in data.get("articles", []):
        content = article.get("description") or article.get("content")
        if not content:
            continue

        news_id = str(uuid.uuid4())
        title = article.get("title", "")
        source = article.get("source", {}).get("name", "")
        url = article.get("url", "")
        image_url = article.get("urlToImage") or fetch_image_from_google(title)
        cloudinary_url = upload_to_cloudinary(image_url, public_id=news_id)
        published_at = article.get("publishedAt")  


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
    fetch_and_save_news(country="us")