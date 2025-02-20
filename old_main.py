import os
import sys
import json
import requests
import openai
from pinecone import Pinecone
from tenacity import retry, stop_after_attempt, wait_exponential
from logging import getLogger
from dotenv import load_dotenv

from models import PineconeVector

load_dotenv()

# pinecone = Pinecone(api_key=os.getenv("PINECONE_KEY"))
# openai.api_key = os.getenv("OPENAI_API_KEY")
logger = getLogger(__name__)

# @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=10))
# def get_embeddings_with_retry(query):
#     return get_embeddings([query])[0]

# def get_embeddings(text: list[str]) -> tuple[list[list[float]], int]:
#     """ Get embeddings and tokens used for a list of text strings. """
#     if len(text) > 2048:
#         embeddings = []
#         total_tokens = 0
#         for i in range(0, len(text), 2048):
#             response = openai.Embedding.create(input=text[i:i+2048], engine=os.getenv("EMBEDDING_MODEL"))
#             total_tokens += response["usage"]["total_tokens"]
#             embeddings.extend([data["embedding"] for data in response["data"]])
            
#         return (embeddings, total_tokens)
#     else:
#         response = openai.Embedding.create(input=text, engine=os.getenv("EMBEDDING_MODEL"))
#         embeddings = [data["embedding"] for data in response["data"]]
#         total_tokens = response["usage"]["total_tokens"]
        
#         return (embeddings, total_tokens)

# @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=10))
# def search_pinecone_with_retry(embedding, take, skip, filter_dict):
#     topk = take + skip
#     response = index.query(
#         vector=embedding,
#         top_k=topk,
#         include_values=True,
#         include_metadata=True,
#         filter=filter_dict
#     )
    
#     return [PineconeVector(
#         id=result["id"],
#         values=result["values"],
#         metadata=result["metadata"]
#     ) for result in response["matches"][skip:take+skip]]

# def search_pinecone(query: str, take: int = 5, skip: int = 0, filter_dict={}) -> list[PineconeVector]:
#     try:
#         embedding = get_embeddings_with_retry(query)
#         if not embedding:
#             return []
#         return search_pinecone_with_retry(embedding, take, skip, filter_dict)
#     except Exception as e:
#         logger.exception("Error in search_pinecone:")
#         return []
    
# def fetch_all_packages_from_facepunch() -> list[dict]:
#     packages = []
#     try:
#         skip = 0
#         while True:
#             query_params = {"skip": skip, "take": 500}
#             response = requests.get(os.getenv("BASE_URL") + os.getenv("PACKAGES_LIST_URI"), params=query_params)
#             response.raise_for_status()
#             json_data = response.json()
#             packages.extend(json_data['Packages'])
#             if len(json_data['Packages']) < 500:
#                 break
#             skip += 500
#             logger.info(f"Fetching packages, current count: {len(packages)}")
#         return packages
#     except requests.exceptions.RequestException as e:
#         print("Error fetching data from facepunch backend.\nError:", e)
#         return []

def fetch_all_packages_from_file(filename: str) -> list[dict]:
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File {filename} not found.")
        return []

# def upsert_embeddings(data: list[PineconeVector]):
#     for i in range(0, len(data), 100):
#         index.upsert(vectors=[vector.to_dict() for vector in data[i:i+100]])

def get_embed_string(package: dict) -> str:
    string = package['Title']
    if package['Summary']:
        string += " - " + package['Summary']
    if package["Tags"]:
        string += " - " + ", ".join(package["Tags"])
    return string

def refresh_pinecone_embeddings():
    packages = fetch_all_packages_from_facepunch()
    if not packages:
        sys.exit(1)

    embed_strings = [get_embed_string(package) for package in packages]
    embeddings_list = get_embeddings(embed_strings)

    vectors = [PineconeVector(
        id=package["FullIdent"],
        values=embeddings_list[i],
        metadata={
            "Title": package["Title"],
            "FullIdent": package["FullIdent"],
            "Tags": package["Tags"],
            "Summary": package["Summary"],
            "EmbedString": embed_strings[i],
            "Type": package["Type"]
        }
    ) for i, package in enumerate(packages)]

    if vectors:
        upsert_embeddings(vectors)


def cli_search():
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        print("Please add a query to search for.")
        sys.exit()

    results = search_pinecone(query, 30)
    for i, result in enumerate(results, 1):
        print(f"{i}) Asset Title: {result.metadata['Title']}")
        print(f"    Asset Summary: {result.metadata['Summary']}")
        print(f"    Ident: {result.metadata['FullIdent']}\n")


if __name__ == "__main__":
    # refresh_pinecone_embeddings()
    # cli_search()
    exit()