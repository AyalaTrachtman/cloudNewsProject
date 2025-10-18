import sys
import requests

API_KEY = "cf0598a600744dbb8092ef66ea26ae2b"
BASE_URL = "https://newsapi.org/v2/top-headlines"

# קלט מהמשתמש (מדינה וקטגוריה)
country = sys.argv[1] if len(sys.argv) > 1 else "il"
category = sys.argv[2] if len(sys.argv) > 2 else None

params = {
    "apiKey": API_KEY,
    "country": country
}

if category:
    params["category"] = category

response = requests.get(BASE_URL, params=params)
print(response.status_code)
print(response.text)
