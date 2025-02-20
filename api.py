from datetime import datetime
import os
from fastapi import FastAPI, HTTPException, Depends
from functools import lru_cache
import uvicorn
from dotenv import load_dotenv
from dateutil import parser

from models import PineconeVector, SearchRequest
from services import PineconeService, OpenAiService, FacepunchService

load_dotenv()

@lru_cache()
def get_pinecone_service() -> PineconeService:
    return PineconeService(api_key=os.getenv("PINECONE_KEY"), index_name=os.getenv("PINECONE_INDEX"))

@lru_cache()
def get_openai_service() -> OpenAiService:
    return OpenAiService(api_key=os.getenv("OPENAI_KEY"), embedding_model=os.getenv("EMBEDDING_MODEL"))

@lru_cache()
def get_facepunch_service() -> FacepunchService:
    return FacepunchService(base_url=os.getenv("FACEPUNCH_BASE_URL"))

app = FastAPI()



@app.get("/package/fetch/all/")
def fetch_all(facepunch_service: FacepunchService = Depends(get_facepunch_service)) -> list[dict]:
    return facepunch_service.fetch_all_packages_from_file("data/packages.json")[0:5]


@app.get("/package/fetch/recently-created/")
def fetch_recently_created(take: int, 
                           skip: int, 
                           facepunch_service: FacepunchService = Depends(get_facepunch_service)) -> list[dict]:
    return facepunch_service.fetch_recently_created_packages(take, skip)
    # return [{'id': x['FullIdent']} for x in facepunch_service.fetch_recently_created_packages(take, skip)]


@app.get("/package/fetch/recently-updated/")
def fetch_recently_updated_facepunch(take: int, 
                           skip: int, 
                           facepunch_service: FacepunchService = Depends(get_facepunch_service)) -> list[dict]:
    results = facepunch_service.fetch_recently_updated_packages(take, skip)
    # return [{
    #     "id": result['FullIdent'],
    #     "date": from_timestamp(to_timestamp(result['Updated'])),
    #     # "metadata": result.metadata,
    # } for result in results]

    return results



@app.post("/index/delete/")
def delete(pinecone_service: PineconeService = Depends(get_pinecone_service)) -> dict:
    pinecone_service.delete_index()
    return {"message": "Index deleted"}


@app.get("/index/fetch/recently-created/")
def fetch_recently_created(take: int,
                           pinecone_service: PineconeService = Depends(get_pinecone_service)) -> list[dict]:
    results = pinecone_service.fetch_recently_created_packages(take)
    return [{
        "id": result.id,
        # "metadata": result.metadata,
    } for result in results]


@app.get("/index/fetch/recently-updated/")
def fetch_recently_updated(take: int,
                           pinecone_service: PineconeService = Depends(get_pinecone_service)) -> list[dict]:
    results = pinecone_service.fetch_recently_updated_packages(take)
    return [{
        "id": result.id,
        "updated": from_timestamp(result.metadata['Updated']),
        "timestamp": result.metadata['Updated'],
        # "metadata": result.metadata,
    } for result in results]


@app.get("/index/fetch/needs-update/")
def fetch_needs_update(pinecone_service: PineconeService = Depends(get_pinecone_service),
                       facepunch_service: FacepunchService = Depends(get_facepunch_service)) -> list[dict]:
    new_packages = fetch_newly_updated_packages(pinecone_service, facepunch_service)
    new_packages += fetch_newly_created_packages(pinecone_service, facepunch_service)

    return [{
        "full_ident": result['FullIdent'],
        # "metadata": result.metadata,
    } for result in new_packages]


@app.post("/index/update/")
def index_update(facepunch_service: FacepunchService = Depends(get_facepunch_service),
            pinecone_service: PineconeService = Depends(get_pinecone_service),
            openai_service: OpenAiService = Depends(get_openai_service)) -> dict:
    new_packages = fetch_newly_updated_packages(pinecone_service, facepunch_service)
    new_packages += fetch_newly_created_packages(pinecone_service, facepunch_service)
    embed_strings = [get_embed_string(package) for package in new_packages]
    embeddings_list, tokens = openai_service.get_embeddings(embed_strings)

    vectors = [get_pinecone_vector_from_package(embeddings_list[i], package) for i, package in enumerate(new_packages)]

    if vectors:
        pinecone_service.upsert_embeddings(vectors)
        return {"message": f"Indexed {len(vectors)} packages with {tokens} tokens, cost ${openai_service.token_cost(tokens)}"}

@app.post("/index/reindex/")
def reindex(facepunch_service: FacepunchService = Depends(get_facepunch_service),
                pinecone_service: PineconeService = Depends(get_pinecone_service),
                openai_service: OpenAiService = Depends(get_openai_service)) -> dict:
    packages = facepunch_service.fetch_all_packages()
    embed_strings = [get_embed_string(package) for package in packages]
    embeddings_list, tokens = openai_service.get_embeddings(embed_strings)

    vectors = [get_pinecone_vector_from_package(embeddings_list[i], package) for i, package in enumerate(packages)]

    if vectors:
        pinecone_service.upsert_embeddings(vectors)
        return {"message": f"Indexed {len(vectors)} packages with {tokens} tokens, cost ${openai_service.token_cost(tokens)}"}


@app.post("/search/")
def search(request: SearchRequest, 
           pinecone_service: PineconeService = Depends(get_pinecone_service),
           openai_service: OpenAiService = Depends(get_openai_service)) -> list[dict]:
    filter_dict = {}
    if len(request.type_filter) > 0:
        filter_dict = {"Type": {"$in": request.type_filter }}

    query_embedding, _ = openai_service.get_embedding(request.query)
    results = pinecone_service.search_pinecone(query_embedding, request.take, request.skip, filter_dict)
    if len(results) == 0:
        return []
    
    return [{
        "id": result.id,
        "metadata": result.metadata,
    } for result in results]
    

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


def get_embed_string(package: dict) -> str:
    string = "Title:" + package['Title']
    if package['Summary']:
        string += ", Summary: " + package['Summary']
    if package["Tags"]:
        string += ", Tags:" + ", ".join(package["Tags"])
    return string

def get_pinecone_vector_from_package(embedding: list[float], facepunch_package: dict) -> PineconeVector:
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

def to_timestamp(date_str: str) -> int:
            return int(parser.isoparse(date_str).timestamp())

def from_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).isoformat()

if __name__ == "__main__":
    print("Swagger UI available at http://localhost:8080/docs")
    uvicorn.run(app, host="localhost", port=8080)
