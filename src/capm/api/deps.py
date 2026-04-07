from fastapi import Depends, HTTPException, Request
from src.capm.domain.interfaces import IMetricRepository
from src.capm.domain.repositories import SQLiteMetricRepository


def get_db() -> IMetricRepository:
    return SQLiteMetricRepository()


def verify_api_key(request: Request):
    from fastapi import HTTPException
    from src.capm.config import settings

    key = request.headers.get("x-api-key")
    if not key or key != settings.secret_trigger_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
