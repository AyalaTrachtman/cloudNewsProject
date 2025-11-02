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
import requests
from dotenv import load_dotenv
import os
load_dotenv()


API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
DEFAULT_IMAGE_URL = os.getenv("DEFAULT_IMAGE_URL")

# הגדרות Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("CLOUD_API_KEY"),
    api_secret=os.getenv("CLOUD_API_SECRET"),
    secure=True
)

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
DEFAULT_IMAGE_URL = os.getenv("DEFAULT_IMAGE_URL")

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


#def generate_image_bytes(prompt: str) -> BytesIO:
#    encoded_prompt = urllib.parse.quote(prompt)
#    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
 #   response = requests.get(image_url)
 #   response.raise_for_status()
#    image_bytes = BytesIO(response.content)
#    return image_bytes

def get_real_image_url(entities):
    """
    מקבלת רשימת entities ומחזירה כתובת תמונה אמיתית מ-Unsplash.
    אם אין תוצאה - מחזירה תמונה ברירת מחדל.
    """
    if not entities:
        query = "news"
    else:
        # תומך גם ברשימת מחרוזות וגם ברשימת מילונים
        if isinstance(entities[0], dict):
            query = ", ".join([e.get('text', '') for e in entities if 'text' in e])
        else:
            query = ", ".join(entities)

    url = f"https://api.unsplash.com/photos/random?query={requests.utils.quote(query)}&client_id={UNSPLASH_ACCESS_KEY}&orientation=landscape"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("urls", {}).get("regular", DEFAULT_IMAGE_URL)
    except Exception as e:
        print("Unsplash fetch error:", e)
        return DEFAULT_IMAGE_URL

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
            print(f"Skipping article from {source_name}")
            continue

        content = article.get("description") or article.get("content")
        if not content:
            continue

        title = article.get("title", "")
        source = article.get("source", {}).get("name", "")
        url = article.get("url", "")
        published_at = article.get("publishedAt")

        if news_exists(url):
            print(f"Article already exists: {url}")
            continue

        news_id = str(uuid.uuid4())

        analysis = analyze_article(title, content)
        entities = analysis.get("entities", [])

        # אם אין ישויות, ניצור ישות אחת מהכותרת כדי לקבל תמונה רלוונטית
        if not entities:
           entities = [{"text": title}]

        for e in entities:
            if 'score' in e:
                e['score'] = safe_float(e['score'])

        image_url = article.get("urlToImage") or get_real_image_url(entities)
        cloudinary_url = upload_to_cloudinary(image_url, public_id=news_id)

        if not cloudinary_url or "res.cloudinary.com" not in cloudinary_url:
           print("Cloudinary upload failed, fetching new image from Unsplash...")
           cloudinary_url = get_real_image_url(entities)
           cloudinary_url = upload_to_cloudinary(cloudinary_url, public_id=news_id)



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

def fix_missing_images_in_firebase():
    """
    מעדכנת כתבות קיימות ב-Firebase שאין להן תמונה מ-Cloudinary.
    במידה ואין תמונה או שהתמונה לא הועלתה ל-Cloudinary,
    תישלף תמונה רלוונטית מ-Unsplash לפי שדה ה-entities ותועלה ל-Cloudinary.
    """
    print("Checking existing news for missing images...")
    all_news = get_all_news()

    if not all_news:
        print("No news found in Firebase.")
        return

    fixed_count = 0

    for article in all_news:
        news_id = article.get("id")
        image_url = article.get("image_url", "")
        entities = article.get("entities", [])
        title = article.get("title", "news")

        if not entities:
            entities = [{"text": title}]

        if not image_url or "res.cloudinary.com" not in image_url:
            print(f"⚠ Fixing image for article: {title[:50]}...")
            new_image_url = get_real_image_url(entities)
            cloudinary_url = upload_to_cloudinary(new_image_url, public_id=news_id)

            if not cloudinary_url or "res.cloudinary.com" not in cloudinary_url:
                cloudinary_url = DEFAULT_IMAGE_URL

            article["image_url"] = cloudinary_url
            save_news(news_id, article)
            fixed_count += 1

    print(f"Finished fixing images. {fixed_count} articles updated.")



if __name__ == "__main__":
   fetch_and_save_news()

