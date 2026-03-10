"""
Response formatting and pagination.
"""
import logging
from typing import List

from models import Recipe
from search.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

logger = logging.getLogger(__name__)


def format_recipe(recipe: Recipe) -> dict:
    """Convert a *Recipe* instance to a JSON-serialisable dict."""
    return {
        "id": str(recipe.id),
        "name": recipe.name,
        "ingredients": recipe.ingredients,
        "dietary_tags": recipe.dietary_tags,
        "cuisine": recipe.cuisine,
        "prep_time_minutes": recipe.prep_time_minutes,
        "difficulty": recipe.difficulty,
        "rating": recipe.avg_rating,
    }


def paginate(recipes: List[Recipe], page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> dict:
    """Slice *recipes* to the requested page and return a response envelope.

    Args:
        recipes: Full ranked result set.
        page: 1-based page number.
        page_size: Number of results per page (capped at MAX_PAGE_SIZE).

    Returns:
        Dict with keys ``results``, ``page``, ``page_size``, ``total``,
        ``has_more``.
    """
    # Clamp page_size to a safe maximum
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    page = max(page, 1)

    start = (page - 1) * page_size
    end = start + page_size
    page_recipes = recipes[start:end]

    logger.debug(
        "Page %d: showing %d–%d of %d",
        page,
        start + 1,
        min(end, len(recipes)),
        len(recipes),
    )

    return {
        "results": [format_recipe(r) for r in page_recipes],
        "page": page,
        "page_size": page_size,
        "total": len(recipes),
        "has_more": end < len(recipes),
    }
