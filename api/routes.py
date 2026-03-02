"""
API Routes for FlavorHub Recipe Manager

WARNING: Intentionally minimal error handling for workshop.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from models import SAMPLE_USERS
from search import search_recipes

router = APIRouter()


def get_user_from_token(authorization: Optional[str] = Header(None)):
    """
    Mock user authentication.
    In workshop: Gets user with dietary_restrictions=None to trigger bug
    """
    if not authorization:
        # Default to Bob (has dietary_restrictions=None) - triggers the bug!
        return SAMPLE_USERS[1]
    
    # In real app: decode JWT, lookup user, etc.
    # For workshop: just return Bob (the problematic user)
    return SAMPLE_USERS[1]


@router.post("/search")
async def search_endpoint(
    request_data: dict,
    current_user = None  # Will be dependency injected
):
    """
    Search recipes endpoint.
    
    THIS IS WHERE THE BUG HAPPENS in production!
    
    When request comes from user without dietary preferences,
    search.py line 145 crashes.
    
    Example request that crashes:
    {
        "query": "pasta",
        "dietary_restrictions": null,
        "cuisine": "Italian"
    }
    """
    # Get user (in workshop: returns user with dietary_restrictions=None)
    user = current_user or get_user_from_token()
    
    try:
        # This is where it crashes!
        results = search_recipes(request_data, user)
        return results
    
    except TypeError as e:
        # Production error logs show this:
        if "'NoneType' object is not iterable" in str(e):
            raise HTTPException(
                status_code=500,
                detail="Internal server error in search filtering"
            )
        raise


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "recipe-search"}
