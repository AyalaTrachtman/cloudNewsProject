from pydantic import BaseModel
from typing import Optional, List

class News(BaseModel):
    id: Optional[str]  # UUID – נוצרת אוטומטית
    title: str
    content: Optional[str]
    url: Optional[str]
    source: Optional[str]
    image_url: Optional[str]  # לינק לתמונה
    classification: Optional[str]  # תוצאה של Hugging Face Zero-shot
    entities: Optional[List[str]] = []  # רשימת שמות, מקומות, וכו'
