"""
API Routes for FlavorHub Recipe Manager
"""
from fastapi import APIRouter, Header
from typing import Optional

from models import SAMPLE_USERS
from search import search_recipes
from search.validation import SearchRequest

router = APIRouter()


def get_user_from_token(authorization: Optional[str] = Header(None)):
    """Mock user authentication — returns a sample user."""
    # In a real app: decode JWT, look up user from DB, etc.
    if not authorization:
        return SAMPLE_USERS[1]  # Bob (dietary_restrictions=None) — handled safely
    return SAMPLE_USERS[1]


@router.post("/search")
async def search_endpoint(
    request_data: SearchRequest,
    current_user=None,
):
    """Search recipes.

    ``dietary_restrictions: null`` in the request body is safely coerced to
    ``[]`` by ``SearchRequest`` before it reaches any filter logic, so the
    TypeError that previously crashed 23% of requests can no longer occur.
    """
    user = current_user or get_user_from_token()
    results = search_recipes(request_data.model_dump(), user)
    return results


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "recipe-search"}
