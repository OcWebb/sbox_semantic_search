from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
import os
from dotenv import load_dotenv
import secrets

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def generate_api_key() -> str:
    """Generate a secure API key using secrets module"""
    return secrets.token_urlsafe(32)

async def verify_api_key(
    api_key_header: Optional[str] = Security(api_key_header)
) -> str:
    if api_key_header and api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API Key"
    )