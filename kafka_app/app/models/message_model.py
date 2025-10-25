# app/models/message_model.py
import json
from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class Message:
    id: str
    title: str
    content: str
    url: str
    source: str
    image_url: Optional[str] = None
    classification: Optional[str] = None
    entities: Optional[List[str]] = None
    published_at: Optional[str] = None 


    def to_json(self) -> str:
        """ממיר את האובייקט ל־JSON כדי לשלוח ל־Kafka"""
        return json.dumps(asdict(self), ensure_ascii=False)

    @staticmethod
    def from_json(json_str: str):
        """מקבל JSON מ־Kafka וממיר בחזרה ל־Message object"""
        data = json.loads(json_str)
        return Message(**data)
