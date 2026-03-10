"""
FlavorHub Search Engine - MONOLITHIC SEARCH MODULE (1103 lines)

⚠️ CRITICAL ARCHITECTURAL DEBT ⚠️

This file has grown organically over 18 months from 150 lines to 1103 lines.
It embodies the "God Object" anti-pattern - doing everything related to search.

WHAT'S IN THIS FILE (everything!):
- Database connection management (hard-coded, no pooling)
- Query parsing (3 different versions, only one used)
- Input validation (none - accepts garbage)
- Filtering logic (5 filter functions + 3 deprecated versions)
- Dietary restriction handling (THE BUG: Line 447)
- Ranking algorithms (2 active, 3 commented-out experiments)
- A/B testing variants (feature flags everywhere)
- Response formatting (JSON, XML support half-implemented)
- Pagination (inefficient, loads everything in memory)
- Caching logic (broken, causes stale data - Issue #183)
- Metrics collection (manual counters, no aggregation)
- Error handling (inconsistent, swallows exceptions)
- Debug logging (print statements everywhere)
- Helper utilities (miscellaneous functions)

THE PRODUCTION BUG:
- LINE 447: filter_by_dietary() crashes when user.dietary_restrictions is None
- Affects 23% of users (those without dietary preferences)
- Causes: TypeError: 'NoneType' object is not iterable
- Workaround: Frontend team hardcodes dietary_restrictions=[] (breaks API contract)

ARCHITECTURE SMELLS:
- 74 magic numbers (no constants)
- 12 feature flags (unclear which are active)
- Database connection created per request (no pooling)
- 3 versions of ranking algorithm (unclear which is production)
- Dead code from failed A/B tests (never removed)
- No separation of concerns (validation, business logic, persistence all mixed)
- 0% test coverage (too coupled to test)

TEAM NOTES:
- "TODO: Refactor this monster" (added 9 months ago)
- "FIXME: This is getting out of hand" (added 6 months ago)
- "HACK: Don't judge me" (appears 8 times)
- Last person who tried to refactor quit after 2 weeks

NEEDED (from @search-architect analysis):
1. Break into 4 modules: validation, filtering, aggregation, formatting
2. Add Pydantic validation layer
3. Fix null handling (Issue #247)
4. Extract database connection to connection pool
5. Remove dead code and obsolete experiments
6. Add comprehensive test coverage
7. Document which feature flags are active
8. Replace magic numbers with named constants

REFACTOR PLAN:
- Traditional approach: 3-4 days, high risk of regression
- With Spec Kit + Agents: 2 hours, governed by constitution, trackable specs
"""
from typing import List, Dict, Optional, Any
from models import Recipe, User, SAMPLE_RECIPES
import re
import time
import json


# =============================================================================
# CONFIGURATION & FEATURE FLAGS
# =============================================================================
# TODO: Move these to config file (they're scattered everywhere)

# Database config (HARDCODED! Should be environment variables)
DB_HOST = "localhost"  # FIXME: Use connection pool
DB_PORT = 5432
DB_NAME = "flavorhub"
DB_USER = "admin"  # WARNING: Credentials in code!
DB_MAX_CONNECTIONS = 50  # Not actually used
DB_TIMEOUT = 30

# Search behavior flags
ENABLE_FUZZY_SEARCH = True  # A/B test started Q3 2024
ENABLE_SEMANTIC_RANKING = False  # Experiment failed, never removed
USE_LEGACY_FILTERS = False  # Should be deleted
ENABLE_CACHE = True  # Currently broken (Issue #183)
CACHE_TTL_SECONDS = 300  # 5 minutes

# Ranking algorithm flags (unclear which is production!)
RANKING_ALGORITHM = "hybrid_v3"  # Options: basic, weighted_v2, hybrid_v3, ml_v1
USE_POPULARITY_BOOST = True
POPULARITY_WEIGHT = 0.25  # Magic number
RATING_WEIGHT = 0.3  # Another magic number
RELEVANCE_WEIGHT = 0.45  # Yet another magic number

# Pagination settings
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MAX_RESULTS_IN_MEMORY = 10000  # Performance killer

# Metrics counters (should use proper monitoring service)
search_count = 0
filter_count = 0
error_count = 0
cache_hits = 0
cache_misses = 0

# Debug mode (prints everywhere when True)
DEBUG = True  # TODO: Remove before production (added 12 months ago)


# =============================================================================
# SECTION 1: DATABASE CONNECTION (Should be in separate module)
# =============================================================================
# HACK: Don't judge me - this works but it's terrible

