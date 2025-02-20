from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    type_filter: list[str] = []
    take: int = 5
    skip: int = 0