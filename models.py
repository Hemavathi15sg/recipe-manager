"""
FlavorHub Recipe Model Definitions

WARNING: This has intentional issues for workshop learning.
Issue #247: User.dietary_restrictions can be None (not handled properly)
"""
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime


class User:
    """User model - has the dietary restrictions bug"""
    
    def __init__(self, id: UUID, name: str, email: str, dietary_restrictions=None):
        self.id = id
        self.name = name
        self.email = email
        self.dietary_restrictions = dietary_restrictions  # ← BUG: Can be None!
        self.created_at = datetime.now()


class Recipe:
    """Recipe model"""
    
    def __init__(
        self,
        id: UUID,
        name: str,
        ingredients: List[str],
        dietary_tags: List[str],
        cuisine: str,
        prep_time_minutes: int,
        difficulty: str,
        avg_rating: float = 0.0
    ):
        self.id = id
        self.name = name
        self.ingredients = ingredients
        self.dietary_tags = dietary_tags
        self.cuisine = cuisine
        self.prep_time_minutes = prep_time_minutes
        self.difficulty = difficulty
        self.avg_rating = avg_rating
        self.created_at = datetime.now()


# Sample data for demonstration
SAMPLE_RECIPES = [
    Recipe(
        id=uuid4(),
        name="Spaghetti Carbonara",
        ingredients=["pasta", "eggs", "bacon", "parmesan", "black pepper"],
        dietary_tags=[],
        cuisine="Italian",
        prep_time_minutes=25,
        difficulty="intermediate",
        avg_rating=4.5
    ),
    Recipe(
        id=uuid4(),
        name="Vegan Buddha Bowl",
        ingredients=["quinoa", "chickpeas", "avocado", "kale", "tahini"],
        dietary_tags=["vegan", "gluten-free"],
        cuisine="American",
        prep_time_minutes=30,
        difficulty="beginner",
        avg_rating=4.7
    ),
    Recipe(
        id=uuid4(),
        name="Pad Thai",
        ingredients=["rice noodles", "tofu", "peanuts", "bean sprouts", "lime"],
        dietary_tags=["vegetarian"],
        cuisine="Thai",
        prep_time_minutes=20,
        difficulty="intermediate",
        avg_rating=4.6
    )
]


# Sample users
SAMPLE_USERS = [
    User(uuid4(), "Alice", "alice@example.com", dietary_restrictions=["vegan"]),
    User(uuid4(), "Bob", "bob@example.com", dietary_restrictions=None),  # ← This causes the bug!
    User(uuid4(), "Charlie", "charlie@example.com", dietary_restrictions=["gluten-free", "dairy-free"]),
]
