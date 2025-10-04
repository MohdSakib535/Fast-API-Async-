from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth.utils import AccessTokenBearer
from app.Database.session import get_db
from .schemas import SeedRequest, SeedResponse
from .service import run_seed


seed_router = APIRouter(
    prefix="/seed",
    tags=["Seeder"],
)


@seed_router.post("/run", response_model=SeedResponse, status_code=status.HTTP_201_CREATED)
async def seed_database(
    payload: SeedRequest,
    db: AsyncSession = Depends(get_db),
    # _: dict = Depends(AccessTokenBearer()),
) -> SeedResponse:
    try:
        return await run_seed(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
