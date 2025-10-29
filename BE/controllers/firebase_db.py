import os
import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np

# נתיב לקובץ credentials יחסית לתיקייה BE
cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firebase_credentials.json")

# אתחול Firebase רק פעם אחת
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# יצירת client של Firestore
db = firestore.client()


# ===== פונקציות עזר =====

def clean_for_firestore(data):
    """
    ממירה טיפוסים לא נתמכים (כמו np.float32, np.int64 וכו') לטיפוסים רגילים של Python.
    """
    if isinstance(data, dict):
        return {k: clean_for_firestore(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_for_firestore(v) for v in data]
    elif isinstance(data, np.generic):  # לדוגמה np.float32
        return data.item()
    else:
        return data


# ===== פעולות על חדשות =====

def save_news(news_id, news_data):
    news_data = clean_for_firestore(news_data)
    db.collection("news").document(str(news_id)).set(news_data)


def get_news(news_id):
    doc = db.collection("news").document(str(news_id)).get()
    return doc.to_dict() if doc.exists else None


def update_news(news_id, news_data):
    news_data = clean_for_firestore(news_data)
    db.collection("news").document(str(news_id)).update(news_data)


def delete_news(news_id):
    db.collection("news").document(str(news_id)).delete()


def get_all_news():
    """
    מחזיר רשימה של כל החדשות מ-Firestore.
    """
    news_collection = db.collection("news").stream()
    all_news = []
    for doc in news_collection:
        news_item = doc.to_dict()
        news_item["id"] = doc.id
        all_news.append(news_item)
    return all_news


def get_news_by_url(url):
    """
    מחפש כתבה לפי השדה 'url' כדי למנוע כפילויות.
    מחזיר רשימת מסמכים תואמים.
    """
    results = db.collection("news").where("url", "==", url).stream()
    return [r.to_dict() for r in results]

def delete_all_news():
    """
    מוחקת את כל הכתבות ב-Firestore.
    """
    news_collection = db.collection("news").stream()
    for doc in news_collection:
        doc.reference.delete()
    print("All news deleted.")

def news_exists(url: str) -> bool:
    """
    בודק אם כתבה עם ה-URL הזה כבר קיימת ב-Firestore.
    """
    results = db.collection("news").where("url", "==", url).stream()
    return any(True for _ in results)
