from typing import List
from fastapi import APIRouter, Depends
from services import PineconeService, OpenAiService, FacepunchService
from dependencies import get_pinecone_service, get_openai_service, get_facepunch_service
from utils import from_timestamp, get_embed_string, get_pinecone_vector_from_package, to_timestamp
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


def fetch_newly_updated_packages(
        pinecone_service: PineconeService,
        facepunch_service: FacepunchService) -> list[dict]:
    TAKE = 100
    most_recent = pinecone_service.fetch_recently_updated_packages(1)[0]
    most_recent_timestamp = most_recent.metadata['Updated']
    facepunch_recent = facepunch_service.fetch_recently_updated_packages(TAKE, 0)

    iteration = 0
    while to_timestamp(facepunch_recent[-1]['Updated']) > most_recent_timestamp and iteration < 10:
        iteration += 1
        facepunch_recent = facepunch_service.fetch_recently_updated_packages(TAKE, TAKE*iteration)

    if iteration == 10:
        return []
    
    packages_newer_than_most_recent = [x for x in facepunch_recent if to_timestamp(x['Updated']) > most_recent_timestamp]
    packages_newer_than_most_recent.sort(key=lambda x: to_timestamp(x['Updated']), reverse=True)

    return packages_newer_than_most_recent


def fetch_newly_created_packages(
        pinecone_service: PineconeService, 
        facepunch_service: FacepunchService) -> list[dict]:
    TAKE = 100
    most_recent = pinecone_service.fetch_recently_created_packages(1)[0]
    most_recent_timestamp = most_recent.metadata['Created']
    facepunch_recent = facepunch_service.fetch_recently_created_packages(TAKE, 0)

    iteration = 0
    while to_timestamp(facepunch_recent[-1]['Created']) > most_recent_timestamp and iteration < 10:
        iteration += 1
        facepunch_recent = facepunch_service.fetch_recently_created_packages(TAKE, TAKE*iteration)

    if iteration == 10:
        return []
    
    packages_newer_than_most_recent = [x for x in facepunch_recent if to_timestamp(x['Created']) > most_recent_timestamp]
    packages_newer_than_most_recent.sort(key=lambda x: to_timestamp(x['Created']), reverse=True)

    return packages_newer_than_most_recent