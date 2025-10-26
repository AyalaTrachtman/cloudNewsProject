import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os
load_dotenv()

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)


def upload_to_cloudinary(image_url: str) -> str | None:
    """
    מקבל URL של תמונה ומעלה ל-Cloudinary.
    מחזיר URL מאובטח של Cloudinary או None במקרה של כישלון.
    """
    try:
        result = cloudinary.uploader.upload(image_url)
        return result.get("secure_url")
    except Exception as e:
        print(f"[Cloudinary] Error uploading image: {e}")
        return None
