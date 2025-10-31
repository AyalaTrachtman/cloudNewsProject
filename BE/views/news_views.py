from fastapi import APIRouter
from ..controllers.firebase_db import save_news, get_news, update_news, delete_news, get_all_news
from ..controllers.news_api import fetch_and_save_news
from ..models.news_model import News

router = APIRouter()

# CREATE
@router.post("/news/{news_id}")
def create_news(news_id: str, news: News):
    save_news(news_id, news.dict())
    return {"message": "News saved"}

# READ
@router.get("/news/{news_id}")
def read_news(news_id: str):
    data = get_news(news_id)
    return data if data else {"error": "News not found"}

# UPDATE
@router.put("/news/{news_id}")
def edit_news(news_id: str, news: News):
    update_news(news_id, news.dict())
    return {"message": "News updated"}

# DELETE
@router.delete("/news/{news_id}")
def remove_news(news_id: str):
    delete_news(news_id)
    return {"message": "News deleted"}

# READ ALL
@router.get("/news")
def read_all_news():
    return get_all_news()

# FETCH NEWS (כולל Hugging Face)
@router.get("/fetch-news")
def fetch_news(country: str = "us", category: str = None):
    result = fetch_and_save_news(country=country, category=category)
    return {
        "message": result["message"],
        "saved_count": len(result["articles"]),
        "ids": result["ids"]
    }

# TEST Firebase
@router.get("/test-firebase")
def test_firebase():
    test_id = "1"
    test_data = {"title": "שלום עולם", "content": "זוהי ידיעה לדוגמה"}
    save_news(test_id, test_data)
    return get_news(test_id)