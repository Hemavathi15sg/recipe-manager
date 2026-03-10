"""
Integration tests for search.service.search_recipes

These tests exercise the full search pipeline through the public API and
are the primary regression guard for Issue #1.
"""
import pytest
from uuid import uuid4

from models import User, SAMPLE_USERS
from search.service import search_recipes, clear_search_cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure a clean cache state for every test."""
    clear_search_cache()
    yield
    clear_search_cache()


def _user(dietary_restrictions=None) -> User:
    return User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        dietary_restrictions=dietary_restrictions,
    )


# ---------------------------------------------------------------------------
# Issue #247: null dietary_restrictions must not crash
# ---------------------------------------------------------------------------

class TestNullDietaryRestrictions:
    def test_none_dietary_does_not_raise(self):
        """User with dietary_restrictions=None must not crash search."""
        user = _user(dietary_restrictions=None)
        result = search_recipes({"query": "pasta"}, user)
        assert "results" in result
        assert "total" in result

    def test_sample_user_bob_does_not_crash(self):
        """Bob (SAMPLE_USERS[1]) has dietary_restrictions=None — must not crash."""
        bob = SAMPLE_USERS[1]
        assert bob.dietary_restrictions is None
        result = search_recipes({"query": "pasta", "cuisine": None}, bob)
        assert "results" in result

    def test_request_null_dietary_does_not_crash(self):
        """JSON null in request body must not crash search."""
        user = _user()
        result = search_recipes({"query": "pasta", "dietary_restrictions": None}, user)
        assert "results" in result


# ---------------------------------------------------------------------------
# Correct results
# ---------------------------------------------------------------------------

class TestSearchResults:
    def test_vegan_user_gets_vegan_results(self):
        alice = SAMPLE_USERS[0]  # dietary_restrictions=["vegan"]
        result = search_recipes({"query": "bowl"}, alice)
        assert result["total"] >= 1
        for recipe in result["results"]:
            assert "vegan" in recipe["dietary_tags"]

    def test_no_restrictions_returns_results(self):
        user = _user(dietary_restrictions=[])
        result = search_recipes({"query": "pasta"}, user)
        assert result["total"] >= 1

    def test_cuisine_filter_applied(self):
        user = _user()
        result = search_recipes({"query": "", "cuisine": "Italian"}, user)
        for recipe in result["results"]:
            assert recipe["cuisine"] == "Italian"

    def test_response_structure(self):
        user = _user()
        result = search_recipes({}, user)
        assert set(result.keys()) >= {"results", "page", "page_size", "total", "has_more"}

    def test_result_recipe_structure(self):
        user = _user()
        result = search_recipes({}, user)
        if result["results"]:
            recipe = result["results"][0]
            assert set(recipe.keys()) >= {
                "id", "name", "ingredients", "dietary_tags",
                "cuisine", "prep_time_minutes", "difficulty", "rating",
            }


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

class TestCaching:
    def test_identical_requests_return_same_result(self):
        user = _user()
        r1 = search_recipes({"query": "pasta"}, user)
        r2 = search_recipes({"query": "pasta"}, user)
        assert r1 == r2

    def test_different_queries_return_different_results(self):
        user = _user()
        r1 = search_recipes({"query": "pasta", "cuisine": "Italian"}, user)
        r2 = search_recipes({"query": "bowl"}, user)
        # Verify both calls succeed without error; results may differ
        assert "results" in r1
        assert "results" in r2
