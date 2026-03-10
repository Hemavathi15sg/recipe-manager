"""
Search service — thin orchestrator.

All business logic lives in the focused sub-modules:
  - validation  : input parsing & coercion
  - filters     : filtering pipeline
  - ranking     : scoring & sorting
  - formatting  : response shaping & pagination
  - cache       : result caching

This function contains *no* business logic: it only wires the modules
together and handles cross-cutting concerns (caching, logging).
"""
import logging
from typing import Optional

from models import Recipe, User, SAMPLE_RECIPES
from search.cache import build_cache, make_cache_key, InMemoryCache, NullCache
from search.config import ENABLE_FUZZY_SEARCH
from search.filters import apply_all_filters, preprocess_query
from search.formatting import paginate
from search.ranking import rank_recipes
from search.validation import SearchRequest

logger = logging.getLogger(__name__)

# Module-level cache instance (shared across requests in a single process).
_cache: InMemoryCache | NullCache = build_cache()


def search_recipes(request_data: dict, user: User) -> dict:
    """Search recipes and return a paginated, ranked response.

    Args:
        request_data: Raw request dict (typically from the API layer).
            ``None`` values are coerced to safe defaults by ``SearchRequest``.
        user: The requesting user.  ``dietary_restrictions`` may be ``None``
            (legacy callers); it is normalised to ``[]`` before use.

    Returns:
        Paginated response dict with keys ``results``, ``page``,
        ``page_size``, ``total``, ``has_more``.
    """
    logger.debug("search_recipes called for user=%s request=%s", user.name, request_data)

    # ------------------------------------------------------------------
    # 1. Validate & normalise input
    # ------------------------------------------------------------------
    req = SearchRequest.model_validate(request_data)

    # Merge user dietary restrictions with any restrictions in the request.
    # user.dietary_restrictions may be None for legacy User instances.
    user_restrictions: list[str] = user.dietary_restrictions or []
    effective_restrictions = list({*user_restrictions, *req.dietary_restrictions})

    query = req.query
    if ENABLE_FUZZY_SEARCH and query:
        query = preprocess_query(query)

    # ------------------------------------------------------------------
    # 2. Cache lookup (keyed on normalised request params only)
    # ------------------------------------------------------------------
    cache_payload = {
        "query": query,
        "dietary_restrictions": sorted(effective_restrictions),
        "cuisine": req.cuisine,
        "max_prep_time": req.max_prep_time,
        "difficulty": req.difficulty,
        "min_rating": req.min_rating,
    }
    cache_key = make_cache_key(cache_payload)
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    # ------------------------------------------------------------------
    # 3. Retrieve recipes
    # ------------------------------------------------------------------
    all_recipes: list[Recipe] = SAMPLE_RECIPES

    # ------------------------------------------------------------------
    # 4. Filter (optimised pipeline)
    # ------------------------------------------------------------------
    filtered = apply_all_filters(
        recipes=all_recipes,
        query=query,
        dietary_restrictions=effective_restrictions,
        cuisine=req.cuisine,
        max_prep_time=req.max_prep_time,
        difficulty=req.difficulty,
        min_rating=req.min_rating,
    )

    # ------------------------------------------------------------------
    # 5. Rank
    # ------------------------------------------------------------------
    ranked = rank_recipes(filtered, query)

    # ------------------------------------------------------------------
    # 6. Paginate & format
    # ------------------------------------------------------------------
    response = paginate(ranked)

    # ------------------------------------------------------------------
    # 7. Cache store
    # ------------------------------------------------------------------
    _cache.set(cache_key, response)

    return response


def clear_search_cache() -> None:
    """Clear the module-level search cache (used by admin endpoints / tests)."""
    _cache.clear()
