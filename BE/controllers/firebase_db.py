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


# פונקציה לניקוי נתונים לפני שמירה ל-Firestore
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

# CREATE / UPDATE
def save_news(news_id, news_data):
    news_data = clean_for_firestore(news_data)
    doc_ref = db.collection("news").document(str(news_id))
    doc_ref.set(news_data)


# READ
def get_news(news_id):
    doc_ref = db.collection("news").document(str(news_id))
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None


# UPDATE בלבד
def update_news(news_id, news_data):
    news_data = clean_for_firestore(news_data)
    doc_ref = db.collection("news").document(str(news_id))
    doc_ref.update(news_data)


# DELETE
def delete_news(news_id):
    doc_ref = db.collection("news").document(str(news_id))
    doc_ref.delete()


# READ ALL
def get_all_news():
    """
    מחזיר רשימה של כל החדשות מ-Firestore.
    """
    news_collection = db.collection("news").stream()
    all_news = []
    for doc in news_collection:
        news_item = doc.to_dict()
        news_item["id"] = doc.id  # מוסיפים את מזהה המסמך
        all_news.append(news_item)
    return all_news
def news_exists(url):
    db = firestore.client()
    docs = db.collection("news").where("url", "==", url).stream()
    return any(docs)