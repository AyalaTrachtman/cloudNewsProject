import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_image(file_path: str) -> str:
    """
    מעלה תמונה ל-Cloudinary ומחזיר את ה-URL שלה
    """
    try:
        result = cloudinary.uploader.upload(file_path)
        return result['secure_url']  # URL מוכן לשימוש בפרונט
    except Exception as e:
        print("Error uploading image:", e)
        return ""

def get_image(public_id: str) -> str:
    """
    שולף URL של תמונה קיימת לפי public_id
    """
    try:
        image = cloudinary.api.resource(public_id)
        return image['secure_url']
    except Exception as e:
        print("Error fetching image:", e)
        return ""
