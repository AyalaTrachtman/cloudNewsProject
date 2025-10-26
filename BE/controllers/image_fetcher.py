import requests

# ⚠️ הכניסי כאן את ה-API KEY של Pexels
PEXELS_API_KEY = "YOUR_PEXELS_API_KEY"
DEFAULT_IMAGE_URL = "https://placehold.co/600x400?text=No+Image"

def fetch_image_for_entity(entity: str) -> str:
    """
    מקבל מחרוזת (entity) ומחזיר URL של תמונה מתאימה מ-Pexels.
    """
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        params = {"query": entity, "per_page": 1}
        response = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
        data = response.json()

        photos = data.get("photos", [])
        if not photos:
            return DEFAULT_IMAGE_URL

        return photos[0]["src"]["large"]
    except Exception as e:
        print(f"[Pexels] Error fetching image: {e}")
        return DEFAULT_IMAGE_URL