def get_database_connection():
    """
    Create database connection per request.
    
    ISSUES:
    - No connection pooling (creates new connection every time)
    - Credentials hardcoded
    - No retry logic
    - Connections never properly closed
    - Not actually used (we use SAMPLE_RECIPES instead)
    """
    if DEBUG:
        print(f"[DEBUG] Connecting to database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    try:
        # Simulated connection (not real)
        connection = {
            "host": DB_HOST,
            "port": DB_PORT,
            "database": DB_NAME,
            "connected": True,
            "timestamp": time.time()
        }
        if DEBUG:
            print("[DEBUG] Database connection established")
        return connection
    except Exception as e:
        error_count += 1  # This doesn't actually work (needs global)
        if DEBUG:
            print(f"[ERROR] Database connection failed: {e}")
        return None


def close_database_connection(connection):
    """
    Close database connection.
    NOTE: This is never actually called (connections leak)
    """
    if connection and connection.get("connected"):
        connection["connected"] = False
        if DEBUG:
            print("[DEBUG] Database connection closed")


# Deprecated: Old connection function (kept for "just in case")
# def create_db_connection_v1():
#     """Old version - had timeout issues"""
#     import psycopg2
#     return psycopg2.connect(
#         host=DB_HOST,
#         port=DB_PORT,
#         database=DB_NAME,
#         user=DB_USER,
#         password="password123"  # Kept in git history!
#     )


# =============================================================================
# SECTION 2: QUERY PARSING (Multiple versions, only one used)
# =============================================================================


def parse_search_request(request_data: dict) -> dict:
    """
    Parse raw search request - CURRENT VERSION (v3)
    
    NO VALIDATION! Accepts any garbage input.
    This is the root cause of multiple production issues.
    
    Issues:
    - No type checking (accepts strings for numbers)
    - No bounds checking (negative numbers, huge values)
    - No sanitization (SQL injection risk if we used real DB)
    - dietary_restrictions can be None (causes bug in filtering)
    
    TODO: Replace with Pydantic models (Issue #247)
    """
    global search_count
    search_count += 1  # Manual metrics (should use proper monitoring)
    
    if DEBUG:
        print(f"[DEBUG] Parsing search request: {request_data}")
    
    # Extract fields without any validation
    parsed = {
        "query": request_data.get("query", ""),
        "dietary_restrictions": request_data.get("dietary_restrictions"),  # Can be None!
        "cuisine": request_data.get("cuisine"),
        "max_prep_time": request_data.get("max_prep_time"),
        "difficulty": request_data.get("difficulty"),
        "min_rating": request_data.get("min_rating", 0.0)
    }
    
    # Feature flag: Fuzzy search preprocessing
    if ENABLE_FUZZY_SEARCH and parsed["query"]:
        parsed["query"] = preprocess_fuzzy_query(parsed["query"])
    
    if DEBUG:
        print(f"[DEBUG] Parsed filters: {parsed}")
    
    return parsed


def preprocess_fuzzy_query(query: str) -> str:
    """
    Preprocess query for fuzzy search.
    Part of A/B test started Q3 2024 - unclear if it helped.
    """
    # Remove extra whitespace
    query = " ".join(query.split())
    
    # Remove special characters (maybe too aggressive?)
    query = re.sub(r'[^\w\s]', '', query)
    
    if DEBUG:
        print(f"[DEBUG] Fuzzy preprocessed query: {query}")
    
    return query


# Deprecated: Old parsing function v2 (kept "just in case")
# def parse_search_request_v2(request_data: dict) -> dict:
#     """
#     v2 parsing - had issues with None handling
#     Replaced by v3 but never deleted
#     """
#     query = request_data.get("query", "")
#     dietary = request_data.get("dietary_restrictions", [])  # Default to empty list
#     cuisine = request_data.get("cuisine", None)
#     max_time = int(request_data.get("max_prep_time", 999))  # Can crash!
#     difficulty = request_data.get("difficulty", None)
#     min_rating = float(request_data.get("min_rating", 0.0))  # Can crash!
#     
#     return {
#         "query": query,
#         "dietary_restrictions": dietary,
#         "cuisine": cuisine,
#         "max_prep_time": max_time,
#         "difficulty": difficulty,
#         "min_rating": min_rating
#     }


# Deprecated: Original parsing function v1 (archaeological artifact)
# def parse_search_request_v1(request_data: dict) -> dict:
#     """v1 - The original. Simple times."""
#     return request_data  # Just passed everything through!


# =============================================================================
# SECTION 3: FILTERING LOGIC (5 active functions + 3 deprecated)
# =============================================================================


def filter_by_query(recipes: List[Recipe], query: str) -> List[Recipe]:
    """
    Filter recipes by search query (ingredients or name).
    
    Performance note: O(n*m) where n=recipes, m=avg ingredients
    No indexing, no optimization. Works fine for <1000 recipes.
    """
    if not query:
        if DEBUG:
            print("[DEBUG] No query filter applied")
        return recipes
    
    query_lower = query.lower()
    results = []
    match_count = 0
    
    if DEBUG:
        print(f"[DEBUG] Filtering by query: '{query}'")
    
    for recipe in recipes:
        # Check recipe name (exact match scores higher in ranking)
        if query_lower in recipe.name.lower():
            results.append(recipe)
            match_count += 1
            if DEBUG:
                print(f"[DEBUG]   - Matched name: {recipe.name}")
            continue
        
        # Check ingredients (more lenient matching)
        for ingredient in recipe.ingredients:
            if query_lower in ingredient.lower():
                results.append(recipe)
                match_count += 1
                if DEBUG:
                    print(f"[DEBUG]   - Matched ingredient in: {recipe.name}")
                break
    
    if DEBUG:
        print(f"[DEBUG] Query filter: {len(results)} matches found")
    
    global filter_count
    filter_count += match_count
    
    return results


def filter_by_cuisine(recipes: List[Recipe], cuisine: Optional[str]) -> List[Recipe]:
    """
    Filter by cuisine type.
    
    Issues:
    - Case-sensitive matching (should normalize)
    - No fuzzy matching (Italian vs italian vs ITALIAN)
    - No cuisine aliases (e.g., "Asian" should match Thai, Chinese, Japanese)
    """
    if not cuisine:
        return recipes
    
    if DEBUG:
        print(f"[DEBUG] Filtering by cuisine: '{cuisine}'")
    
    # Simple exact match (case-insensitive at least)
    results = [r for r in recipes if r.cuisine.lower() == cuisine.lower()]
    
    if DEBUG:
        print(f"[DEBUG] Cuisine filter: {len(results)} matches")
    
    return results


def filter_by_prep_time(recipes: List[Recipe], max_time: Optional[int]) -> List[Recipe]:
    """
    Filter by maximum prep time.
    
    Issues:
    - No validation of max_time (could be negative, could be string)
    - No handling of None prep_time in Recipe (assumes always set)
    - Magic number: What if someone wants recipes >180 minutes?
    """
    if not max_time:
        return recipes
    
    if DEBUG:
        print(f"[DEBUG] Filtering by max prep time: {max_time} minutes")
    
    try:
        # Hope max_time is actually a number!
        results = [r for r in recipes if r.prep_time_minutes <= max_time]
        
        if DEBUG:
            print(f"[DEBUG] Prep time filter: {len(results)} matches")
        
        return results
    except TypeError as e:
        # Silent failure - returns all recipes if something goes wrong
        if DEBUG:
            print(f"[ERROR] Prep time filter failed: {e}")
        global error_count
        error_count += 1
        return recipes


def filter_by_difficulty(recipes: List[Recipe], difficulty: Optional[str]) -> List[Recipe]:
    """
    Filter by difficulty level.
    
    Expected values: "beginner", "intermediate", "advanced"
    But there's no validation, so API could send anything.
    """
    if not difficulty:
        return recipes
    
    if DEBUG:
        print(f"[DEBUG] Filtering by difficulty: '{difficulty}'")
    
    # Case-insensitive match
    results = [r for r in recipes if r.difficulty.lower() == difficulty.lower()]
    
    if DEBUG:
        print(f"[DEBUG] Difficulty filter: {len(results)} matches")
    
    return results


def filter_by_rating(recipes: List[Recipe], min_rating: float) -> List[Recipe]:
    """
    Filter by minimum rating.
    
    Issues:
    - No validation (min_rating could be >5.0 or negative)
    - No handling of recipes without ratings
    - Magic number: Rating scale assumed to be 0-5
    """
    if DEBUG:
        print(f"[DEBUG] Filtering by min rating: {min_rating}")
    
    try:
        results = [r for r in recipes if r.avg_rating >= min_rating]
        
        if DEBUG:
            print(f"[DEBUG] Rating filter: {len(results)} matches")
        
        return results
    except (TypeError, AttributeError) as e:
        if DEBUG:
            print(f"[ERROR] Rating filter failed: {e}")
        global error_count
        error_count += 1
        return recipes


# ⚠️ THE PRODUCTION BUG IS IN THIS FUNCTION ⚠️
def filter_by_dietary(recipes: List[Recipe], user: User) -> List[Recipe]:
    """
    Filter recipes based on user's dietary restrictions.
    
    🔥 LINE 447: THE PRODUCTION BUG! 🔥
    
    This function assumes user.dietary_restrictions is always a list.
    However, 23% of users have dietary_restrictions=None (no preferences).
    
    When None is passed, the iteration fails with:
    TypeError: 'NoneType' object is not iterable
    
    This bug crashes the search for 1 in 4 users!
    
    Root cause: No input validation + API contract violation
    Quick fix: Add null check
    Proper fix: Pydantic validation at API boundary
    
    Reported: Issue #447 (2 weeks ago)
    Impact: 23% of search requests fail
    Workaround: Frontend hardcodes dietary_restrictions=[] (breaks semantics)
    """
    if DEBUG:
        print(f"[DEBUG] Filtering by dietary restrictions: {user.dietary_restrictions}")
    
    # 🔥 BUG: No null check before iterating! 🔥
    for restriction in user.dietary_restrictions:  # ← LINE 447: CRASHES IF None!
        recipes = [r for r in recipes if restriction in r.dietary_tags]
        
        if DEBUG:
            print(f"[DEBUG]   - Applied restriction: {restriction}, {len(recipes)} remaining")
    
    if DEBUG:
        print(f"[DEBUG] Dietary filter: {len(recipes)} matches")
    
    return recipes


# Deprecated dietary filter v1 (worked but was too strict)
# def filter_by_dietary_v1(recipes: List[Recipe], restrictions: List[str]) -> List[Recipe]:
#     """
#     Old version - removed recipes missing ANY tag
#     Too aggressive: vegetarian users couldn't see vegan recipes
#     """
#     if not restrictions:
#         return recipes
#     
#     results = []
#     for recipe in recipes:
#         # Recipe must have ALL restrictions
#         if all(r in recipe.dietary_tags for r in restrictions):
#             results.append(recipe)
#     
#     return results


# Deprecated dietary filter v2 (attempted fix, made it worse)
# def filter_by_dietary_v2(recipes: List[Recipe], user: User) -> List[Recipe]:
#     """
#     v2 - tried to be smart about tag matching
#     Led to weird bugs like kosher users seeing pork recipes
#     """
#     if not user or not user.dietary_restrictions:
#         return recipes
#     
#     # Tried to implement tag hierarchy (failed spectacularly)
#     tag_hierarchy = {
#         "vegan": ["vegetarian", "plant-based"],
#         "gluten-free": ["celiac-safe"],
#         "kosher": ["halal"]  # This was incorrect!
#     }
#     
#     results = []
#     for recipe in recipes:
#         safe = True
#         for restriction in user.dietary_restrictions:
#             acceptable_tags = tag_hierarchy.get(restriction, [restriction])
#             if not any(tag in recipe.dietary_tags for tag in acceptable_tags):
#                 safe = False
#                 break
#         if safe:
#             results.append(recipe)
#     
#     return results


def apply_all_filters(recipes: List[Recipe], filters: dict, user: User) -> List[Recipe]:
    """
    Apply all filters sequentially.
    
    Performance issues:
    - No query optimization (applies in arbitrary order)
    - Should apply most selective filters first (min_rating, cuisine)
    - Currently applies broadest first (query matching)
    - Loads everything in memory (doesn't scale past 10k recipes)
    
    The bug manifests here when filter_by_dietary() is called.
    """
    if DEBUG:
        print(f"[DEBUG] Applying filters to {len(recipes)} recipes")
        start_time = time.time()
    
    results = recipes
    
    # Apply filters (inefficient order - should do most selective first)
    results = filter_by_query(results, filters["query"])
    if DEBUG:
        print(f"[DEBUG]   After query filter: {len(results)} recipes")
    
    results = filter_by_cuisine(results, filters["cuisine"])
    if DEBUG:
        print(f"[DEBUG]   After cuisine filter: {len(results)} recipes")
    
    results = filter_by_prep_time(results, filters["max_prep_time"])
    if DEBUG:
        print(f"[DEBUG]   After prep time filter: {len(results)} recipes")
    
    results = filter_by_difficulty(results, filters["difficulty"])
    if DEBUG:
        print(f"[DEBUG]   After difficulty filter: {len(results)} recipes")
    
    results = filter_by_rating(results, filters["min_rating"])
    if DEBUG:
        print(f"[DEBUG]   After rating filter: {len(results)} recipes")
    
    # 🔥 This is where the crash happens for users with dietary_restrictions=None 🔥
    results = filter_by_dietary(results, user)
    if DEBUG:
        print(f"[DEBUG]   After dietary filter: {len(results)} recipes")
    
    if DEBUG:
        elapsed = time.time() - start_time
        print(f"[DEBUG] All filters applied in {elapsed:.3f}s")
    
    return results


# =============================================================================
# SECTION 4: RANKING ALGORITHMS (Multiple versions, unclear which is active)
# =============================================================================


def calculate_relevance_score(recipe: Recipe, query: str) -> float:
    """
    Calculate how relevant recipe is to search query.
    
    Scoring logic (magic numbers everywhere):
    - Exact name match: +10.0
    - Partial name match: +5.0
    - Each ingredient match: +2.0
    
    Issues:
    - Weights not tuned (just guessed)
    - No TF-IDF or proper text search
    - No stemming or lemmatization
    - Case-sensitive in some paths (bugs)
    """
    score = 0.0
    query_lower = query.lower()
    
    if DEBUG:
        print(f"[DEBUG] Calculating relevance for: {recipe.name}")
    
    # Exact name match (highest score)
    if query_lower == recipe.name.lower():
        score += 10.0  # Magic number #1
        if DEBUG:
            print(f"[DEBUG]   - Exact name match: +10.0")
    # Partial name match
    elif query_lower in recipe.name.lower():
        score += 5.0  # Magic number #2
        if DEBUG:
            print(f"[DEBUG]   - Partial name match: +5.0")
    
    # Ingredient matches (each match adds to score)
    ingredient_matches = sum(1 for ing in recipe.ingredients if query_lower in ing.lower())
    ingredient_score = ingredient_matches * 2.0  # Magic number #3
    score += ingredient_score
    
    if DEBUG and ingredient_matches > 0:
        print(f"[DEBUG]   - Ingredient matches: {ingredient_matches}, +{ingredient_score}")
    
    if DEBUG:
        print(f"[DEBUG]   - Final relevance score: {score}")
    
    return score


def calculate_popularity_score(recipe: Recipe) -> float:
    """
    Calculate popularity score based on ratings.
    
    Currently just returns avg_rating, but structured for future expansion:
    - View count
    - Save count  
    - Share count
    - Recent trending boost
    
    All of this is TODO (never implemented).
    """
    # Future: weighted formula combining multiple signals
    # For now: just use rating
    popularity = recipe.avg_rating * POPULARITY_WEIGHT  # Magic weight from config
    
    if DEBUG:
        print(f"[DEBUG] Popularity score for {recipe.name}: {popularity}")
    
    return popularity


def rank_recipes(recipes: List[Recipe], query: str) -> List[Recipe]:
    """
    Rank recipes by relevance using active ranking algorithm.
    
    Algorithm selection via RANKING_ALGORITHM flag:
    - "basic": Simple rating sort
    - "weighted_v2": Rating + relevance with fixed weights
    - "hybrid_v3": Current production (allegedly)
    - "ml_v1": ML model (never finished, flag exists anyway)
    
    Issues:
    - No A/B testing framework
    - Unclear which algorithm is actually running in production
    - No metrics to compare algorithm performance
    - Results not cached (re-calculated every request)
    """
    if DEBUG:
        print(f"[DEBUG] Ranking {len(recipes)} recipes with algorithm: {RANKING_ALGORITHM}")
        start_time = time.time()
    
    if RANKING_ALGORITHM == "basic":
        # Just sort by rating (simple but effective)
        results = sorted(recipes, key=lambda r: r.avg_rating, reverse=True)
    
    elif RANKING_ALGORITHM == "weighted_v2":
        # Weighted combination (old version, might still be in use?)
        scored_recipes = []
        for recipe in recipes:
            if query:
                relevance = calculate_relevance_score(recipe, query)
                score = (relevance * 0.6) + (recipe.avg_rating * 0.4)  # Magic weights
            else:
                score = recipe.avg_rating
            scored_recipes.append((score, recipe))
        
        scored_recipes.sort(key=lambda x: x[0], reverse=True)
        results = [recipe for score, recipe in scored_recipes]
    
    elif RANKING_ALGORITHM == "hybrid_v3":
        # Current "production" algorithm (supposedly)
        if not query:
            # No query = just sort by rating
            results = sorted(recipes, key=lambda r: r.avg_rating, reverse=True)
        else:
            # Complex hybrid scoring
            scored_recipes = []
            for recipe in recipes:
                relevance = calculate_relevance_score(recipe, query)
                rating_component = recipe.avg_rating * RATING_WEIGHT  # 0.3
                relevance_component = relevance * RELEVANCE_WEIGHT  # 0.45
                
                # Popularity boost (if enabled)
                popularity_boost = 0.0
                if USE_POPULARITY_BOOST:
                    popularity_boost = calculate_popularity_score(recipe)
                
                final_score = relevance_component + rating_component + popularity_boost
                scored_recipes.append((final_score, recipe))
                
                if DEBUG:
                    print(f"[DEBUG]   {recipe.name}: rel={relevance_component:.2f}, "
                          f"rating={rating_component:.2f}, pop={popularity_boost:.2f}, "
                          f"final={final_score:.2f}")
            
            # Sort by final score
            scored_recipes.sort(key=lambda x: x[0], reverse=True)
            results = [recipe for score, recipe in scored_recipes]
    
    elif RANKING_ALGORITHM == "ml_v1":
        # ML-based ranking (never implemented, just returns sorted by rating)
        if DEBUG:
            print("[DEBUG] ML ranking not implemented, falling back to rating sort")
        results = sorted(recipes, key=lambda r: r.avg_rating, reverse=True)
    
    else:
        # Unknown algorithm - fallback to basic
        if DEBUG:
            print(f"[WARN] Unknown ranking algorithm: {RANKING_ALGORITHM}, using basic")
        results = sorted(recipes, key=lambda r: r.avg_rating, reverse=True)
    
    if DEBUG:
        elapsed = time.time() - start_time
        print(f"[DEBUG] Ranking completed in {elapsed:.3f}s")
    
    return results


# Deprecated: Semantic ranking experiment (failed A/B test Q4 2024)
# def rank_recipes_semantic(recipes: List[Recipe], query: str) -> List[Recipe]:
#     """
#     Attempted semantic search using embeddings.
#     Performance was terrible (3s per request) and results weren't better.
#     Experiment abandoned but code remains.
#     """
#     # Would have used sentence-transformers or similar
#     # Never properly implemented
#     pass


# =============================================================================
# SECTION 5: RESPONSE FORMATTING (Multiple formats, only JSON used)
# =============================================================================


def format_recipe_response(recipe: Recipe) -> dict:
    """
    Convert Recipe to API response format (JSON).
    
    Issues:
    - Inconsistent field naming (snake_case vs camelCase)
    - No versioning (breaking changes shipped to all clients)
    - Timezone handling is broken for created_at
    - No validation of output format
    """
    if DEBUG:
        print(f"[DEBUG] Formatting recipe: {recipe.name}")
    
    return {
        "id": str(recipe.id),
        "name": recipe.name,
        "ingredients": recipe.ingredients,  # Should this be sorted?
        "dietary_tags": recipe.dietary_tags,  # Called "dietary_tags" here but "restrictions" elsewhere
        "cuisine": recipe.cuisine,
        "prep_time_minutes": recipe.prep_time_minutes,  # Inconsistent: snake_case
        "difficulty": recipe.difficulty,
        "rating": recipe.avg_rating,  # Field name mismatch: avg_rating -> rating
        # Missing: created_at, updated_at, calories, servings, author_id
    }


# Started XML support, never finished (50% implemented)
# def format_recipe_response_xml(recipe: Recipe) -> str:
#     """
#     XML format for legacy API clients.
#     Half-implemented, never tested, probably broken.
#     """
#     return f"""
#     <recipe>
#         <id>{recipe.id}</id>
#         <name>{recipe.name}</name>
#         <!-- TODO: Finish this, escape special characters, add CDATA -->
#     </recipe>
#     """


def paginate_results(recipes: List[Recipe], page: int = 1, page_size: int = 50) -> dict:
    """
    Paginate results for API response.
    
    Performance disaster:
    - Loads ALL results in memory first
    - Then slices to get page (doesn't use SQL LIMIT/OFFSET)
    - page_size=50 hardcoded in most places
    - No validation (page=-1, page_size=999999 both accepted)
    
    This doesn't scale past 10k recipes (we're at 8.5k currently).
    """
    if DEBUG:
        print(f"[DEBUG] Paginating results: page={page}, page_size={page_size}")
    
    # No validation of inputs!
    start = (page - 1) * page_size
    end = start + page_size
    
    # Array slicing (works but loads everything in memory)
    page_recipes = recipes[start:end]
    
    if DEBUG:
        print(f"[DEBUG] Page {page}: showing recipes {start+1}-{min(end, len(recipes))} of {len(recipes)}")
    
    # Response format
    response = {
        "results": [format_recipe_response(r) for r in page_recipes],
        "page": page,
        "page_size": page_size,
        "total": len(recipes),
        "has_more": end < len(recipes),
        # Missing: next_page_url, previous_page_url, total_pages
    }
    
    return response


# Attempted cursor-based pagination (never finished)
# def paginate_results_cursor(recipes: List[Recipe], cursor: Optional[str], page_size: int = 50) -> dict:
#     """
#     Cursor-based pagination for better performance.
#     Started in Q2 2024, abandoned after 1 week.
#     Partially implemented, breaks on edge cases.
#     """
#     # Would have used base64-encoded cursor pointing to last recipe ID
#     # Abandoned because "array slicing is good enough for now"
#     pass


# =============================================================================
# SECTION 6: CACHING LAYER (Broken, causes stale data - Issue #183)
# =============================================================================

# In-memory cache (should use Redis)
search_cache = {}
cache_timestamps = {}


def get_cache_key(request_data: dict, user_id: str) -> str:
    """
    Generate cache key from request.
    
    Issues:
    - Uses JSON serialization (slow for large requests)
    - Doesn't sort dict keys (same request can have different keys)
    - Includes user_id but recipes are same for all users (over-caching)
    - No cache size limit (memory leak)
    """
    try:
        # This can fail if request_data contains non-serializable objects
        cache_key = f"{user_id}:{json.dumps(request_data, sort_keys=True)}"
        return cache_key
    except (TypeError, ValueError) as e:
        if DEBUG:
            print(f"[WARN] Cache key generation failed: {e}")
        return f"{user_id}:uncacheable:{time.time()}"


def get_from_cache(cache_key: str) -> Optional[dict]:
    """
    Retrieve result from cache if not expired.
    
    Issues:
    - No cache invalidation strategy
    - TTL not enforced properly (check is after retrieval)
    - Memory leak (old entries never cleaned up)
    - Not thread-safe (race conditions in production)
    """
    if not ENABLE_CACHE:
        return None
    
    if cache_key in search_cache:
        # Check TTL
        cached_time = cache_timestamps.get(cache_key, 0)
        age = time.time() - cached_time
        
        if age < CACHE_TTL_SECONDS:  # 300 seconds = 5 minutes
            global cache_hits
            cache_hits += 1
            if DEBUG:
                print(f"[DEBUG] Cache HIT: {cache_key[:50]}... (age: {age:.1f}s)")
            return search_cache[cache_key]
        else:
            # Expired - should delete, but doesn't (memory leak!)
            if DEBUG:
                print(f"[DEBUG] Cache EXPIRED: {cache_key[:50]}... (age: {age:.1f}s)")
    
    global cache_misses
    cache_misses += 1
    if DEBUG:
        print(f"[DEBUG] Cache MISS: {cache_key[:50]}...")
    
    return None


def save_to_cache(cache_key: str, result: dict):
    """
    Save result to cache.
    
    Issues:
    - No size limit (can OOM)
    - No LRU eviction
    - Not thread-safe
    - Stores entire response (should store just recipe IDs)
    """
    if not ENABLE_CACHE:
        return
    
    search_cache[cache_key] = result
    cache_timestamps[cache_key] = time.time()
    
    if DEBUG:
        print(f"[DEBUG] Cached result: {cache_key[:50]}... ({len(search_cache)} total entries)")
    
    # Should check cache size and evict old entries, but doesn't!
    # This causes memory to grow unbounded until service restarts


# =============================================================================
# SECTION 7: MAIN SEARCH FUNCTION (God Object Entry Point)
# =============================================================================


def search_recipes(request_data: dict, user: User) -> dict:
    """
    Main search function - THE MONOLITHIC ENTRY POINT
    
    This function orchestrates everything:
    1. Cache lookup (broken)
    2. Request parsing (no validation)
    3. Database connection (not used)
    4. Filtering (crashes on dietary restrictions)
    5. Ranking (unclear which algorithm)
    6. Formatting (inconsistent)
    7. Pagination (doesn't scale)
    8. Cache storage (memory leak)
    9. Metrics collection (manual counters)
    10. Error handling (mix of try/except and silent failures)
    
    All concerns mixed together in one function.
    This is the definition of a "God Object" anti-pattern.
    
    🔥 THE BUG MANIFESTS HERE 🔥
    When user.dietary_restrictions is None, apply_all_filters()
    calls filter_by_dietary() which crashes on line 447.
    
    Error propagation:
    - TypeError raises here
    - Crashes entire request
    - Returns 500 to client
    - No graceful degradation
    - No error recovery
    """
    if DEBUG:
        print("=" * 80)
        print("[DEBUG] Starting search request")
        print(f"[DEBUG] Request data: {request_data}")
        print(f"[DEBUG] User: {user.name} (ID: {user.id})")
        print("=" * 80)
    
    request_start_time = time.time()
    
    # Generate cache key
    cache_key = get_cache_key(request_data, str(user.id))
    
    # Try cache (currently broken - Issue #183)
    cached_result = get_from_cache(cache_key)
    if cached_result:
        if DEBUG:
            elapsed = time.time() - request_start_time
            print(f"[DEBUG] Returned cached result in {elapsed:.3f}s")
        return cached_result
    
    # Parse request (NO VALIDATION!)
    filters = parse_search_request(request_data)
    
    # Get database connection (not actually used, but created anyway)
    db_conn = get_database_connection()
    
    # Get all recipes from "database" (actually just uses SAMPLE_RECIPES)
    all_recipes = SAMPLE_RECIPES
    if DEBUG:
        print(f"[DEBUG] Loaded {len(all_recipes)} recipes from storage")
    
    # Apply filters
    # 🔥 THIS IS WHERE THE BUG CRASHES for users with dietary_restrictions=None 🔥
    try:
        filtered_recipes = apply_all_filters(all_recipes, filters, user)
        if DEBUG:
            print(f"[DEBUG] Filtering resulted in {len(filtered_recipes)} matches")
    except TypeError as e:
        # This is what production logs show for 23% of users:
        # ERROR: TypeError: 'NoneType' object is not iterable at line 447
        if DEBUG:
            print(f"[ERROR] Filter crashed: {e}")
            print(f"[ERROR] User dietary_restrictions: {user.dietary_restrictions}")
        
        global error_count
        error_count += 1
        
        # No graceful degradation - just re-raise and crash the request
        raise e
    
    # Rank results (which algorithm? unclear!)
    ranked_recipes = rank_recipes(filtered_recipes, filters["query"])
    if DEBUG:
        print(f"[DEBUG] Ranked {len(ranked_recipes)} recipes")
        if ranked_recipes[:3]:
            print(f"[DEBUG] Top 3 results: {[r.name for r in ranked_recipes[:3]]}")
    
    # Paginate and format (hardcoded page size, loads all in memory)
    response = paginate_results(ranked_recipes, page=1, page_size=50)
    
    # Save to cache (memory leak here)
    save_to_cache(cache_key, response)
    
    # Close database connection (actually never opened a real one)
    close_database_connection(db_conn)
    
    # Log metrics (manual counters, no proper monitoring)
    elapsed = time.time() - request_start_time
    if DEBUG:
        print("=" * 80)
        print(f"[DEBUG] Search completed in {elapsed:.3f}s")
        print(f"[DEBUG] Total searches: {search_count}")
        print(f"[DEBUG] Cache hit rate: {cache_hits}/{cache_hits + cache_misses}")
        print(f"[DEBUG] Total errors: {error_count}")
        print("=" * 80)
    
    return response


# Deprecated: Old search function v1 (archaeological artifact)
# def search_recipes_v1(query: str, page: int = 1) -> List[dict]:
#     """
#     The original search function from 18 months ago.
#     Simple times: just query string, no filters, no pagination.
#     Worked fine when we had 50 recipes.
#     """
#     recipes = SAMPLE_RECIPES
#     if query:
#         recipes = [r for r in recipes if query.lower() in r.name.lower()]
#     
#     return [format_recipe_response(r) for r in recipes]


# =============================================================================
# HELPER UTILITIES (Miscellaneous functions that don't fit elsewhere)
# =============================================================================


def clear_cache():
    """
    Manually clear cache (called by admin endpoint).
    Thread-unsafe, can cause race conditions.
    """
    global search_cache, cache_timestamps
    search_cache = {}
    cache_timestamps = {}
    
    if DEBUG:
        print("[DEBUG] Cache cleared")


def get_search_metrics() -> dict:
    """
    Return current metrics (for monitoring dashboard).
    These are global counters that reset on service restart.
    No persistence, no aggregation, no historical data.
    """
    return {
        "total_searches": search_count,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_hit_rate": cache_hits / max(cache_hits + cache_misses, 1),
        "total_errors": error_count,
        "cache_size": len(search_cache)
    }


# =============================================================================
# END OF FILE
# =============================================================================
# 
# Summary of technical debt:
# - 1103 lines in single file (God Object anti-pattern)
# - 74+ magic numbers  (no constants)
# - 12 feature flags (unclear which are active)
# - 5 active functions + 3 deprecated versions (dead code)
# - 3 ranking algorithms (unclear which is production)
# - 0% test coverage (too coupled to test)
# - Manual metrics (no proper monitoring)
# - Broken caching (memory leak - Issue #183)
# - No input validation (accepts garbage)
# - THE BUG: Line 447 crashes for 23% of users (Issue #247)
# 
# Architect's recommendation (@search-architect):
# Break into 4 modules:
#   1. validation_module.py  - Pydantic models, input validation
#   2. filtering_module.py   - All filter logic, optimizations
#   3. aggregation_module.py - Ranking algorithms, scoring
#   4. formatting_module.py  - Response formatting, pagination
# 
# Estimated effort: 3-4 days (traditional approach)
# With Spec Kit + Agents: 2 hours, governed by constitution, specs
# =============================================================================
