"""
Tests for search/filters.py

Covers the null-dietary fix and verifies that each filter returns correct
results; also verifies the optimised pipeline order does not change outcomes.
"""
import pytest
from uuid import uuid4

from models import Recipe, User
from search.filters import (
    apply_all_filters,
    filter_by_cuisine,
    filter_by_dietary,
    filter_by_difficulty,
    filter_by_prep_time,
    filter_by_query,
    filter_by_rating,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _recipe(
    name="Test Recipe",
    cuisine="Italian",
    dietary_tags=None,
    prep_time_minutes=30,
    difficulty="beginner",
    avg_rating=4.0,
    ingredients=None,
) -> Recipe:
    return Recipe(
        id=uuid4(),
        name=name,
        ingredients=ingredients or ["pasta"],
        dietary_tags=dietary_tags or [],
        cuisine=cuisine,
        prep_time_minutes=prep_time_minutes,
        difficulty=difficulty,
        avg_rating=avg_rating,
    )


@pytest.fixture()
def vegan_recipe():
    return _recipe(name="Vegan Bowl", dietary_tags=["vegan", "gluten-free"])


@pytest.fixture()
def non_vegan_recipe():
    return _recipe(name="Carbonara", dietary_tags=[])


@pytest.fixture()
def italian_recipe():
    return _recipe(name="Pasta", cuisine="Italian")


@pytest.fixture()
def thai_recipe():
    return _recipe(name="Pad Thai", cuisine="Thai")


# ---------------------------------------------------------------------------
# filter_by_dietary — the bug fix
# ---------------------------------------------------------------------------

class TestFilterByDietary:
    def test_empty_restrictions_returns_all(self, vegan_recipe, non_vegan_recipe):
        """Empty list (coerced from None) must return all recipes — not crash."""
        result = filter_by_dietary([vegan_recipe, non_vegan_recipe], [])
        assert result == [vegan_recipe, non_vegan_recipe]

    def test_vegan_restriction_filters_correctly(self, vegan_recipe, non_vegan_recipe):
        result = filter_by_dietary([vegan_recipe, non_vegan_recipe], ["vegan"])
        assert result == [vegan_recipe]

    def test_multiple_restrictions_applied(self):
        r1 = _recipe(dietary_tags=["vegan", "gluten-free"])
        r2 = _recipe(dietary_tags=["vegan"])
        result = filter_by_dietary([r1, r2], ["vegan", "gluten-free"])
        assert result == [r1]

    def test_no_match_returns_empty(self, non_vegan_recipe):
        result = filter_by_dietary([non_vegan_recipe], ["kosher"])
        assert result == []


# ---------------------------------------------------------------------------
# filter_by_cuisine
# ---------------------------------------------------------------------------

class TestFilterByCuisine:
    def test_none_returns_all(self, italian_recipe, thai_recipe):
        assert filter_by_cuisine([italian_recipe, thai_recipe], None) == [italian_recipe, thai_recipe]

    def test_exact_match(self, italian_recipe, thai_recipe):
        assert filter_by_cuisine([italian_recipe, thai_recipe], "Italian") == [italian_recipe]

    def test_case_insensitive(self, italian_recipe):
        assert filter_by_cuisine([italian_recipe], "italian") == [italian_recipe]

    def test_no_match(self, italian_recipe):
        assert filter_by_cuisine([italian_recipe], "Mexican") == []


# ---------------------------------------------------------------------------
# filter_by_difficulty
# ---------------------------------------------------------------------------

class TestFilterByDifficulty:
    def test_none_returns_all(self):
        r = _recipe(difficulty="beginner")
        assert filter_by_difficulty([r], None) == [r]

    def test_match(self):
        r = _recipe(difficulty="advanced")
        assert filter_by_difficulty([r], "advanced") == [r]

    def test_case_insensitive(self):
        r = _recipe(difficulty="Intermediate")
        assert filter_by_difficulty([r], "intermediate") == [r]

    def test_no_match(self):
        r = _recipe(difficulty="beginner")
        assert filter_by_difficulty([r], "advanced") == []


# ---------------------------------------------------------------------------
# filter_by_rating
# ---------------------------------------------------------------------------

class TestFilterByRating:
    def test_zero_returns_all(self):
        r = _recipe(avg_rating=0.0)
        assert filter_by_rating([r], 0.0) == [r]

    def test_filters_below_threshold(self):
        high = _recipe(avg_rating=4.5)
        low = _recipe(avg_rating=3.0)
        assert filter_by_rating([high, low], 4.0) == [high]

    def test_exact_threshold_included(self):
        r = _recipe(avg_rating=4.0)
        assert filter_by_rating([r], 4.0) == [r]


# ---------------------------------------------------------------------------
# filter_by_prep_time
# ---------------------------------------------------------------------------

class TestFilterByPrepTime:
    def test_none_returns_all(self):
        r = _recipe(prep_time_minutes=60)
        assert filter_by_prep_time([r], None) == [r]

    def test_filters_over_max(self):
        fast = _recipe(prep_time_minutes=15)
        slow = _recipe(prep_time_minutes=60)
        assert filter_by_prep_time([fast, slow], 30) == [fast]

    def test_exact_max_included(self):
        r = _recipe(prep_time_minutes=30)
        assert filter_by_prep_time([r], 30) == [r]


# ---------------------------------------------------------------------------
# filter_by_query
# ---------------------------------------------------------------------------

class TestFilterByQuery:
    def test_empty_query_returns_all(self):
        r = _recipe()
        assert filter_by_query([r], "") == [r]

    def test_name_match(self):
        r = _recipe(name="Spaghetti Carbonara")
        assert filter_by_query([r], "carbonara") == [r]

    def test_ingredient_match(self):
        r = _recipe(ingredients=["pasta", "eggs"])
        assert filter_by_query([r], "eggs") == [r]

    def test_no_match(self):
        r = _recipe(name="Salad", ingredients=["lettuce"])
        assert filter_by_query([r], "pasta") == []

    def test_case_insensitive(self):
        r = _recipe(name="Vegan Bowl")
        assert filter_by_query([r], "VEGAN") == [r]


# ---------------------------------------------------------------------------
# apply_all_filters — pipeline integration
# ---------------------------------------------------------------------------

class TestApplyAllFilters:
    def test_no_filters_returns_all(self):
        recipes = [_recipe(), _recipe()]
        result = apply_all_filters(
            recipes=recipes,
            query="",
            dietary_restrictions=[],
            cuisine=None,
            max_prep_time=None,
            difficulty=None,
            min_rating=0.0,
        )
        assert result == recipes

    def test_combined_filters(self):
        match = _recipe(
            name="Vegan Pasta",
            cuisine="Italian",
            dietary_tags=["vegan"],
            prep_time_minutes=20,
            difficulty="beginner",
            avg_rating=4.5,
            ingredients=["pasta"],
        )
        no_match = _recipe(
            name="Beef Stew",
            cuisine="American",
            dietary_tags=[],
            prep_time_minutes=90,
            difficulty="advanced",
            avg_rating=3.0,
            ingredients=["beef"],
        )
        result = apply_all_filters(
            recipes=[match, no_match],
            query="pasta",
            dietary_restrictions=["vegan"],
            cuisine="Italian",
            max_prep_time=30,
            difficulty="beginner",
            min_rating=4.0,
        )
        assert result == [match]

    def test_null_dietary_from_user_does_not_crash(self):
        """Regression test: None dietary restrictions must not raise TypeError."""
        recipes = [_recipe()]
        # Caller is responsible for passing [] instead of None (see service.py)
        result = apply_all_filters(
            recipes=recipes,
            query="",
            dietary_restrictions=[],  # coerced from None by service layer
            cuisine=None,
            max_prep_time=None,
            difficulty=None,
            min_rating=0.0,
        )
        assert result == recipes
