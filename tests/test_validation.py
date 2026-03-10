"""
Tests for search/validation.py

Covers the root-cause fix for Issue #1: null dietary_restrictions.
"""
import pytest
from pydantic import ValidationError

from search.validation import SearchRequest


class TestDietaryRestrictionsCoercion:
    """null / missing dietary_restrictions must never reach filter layer."""

    def test_none_coerced_to_empty_list(self):
        req = SearchRequest.model_validate({"query": "pasta", "dietary_restrictions": None})
        assert req.dietary_restrictions == []

    def test_missing_field_defaults_to_empty_list(self):
        req = SearchRequest.model_validate({"query": "pasta"})
        assert req.dietary_restrictions == []

    def test_valid_list_preserved(self):
        req = SearchRequest.model_validate({"dietary_restrictions": ["vegan", "gluten-free"]})
        assert req.dietary_restrictions == ["vegan", "gluten-free"]

    def test_empty_list_preserved(self):
        req = SearchRequest.model_validate({"dietary_restrictions": []})
        assert req.dietary_restrictions == []


class TestFieldDefaults:
    def test_query_defaults_to_empty_string(self):
        req = SearchRequest.model_validate({})
        assert req.query == ""

    def test_min_rating_defaults_to_zero(self):
        req = SearchRequest.model_validate({})
        assert req.min_rating == 0.0

    def test_cuisine_defaults_to_none(self):
        req = SearchRequest.model_validate({})
        assert req.cuisine is None

    def test_max_prep_time_defaults_to_none(self):
        req = SearchRequest.model_validate({})
        assert req.max_prep_time is None


class TestFieldValidation:
    def test_query_max_length(self):
        with pytest.raises(ValidationError):
            SearchRequest.model_validate({"query": "x" * 201})

    def test_min_rating_below_zero(self):
        with pytest.raises(ValidationError):
            SearchRequest.model_validate({"min_rating": -0.1})

    def test_min_rating_above_five(self):
        with pytest.raises(ValidationError):
            SearchRequest.model_validate({"min_rating": 5.1})

    def test_max_prep_time_below_one(self):
        with pytest.raises(ValidationError):
            SearchRequest.model_validate({"max_prep_time": 0})

    def test_max_prep_time_above_480(self):
        with pytest.raises(ValidationError):
            SearchRequest.model_validate({"max_prep_time": 481})

    def test_max_prep_time_valid(self):
        req = SearchRequest.model_validate({"max_prep_time": 30})
        assert req.max_prep_time == 30
