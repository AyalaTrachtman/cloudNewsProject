import os
import requests
from dotenv import load_dotenv

# טוענים את משתני הסביבה
load_dotenv()



API_URL = os.getenv("BACKEND_API_URL")  # http://localhost:8000

def get_news_by_topic(topic: str):
    """
    שולף חדשות לפי נושא מה־Backend
    """
    try:
        response = requests.get(f"{API_URL}/news?topic={topic}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print("Error fetching news:", e)
        return []

def get_news_by_id(news_id: str):
    """
    שולף ידיעה בודדת לפי ID
    """
    try:
        response = requests.get(f"{API_URL}/news/{news_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print("Error fetching news by ID:", e)
        return {}
