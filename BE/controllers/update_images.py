from .firebase_db import get_all_news, update_news
from .image_fetcher import fetch_image_for_entity
from .cloudinary_utils import upload_to_cloudinary



def update_all_images():
    """
    עובר על כל החדשות:
    - אם אין תמונה: מוצא לפי Entities → מעלה ל-Cloudinary → מעדכן Firestore
    - אם כבר יש תמונה: מעלה אותה מחדש ל-Cloudinary → מעדכן Firestore
    """
    articles = get_all_news()

    for article in articles:
        article_id = article["id"]
        current_image_url = article.get("image_url")
        entities = article.get("entities", [])

        # אם אין תמונה קיימת, נשתמש ב-entity הראשון כדי למצוא תמונה
        if not current_image_url:
            if not entities:
                print(f"[NO ENTITIES] Cannot assign image to article {article_id}")
                continue

            first_entity = entities[0]
            entity_word = first_entity["word"] if isinstance(first_entity, dict) else first_entity
            print(f"[FETCH] Searching image for '{entity_word}'")
            image_to_upload = fetch_image_for_entity(entity_word)
        else:
            # אם יש תמונה קיימת ב-Firebase או urlToImage, נעלה אותה מחדש
            image_to_upload = current_image_url
            print(f"[EXISTING] Using current image for article {article_id}")

        # העלאה ל-Cloudinary
        print(f"[UPLOAD] Uploading to Cloudinary...")
        cloud_url = upload_to_cloudinary(image_to_upload)

        if cloud_url:
            update_news(article_id, {"image_url": cloud_url})
            print(f"[UPDATED] ✅ Article {article_id} updated with Cloudinary image.")
        else:
            print(f"[FAILED] ❌ Could not upload image for article {article_id}")


if __name__ == "__main__":
    update_all_images()
