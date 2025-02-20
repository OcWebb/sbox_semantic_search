from functools import lru_cache
import os
from services import PineconeService, OpenAiService, FacepunchService
from dotenv import load_dotenv

load_dotenv()

@lru_cache()
def get_pinecone_service() -> PineconeService:
    return PineconeService(
        api_key=os.getenv("PINECONE_KEY"),
        index_name=os.getenv("PINECONE_INDEX")
    )

@lru_cache()
def get_openai_service() -> OpenAiService:
    return OpenAiService(
        api_key=os.getenv("OPENAI_KEY"),
        embedding_model=os.getenv("EMBEDDING_MODEL")
    )

@lru_cache()
def get_facepunch_service() -> FacepunchService:
    return FacepunchService(
        base_url=os.getenv("FACEPUNCH_BASE_URL")
    )
