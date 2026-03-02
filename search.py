"""
FlavorHub Search Engine - MONOLITH (847 lines)

WARNING: This is intentionally bad code for workshop learning.

ISSUES:
- God object anti-pattern (all concerns mixed)
- No separation: parsing, filtering, ranking, formatting all here
- No input validation
- Hard-coded business logic
- Zero tests
- Performance problems (O(n) scans)
- THE BUG: Line 145 - null handling error
"""
from typing import List, Dict, Optional, Any
from models import Recipe, User, SAMPLE_RECIPES
import re


# =============================================================================
# SECTION 1: Query Parsing (Lines 1-200)
# =============================================================================
# In real codebase, lots of parsing logic here...
# - URL parameter extraction
# - Query string normalization
# - Synonym handling
# - Typo correction (commented out, never finished)
# ... [150 lines omitted for workshop]


def parse_search_request(request_data: dict) -> dict:
    """
    Parse raw search request.
    NO VALIDATION! (Issue: accepts any garbage input)
    """
    return {
        "query": request_data.get("query", ""),
        "dietary_restrictions": request_data.get("dietary_restrictions"),  # Can be None!
        "cuisine": request_data.get("cuisine"),
        "max_prep_time": request_data.get("max_prep_time"),
        "difficulty": request_data.get("difficulty"),
        "min_rating": request_data.get("min_rating", 0.0)
    }


# =============================================================================
# SECTION 2: Filtering Logic (Lines 201-450)
# =============================================================================
# 7 different filters all mixed together here...


def filter_by_query(recipes: List[Recipe], query: str) -> List[Recipe]:
    """Filter recipes by search query (ingredients or name)"""
    if not query:
        return recipes
    
    query_lower = query.lower()
    results = []
    
    for recipe in recipes:
        # Check recipe name
        if query_lower in recipe.name.lower():
            results.append(recipe)
            continue
        
        # Check ingredients
        for ingredient in recipe.ingredients:
            if query_lower in ingredient.lower():
                results.append(recipe)
                break
    
    return results


def filter_by_cuisine(recipes: List[Recipe], cuisine: Optional[str]) -> List[Recipe]:
    """Filter by cuisine type"""
    if not cuisine:
        return recipes
    
    return [r for r in recipes if r.cuisine.lower() == cuisine.lower()]


def filter_by_prep_time(recipes: List[Recipe], max_time: Optional[int]) -> List[Recipe]:
    """Filter by maximum prep time"""
    if not max_time:
        return recipes
    
    return [r for r in recipes if r.prep_time_minutes <= max_time]


def filter_by_difficulty(recipes: List[Recipe], difficulty: Optional[str]) -> List[Recipe]:
    """Filter by difficulty level"""
    if not difficulty:
        return recipes
    
    return [r for r in recipes if r.difficulty.lower() == difficulty.lower()]


def filter_by_rating(recipes: List[Recipe], min_rating: float) -> List[Recipe]:
    """Filter by minimum rating"""
    return [r for r in recipes if r.avg_rating >= min_rating]


# ⚠️ THE BUG IS HERE ⚠️
def filter_by_dietary(recipes: List[Recipe], user: User) -> List[Recipe]:
    """
    Filter recipes based on user's dietary restrictions.
    
    LINE 145: THE PRODUCTION BUG!
    Assumes user.dietary_restrictions is a list,
    but it can be None for users without preferences.
    
    This causes: TypeError: 'NoneType' object is not iterable
    """
    # BUG: No null check before iterating!
    for restriction in user.dietary_restrictions:  # ← LINE 145: CRASHES IF None!
        recipes = [r for r in recipes if restriction in r.dietary_tags]
    
    return recipes


def apply_all_filters(recipes: List[Recipe], filters: dict, user: User) -> List[Recipe]:
    """
    Apply all filters sequentially.
    ISSUE: No optimization - applies in worst order for performance
    """
    results = recipes
    
    # Apply filters (inefficient order - should do most selective first)
    results = filter_by_query(results, filters["query"])
    results = filter_by_cuisine(results, filters["cuisine"])
    results = filter_by_prep_time(results, filters["max_prep_time"])
    results = filter_by_difficulty(results, filters["difficulty"])
    results = filter_by_rating(results, filters["min_rating"])
    
    # This is where it crashes for users with dietary_restrictions=None
    results = filter_by_dietary(results, user)
    
    return results


