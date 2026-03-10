"""
Recipe ranking algorithms.

Only the active ``hybrid_v3`` algorithm is kept.  Dead branches
(``basic``, ``weighted_v2``, ``ml_v1``) have been removed — they are
preserved in git history if ever needed.
"""
import logging
from typing import List

from models import Recipe
from search.config import (
    EXACT_NAME_SCORE,
    INGREDIENT_MATCH_SCORE,
    PARTIAL_NAME_SCORE,
    POPULARITY_WEIGHT,
    RATING_WEIGHT,
    RELEVANCE_WEIGHT,
    USE_POPULARITY_BOOST,
)

logger = logging.getLogger(__name__)


def _relevance_score(recipe: Recipe, query: str) -> float:
    """Return a relevance score for *recipe* against *query*."""
    if not query:
        return 0.0

    query_lower = query.lower()
    score = 0.0

    if query_lower == recipe.name.lower():
        score += EXACT_NAME_SCORE
    elif query_lower in recipe.name.lower():
        score += PARTIAL_NAME_SCORE

    ingredient_matches = sum(1 for ing in recipe.ingredients if query_lower in ing.lower())
    score += ingredient_matches * INGREDIENT_MATCH_SCORE

    return score


def _popularity_score(recipe: Recipe) -> float:
    """Return a popularity score (currently based on avg_rating)."""
    return recipe.avg_rating * POPULARITY_WEIGHT


def rank_recipes(recipes: List[Recipe], query: str) -> List[Recipe]:
    """Rank recipes using the hybrid_v3 algorithm.

    When there is no query, results are sorted by rating descending.
    When there is a query, each recipe receives a composite score:
    ``relevance × RELEVANCE_WEIGHT + rating × RATING_WEIGHT [+ popularity]``.
    """
    if not recipes:
        return recipes

    if not query:
        return sorted(recipes, key=lambda r: r.avg_rating, reverse=True)

    scored: list[tuple[float, Recipe]] = []
    for recipe in recipes:
        relevance = _relevance_score(recipe, query)
        score = (
            relevance * RELEVANCE_WEIGHT
            + recipe.avg_rating * RATING_WEIGHT
            + (_popularity_score(recipe) if USE_POPULARITY_BOOST else 0.0)
        )
        scored.append((score, recipe))
        logger.debug(
            "%s: relevance=%.2f rating=%.2f → final=%.2f",
            recipe.name,
            relevance,
            recipe.avg_rating,
            score,
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [recipe for _, recipe in scored]
