"""
Search configuration constants.

Replaces the 16+ hardcoded magic numbers / feature-flag globals
previously scattered across search.py.
"""
import os

# ---------------------------------------------------------------------------
# Ranking weights
# ---------------------------------------------------------------------------
RELEVANCE_WEIGHT: float = 0.45
RATING_WEIGHT: float = 0.30
POPULARITY_WEIGHT: float = 0.25

# Relevance score bonuses
EXACT_NAME_SCORE: float = 10.0
PARTIAL_NAME_SCORE: float = 5.0
INGREDIENT_MATCH_SCORE: float = 2.0

# ---------------------------------------------------------------------------
# Ranking algorithm
# ---------------------------------------------------------------------------
# Valid choices: "basic" | "weighted_v2" | "hybrid_v3"
RANKING_ALGORITHM: str = os.getenv("RANKING_ALGORITHM", "hybrid_v3")
USE_POPULARITY_BOOST: bool = os.getenv("USE_POPULARITY_BOOST", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 200

# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------
ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))

# ---------------------------------------------------------------------------
# Feature flags
# ---------------------------------------------------------------------------
ENABLE_FUZZY_SEARCH: bool = os.getenv("ENABLE_FUZZY_SEARCH", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Debug / logging
# ---------------------------------------------------------------------------
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
