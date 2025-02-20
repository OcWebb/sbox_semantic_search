from typing import List
from fastapi import APIRouter, Depends
from services import PineconeService, OpenAiService
from dependencies import get_pinecone_service, get_openai_service
from models import SearchRequest

router = APIRouter(prefix="/search")

@router.post("/")
def search(
    request: SearchRequest,
    pinecone_service: PineconeService = Depends(get_pinecone_service),
    openai_service: OpenAiService = Depends(get_openai_service)
) -> List[dict]:
    filter_dict = {}
    if len(request.type_filter) > 0:
        filter_dict = {"Type": {"$in": request.type_filter}}

    query_embedding, _ = openai_service.get_embedding(request.query)
    results = pinecone_service.search_pinecone(
        query_embedding, request.take, request.skip, filter_dict
    )
    if len(results) == 0:
        return []
    
    return [{
        "id": result.id,
        "metadata": result.metadata,
    } for result in results]