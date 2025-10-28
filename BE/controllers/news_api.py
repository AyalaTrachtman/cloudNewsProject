import requests
from .firebase_db import save_news, news_exists, get_all_news, update_news
from .huggingface_analyzer import analyze_article
import uuid
from transformers import pipeline
import numpy as np
import cloudinary
import cloudinary.uploader
import urllib.parse
from io import BytesIO

API_KEY = "cf0598a600744dbb8092ef66ea26ae2b"
BASE_URL = "https://newsapi.org/v2/top-headlines"
DEFAULT_IMAGE_URL = "https://example.com/default-image.jpg"

cloudinary.config(
    cloud_name="dvzpm0jir",
    api_key="431769535972431",
    api_secret="rmagqBMWdt98g57lk84Y5YRvRTk",
    secure=True
)

TOPICS = [
    "Politics", "Finance", "Science", "Culture",
    "Sport", "Technology", "Health", "World"
]

classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)


def upload_to_cloudinary(image_input, public_id=None):
    try:
        if isinstance(image_input, str):
            r = requests.get(image_input, timeout=12)
            r.raise_for_status()
            img_bytes = BytesIO(r.content)
            img_bytes.seek(0)
            return cloudinary.uploader.upload(
                img_bytes,
                public_id=public_id,
                resource_type="image"
            )["secure_url"]

        if isinstance(image_input, BytesIO):
            image_input.seek(0)
            return cloudinary.uploader.upload(
                image_input,
                public_id=public_id,
                resource_type="image"
            )["secure_url"]

    except Exception as e:
        print("Cloudinary upload failed:", e)
        return None


def fetch_real_image_from_unsplash(query: str) -> BytesIO:
    query_encoded = urllib.parse.quote(query)
    url = f"https://source.unsplash.com/800x600/?{query_encoded}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    img_bytes = BytesIO(r.content)
    img_bytes.seek(0)
    return img_bytes


def classify_article(content):
    if not content:
        return "World"
    try:
        result = classifier(content[:512], TOPICS)
        return result["labels"][0]
    except:
        return "World"


def summarize_article(content, max_chars=200):
    if not content:
        return ""
    return content[:max_chars] + "..." if len(content) > max_chars else content


def safe_float(x):
    return float(x) if isinstance(x, (np.float32, np.float64)) else x


def fetch_and_save_news(country="us", category=None):
    params = {"apiKey": API_KEY, "country": country}
    if category:
        params["category"] = category

    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        return

    data = response.json()
    for article in data.get("articles", []):
        content = article.get("description") or article.get("content")
        if not content:
            continue

        title = article.get("title", "")
        url = article.get("url", "")
        if news_exists(url):
            continue

        news_id = str(uuid.uuid4())

        # 🔹 שומר את התמונה המקורית בלבד (מהכתבה)
        original_image_url = article.get("urlToImage") or DEFAULT_IMAGE_URL

        # 🔹 רק image_url עובר דרך Cloudinary / fallback
        if "pollinations.ai" in original_image_url:
            cloud_url = original_image_url
        else:
            cloud_url = upload_to_cloudinary(original_image_url, public_id=news_id)
            if not cloud_url:
                try:
                    fallback = fetch_real_image_from_unsplash(title)
                    cloud_url = upload_to_cloudinary(fallback, public_id=news_id)
                except:
                    cloud_url = DEFAULT_IMAGE_URL

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
            "source": article.get("source", {}).get("name", ""),
            "image_url": cloud_url,                # Cloudinary או fallback
            "original_image_url": original_image_url,  # מהכתבה, תמיד מקורית
            "classification": classification,
            "entities": entities,
            "published_at": article.get("publishedAt")
        }

        save_news(news_id, news_data)


def fill_missing_original_image():
    articles = get_all_news()
    for article in articles:
        if "original_image_url" not in article or not article["original_image_url"]:
            original_image_url = article.get("image_url") or DEFAULT_IMAGE_URL
            update_news(article["id"], {"original_image_url": original_image_url})
            print(f"Filled original_image_url for: {article['title']}")


def upload_missing_or_fallback_images(max_retries=3):
    articles = get_all_news()
    for article in articles:
        news_id = article["id"]
        original_url = article.get("original_image_url")
        current_url = article.get("image_url")

        if current_url and original_url and "pollinations.ai" in current_url:
            continue

        success = False
        for _ in range(max_retries):
            try:
                if original_url:
                    r = requests.get(original_url, timeout=10)
                    r.raise_for_status()
                    img = BytesIO(r.content)
                    img.seek(0)
                    new_url = upload_to_cloudinary(img, public_id=news_id)
                    update_news(news_id, {"image_url": new_url})
                    success = True
                    break
            except:
                pass

        if not success:
            entities_text = " ".join([e.get("word", "") for e in article.get("entities", [])]) or "news"
            try:
                fallback = fetch_real_image_from_unsplash(entities_text)
                url = upload_to_cloudinary(fallback, public_id=news_id)
            except:
                url = DEFAULT_IMAGE_URL
            update_news(news_id, {"image_url": url})


if __name__ == "__main__":
    fill_missing_original_image()
    upload_missing_or_fallback_images()
    fetch_and_save_news(country="us")
