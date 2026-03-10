"""
search package — public API.

Callers import ``search_recipes`` and ``clear_search_cache`` from here;
the internal module layout is an implementation detail.
"""
from search.service import clear_search_cache, search_recipes

__all__ = ["search_recipes", "clear_search_cache"]