# =============================================================================
# SECTION 3: Ranking Logic (Lines 451-680)
# =============================================================================
# Ranking algorithm all hardcoded here...
# - Relevance scoring
# - Popularity boost
# - Freshness factor
# - Personalization (half-implemented)
# ... [230 lines of ranking code]


def calculate_relevance_score(recipe: Recipe, query: str) -> float:
    """Calculate how relevant recipe is to query"""
    score = 0.0
    query_lower = query.lower()
    
    # Exact name match
    if query_lower == recipe.name.lower():
        score += 10.0
    # Partial name match
    elif query_lower in recipe.name.lower():
        score += 5.0
    
    # Ingredient matches
    ingredient_matches = sum(1 for ing in recipe.ingredients if query_lower in ing.lower())
    score += ingredient_matches * 2.0
    
    return score


def rank_recipes(recipes: List[Recipe], query: str) -> List[Recipe]:
    """
    Rank recipes by relevance.
    ISSUE: Hard-coded weights, no A/B testing capability
    """
    if not query:
        # Default sort by rating
        return sorted(recipes, key=lambda r: r.avg_rating, reverse=True)
    
    # Calculate scores (in-memory, no caching)
    scored_recipes = []
    for recipe in recipes:
        relevance = calculate_relevance_score(recipe, query)
        rating_boost = recipe.avg_rating * 0.3
        final_score = relevance + rating_boost
        scored_recipes.append((final_score, recipe))
    
    # Sort by score
    scored_recipes.sort(key=lambda x: x[0], reverse=True)
    
    return [recipe for score, recipe in scored_recipes]


# =============================================================================
# SECTION 4: Response Formatting (Lines 681-847)
# =============================================================================
# Output formatting logic...
# - JSON serialization
# - Pagination
# - Response metadata
# - Error formatting (partial, inconsistent)
# ... [167 lines of formatting code]


def format_recipe_response(recipe: Recipe) -> dict:
    """Convert Recipe to API response format"""
    return {
        "id": str(recipe.id),
        "name": recipe.name,
        "ingredients": recipe.ingredients,
        "dietary_tags": recipe.dietary_tags,
        "cuisine": recipe.cuisine,
        "prep_time_minutes": recipe.prep_time_minutes,
        "difficulty": recipe.difficulty,
        "rating": recipe.avg_rating
    }


def paginate_results(recipes: List[Recipe], page: int = 1, page_size: int = 50) -> dict:
    """
    Paginate results.
    ISSUE: No actual pagination, just slicing (doesn't scale)
    """
    start = (page - 1) * page_size
    end = start + page_size
    
    page_recipes = recipes[start:end]
    
    return {
        "results": [format_recipe_response(r) for r in page_recipes],
        "page": page,
        "page_size": page_size,
        "total": len(recipes),
        "has_more": end < len(recipes)
    }


# =============================================================================
# MAIN SEARCH FUNCTION (Everything wired together)
# =============================================================================


def search_recipes(request_data: dict, user: User) -> dict:
    """
    Main search function - MONOLITHIC ENTRY POINT
    
    All concerns mixed together:
    - Parsing (no validation)
    - Filtering (no optimization)
    - Ranking (hard-coded)
    - Formatting (inflexible)
    
    THIS IS WHERE THE BUG MANIFESTS IN PRODUCTION
    """
    # Parse request (no validation)
    filters = parse_search_request(request_data)
    
    # Get all recipes (no caching, hits "database" every time)
    all_recipes = SAMPLE_RECIPES  # In real app: database query here
    
    # Apply filters (THIS CRASHES if user.dietary_restrictions is None)
    try:
        filtered_recipes = apply_all_filters(all_recipes, filters, user)
    except TypeError as e:
        # This is what production logs show:
        # TypeError: 'NoneType' object is not iterable at line 145
        raise e
    
    # Rank results (no caching)
    ranked_recipes = rank_recipes(filtered_recipes, filters["query"])
    
    # Paginate and format (hardcoded page size)
    response = paginate_results(ranked_recipes, page=1, page_size=50)
    
    return response


# =============================================================================
# ADDITIONAL ISSUES NOT SHOWN (but exist in full 847 lines):
# - No async operations (blocking I/O)
# - Hard-coded database connections (no pooling)
# - No error boundaries (any exception crashes everything)
# - Magic numbers everywhere (74 found by @search-architect)
# - No logging
# - No monitoring/metrics
# - Dead code (lots of commented-out failed experiments)
# =============================================================================
