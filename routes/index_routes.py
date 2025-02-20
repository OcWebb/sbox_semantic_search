from typing import List
from fastapi import APIRouter, Depends
from services import PineconeService, OpenAiService, FacepunchService
from dependencies import get_pinecone_service, get_openai_service, get_facepunch_service
from utils import get_embed_string, get_pinecone_vector_from_package
from auth import verify_api_key

router = APIRouter(prefix="/index")

@router.post("/delete/", dependencies=[Depends(verify_api_key)])
def delete(
    pinecone_service: PineconeService = Depends(get_pinecone_service)
) -> dict:
    pinecone_service.delete_index()
    return {"message": "Index deleted"}

@router.get("/fetch/recently-created/", dependencies=[Depends(verify_api_key)])
def fetch_recently_created(
    take: int,
    pinecone_service: PineconeService = Depends(get_pinecone_service)
) -> List[dict]:
    results = pinecone_service.fetch_recently_created_packages(take)
    return [{"id": result.id} for result in results]

@router.get("/fetch/recently-updated/", dependencies=[Depends(verify_api_key)])
def fetch_recently_updated(
    take: int,
    pinecone_service: PineconeService = Depends(get_pinecone_service)
) -> List[dict]:
    results = pinecone_service.fetch_recently_updated_packages(take)
    return [{
        "id": result.id,
        "updated": from_timestamp(result.metadata['Updated']),
        "timestamp": result.metadata['Updated'],
    } for result in results]

@router.post("/update/", dependencies=[Depends(verify_api_key)])
def index_update(
    facepunch_service: FacepunchService = Depends(get_facepunch_service),
    pinecone_service: PineconeService = Depends(get_pinecone_service),
    openai_service: OpenAiService = Depends(get_openai_service)
) -> dict:
    new_packages = fetch_newly_updated_packages(pinecone_service, facepunch_service)
    new_packages += fetch_newly_created_packages(pinecone_service, facepunch_service)
    embed_strings = [get_embed_string(package) for package in new_packages]
    embeddings_list, tokens = openai_service.get_embeddings(embed_strings)
    
    vectors = [get_pinecone_vector_from_package(embeddings_list[i], package) 
               for i, package in enumerate(new_packages)]

    if vectors:
        pinecone_service.upsert_embeddings(vectors)
        return {
            "message": f"Indexed {len(vectors)} packages with {tokens} tokens, cost ${openai_service.token_cost(tokens)}"
        }