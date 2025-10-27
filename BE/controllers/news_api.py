import requests
from .firebase_db import save_news
from .huggingface_analyzer import analyze_article
import uuid
from transformers import pipeline
import numpy as np
import cloudinary
import cloudinary.uploader
import urllib.parse
import requests
from io import BytesIO
from .firebase_db import news_exists
import cloudinary.uploader
from .firebase_db import get_all_news, update_news



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

def upload_to_cloudinary(image_input, public_id=None):
    """
    מקבלת URL או BytesIO ומעלה ל-Cloudinary.
    משתמשת ב-fallback רק אם GET נכשל.
    """
    try:
        # אם זה URL
        if isinstance(image_input, str):
            try:
                response = requests.get(image_input, timeout=10)
                response.raise_for_status()
                image_bytes = BytesIO(response.content)
                image_bytes.seek(0)
            except Exception as e:
                print("URL לא זמין או GET נכשל, נשתמש ב-fallback:", e)
                image_bytes = generate_image_bytes(public_id or "fallback")
                image_bytes.seek(0)
            
            return cloudinary.uploader.upload(
                image_bytes,
                public_id=public_id,
                resource_type="image",
                timeout=15
            )["secure_url"]

        # אם זה BytesIO
        if isinstance(image_input, BytesIO):
            image_input.seek(0)
            return cloudinary.uploader.upload(
                image_input,
                public_id=public_id,
                resource_type="image",
                timeout=15
            )["secure_url"]

    except Exception as e:
        print("Cloudinary upload failed, משתמשים ב-fallback:", e)
        fallback = generate_image_bytes(public_id or "fallback")
        fallback.seek(0)
        return cloudinary.uploader.upload(
            fallback,
            public_id=public_id,
            resource_type="image",
            timeout=15
        )["secure_url"]


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
#if _name_ == "main":
    #test_text = "The government announced new economic reforms and tax cuts today."
   # print("Testing classification on sample text:")
   # print(classify_article(test_text))


def summarize_article(content, max_chars=200):
    if not content:
        return ""
    return content[:max_chars] + "..." if len(content) > max_chars else content

def safe_float(x):
    return float(x) if isinstance(x, (np.float32, np.float64)) else x

def generate_image_bytes(prompt: str) -> BytesIO:
   
    # Encode פרומפט ל-URL
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    
    
    # מורידה את התמונה כ-Bytes
    response = requests.get(image_url)
    response.raise_for_status()
    image_bytes = BytesIO(response.content)
    
    return image_bytes


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

        title = article.get("title", "")
        source = article.get("source", {}).get("name", "")
        url = article.get("url", "")
        published_at = article.get("publishedAt")  

        # בדיקה אם הכתבה כבר קיימת
        if news_exists(url):
            print(f"⚠ Article already exists: {url}")
            continue

        # אם לא קיימת – ממשיכים ושומרים
        news_id = str(uuid.uuid4())
        image_url = article.get("urlToImage") or generate_image_bytes(title)
        cloudinary_url = upload_to_cloudinary(image_url, public_id=news_id)
        print(f"Uploaded to Cloudinary: {cloudinary_url}")  # מדפיס את ה-URL מה-Cloudinary

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

def upload_missing_or_fallback_images(max_retries=3):
    articles = get_all_news()
    for article in articles:
        news_id = article["id"]
        original_url = article.get("original_image_url")
        current_url = article.get("image_url")

        # אם אין URL מקורי – נשאיר אותו כמו שהוא
        if not original_url:
            continue

        # נבדוק אם התמונה הנוכחית היא fallback/ציור (שונה מהמקור)
        if current_url.startswith("https://res.cloudinary.com/") and current_url != original_url:
            # ננסה שוב להעלות את המקור
            success = False
            for attempt in range(max_retries):
                try:
                    response = requests.get(original_url, timeout=10)
                    response.raise_for_status()
                    image_bytes = BytesIO(response.content)
                    image_bytes.seek(0)
                    new_url = upload_to_cloudinary(image_bytes, public_id=news_id)
                    update_news(news_id, {"image_url": new_url})
                    print(f"Updated Cloudinary with original image for: {article['title']}")
                    success = True
                    break
                except Exception as e:
                    print(f"Attempt {attempt+1} failed for {article['title']}: {e}")

            if not success:
                # fallback: תמונה אמיתית לפי entities
                entities_text = " ".join([e["name"] for e in article.get("entities", [])])
                if entities_text:
                    try:
                        search_url = f"https://source.unsplash.com/800x600/?{urllib.parse.quote(entities_text)}"
                        response = requests.get(search_url)
                        response.raise_for_status()
                        image_bytes = BytesIO(response.content)
                        image_bytes.seek(0)
                        new_url = upload_to_cloudinary(image_bytes, public_id=news_id)
                        update_news(news_id, {"image_url": new_url})
                        print(f"Updated Cloudinary fallback image for: {article['title']}")
                    except Exception as e:
                        print(f"Fallback search failed for {article['title']}: {e}, keeping original Cloudinary URL")

if __name__ == "__main__":

    upload_missing_or_fallback_images()
    fetch_and_save_news(country="us")
    