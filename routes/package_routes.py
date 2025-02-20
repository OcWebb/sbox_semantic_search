from fastapi import APIRouter, Depends
from typing import List
from services import FacepunchService
from dependencies import get_facepunch_service
from auth import verify_api_key

router = APIRouter(prefix="/package")

@router.get("/fetch/all/", dependencies=[Depends(verify_api_key)])
def fetch_all(
    facepunch_service: FacepunchService = Depends(get_facepunch_service)
) -> List[dict]:
    return facepunch_service.fetch_all_packages()

@router.get("/fetch/recently-created/", dependencies=[Depends(verify_api_key)])
def fetch_recently_created(
    take: int,
    skip: int,
    facepunch_service: FacepunchService = Depends(get_facepunch_service)
) -> List[dict]:
    return facepunch_service.fetch_recently_created_packages(take, skip)

@router.get("/fetch/recently-updated/", dependencies=[Depends(verify_api_key)])
def fetch_recently_updated_facepunch(
    take: int,
    skip: int,
    facepunch_service: FacepunchService = Depends(get_facepunch_service)
) -> List[dict]:
    return facepunch_service.fetch_recently_updated_packages(take, skip)