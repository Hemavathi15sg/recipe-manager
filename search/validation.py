"""
Search request validation using Pydantic v2.

Proper fix for Issue #1: null dietary_restrictions.
By enforcing types at the API boundary, None can never reach
the filter layer from any code path.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    """Validated search request model.

    dietary_restrictions defaults to an empty list so that
    ``None`` (JSON null) and a missing key both produce ``[]``
    — the filter layer never sees ``None``.
    """

    query: str = Field(default="", max_length=200)
    dietary_restrictions: list[str] = Field(default_factory=list)
    cuisine: Optional[str] = Field(default=None, max_length=100)
    max_prep_time: Optional[int] = Field(default=None, ge=1, le=480)
    difficulty: Optional[str] = None
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0)

    @field_validator("dietary_restrictions", mode="before")
    @classmethod
    def coerce_none_to_empty_list(cls, v: object) -> list:
        """Coerce JSON ``null`` / Python ``None`` to an empty list."""
        return v if v is not None else []
