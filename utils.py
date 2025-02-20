from datetime import datetime
from dateutil import parser
from models import PineconeVector

def to_timestamp(date_str: str) -> int:
    return int(parser.isoparse(date_str).timestamp())

def from_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).isoformat()

def get_embed_string(package: dict) -> str:
    string = "Title:" + package['Title']
    if package['Summary']:
        string += ", Summary: " + package['Summary']
    if package["Tags"]:
        string += ", Tags:" + ", ".join(package["Tags"])
    return string

def get_pinecone_vector_from_package(
    embedding: list[float],
    facepunch_package: dict
) -> PineconeVector:
    return PineconeVector(
        id=facepunch_package["FullIdent"],
        values=embedding,
        metadata={
            "Title": facepunch_package["Title"],
            "FullIdent": facepunch_package["FullIdent"],
            "Tags": facepunch_package["Tags"],
            "Summary": facepunch_package["Summary"],
            "Type": facepunch_package["TypeName"],
            "Thumb": facepunch_package["Thumb"],
            "Updated": to_timestamp(facepunch_package["Updated"]),
            "Created": to_timestamp(facepunch_package["Created"])
        }
    )