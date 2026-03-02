"""
Test script to reproduce Issue #247

This demonstrates the production bug that crashes search
for users without dietary restrictions.
"""
from models import User, SAMPLE_USERS
from search import search_recipes
from uuid import uuid4


def test_bug_with_null_dietary():
    """
    Reproduce Issue #247: TypeError when dietary_restrictions is None
    
    Expected: TypeError: 'NoneType' object is not iterable
    Location: search.py, line 145
    """
    print("🧪 Testing search with user who has dietary_restrictions=None...")
    print()
    
    # Create user with None dietary restrictions (like Bob in SAMPLE_USERS)
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        dietary_restrictions=None  # ← This causes the crash!
    )
    
    # Simple search request
    request = {
        "query": "pasta",
        "cuisine": "Italian"
    }
    
    print(f"User: {user.name}")
    print(f"Dietary restrictions: {user.dietary_restrictions}")
    print(f"Search query: {request['query']}")
    print()
    
    try:
        results = search_recipes(request, user)
        print("✅ Search succeeded!")
        print(f"Found {results['total']} recipes")
    except TypeError as e:
        print("❌ CRASH! (This is Issue #247)")
        print(f"Error: {e}")
        print()
        print("Stack trace points to search.py line 145:")
        print("  for restriction in user.dietary_restrictions:")
        print("  TypeError: 'NoneType' object is not iterable")
        print()
        print("💡 This is the bug you'll fix in the workshop!")
        return False
    
    return True


def test_bug_with_sample_user():
    """Test with Bob from SAMPLE_USERS (also has None)"""
    print("\n" + "="*60)
    print("🧪 Testing with Bob (SAMPLE_USERS[1])...")
    print()
    
    user = SAMPLE_USERS[1]  # Bob has dietary_restrictions=None
    
    request = {
        "query": "pasta",
        "cuisine": None
    }
    
    print(f"User: {user.name}")
    print(f"Dietary restrictions: {user.dietary_restrictions}")
    print()
    
    try:
        results = search_recipes(request, user)
        print("✅ Search succeeded!")
        print(f"Found {results['total']} recipes")
        return True
    except TypeError as e:
        print("❌ CRASH! Same issue as production")
        print(f"Error: {e}")
        return False


def test_working_case():
    """Test with user who HAS dietary restrictions (works fine)"""
    print("\n" + "="*60)
    print("🧪 Testing with Alice (has dietary restrictions)...")
    print()
    
    user = SAMPLE_USERS[0]  # Alice has dietary_restrictions=["vegan"]
    
    request = {
        "query": "bowl",
        "cuisine": None
    }
    
    print(f"User: {user.name}")
    print(f"Dietary restrictions: {user.dietary_restrictions}")
    print()
    
    try:
        results = search_recipes(request, user)
        print("✅ Search succeeded!")
        print(f"Found {results['total']} recipes")
        for r in results['results']:
            print(f"  - {r['name']} ({r['dietary_tags']})")
        return True
    except TypeError as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("FlavorHub Issue #247 Reproduction Test")
    print("="*60)
    print()
    print("This script demonstrates the production bug that affects")
    print("30% of searches (users without dietary restrictions).")
    print()
    
    # Run tests
    test_working_case()  # This works
    test_bug_with_null_dietary()  # This crashes
    test_bug_with_sample_user()  # This also crashes
    
    print("\n" + "="*60)
    print("Summary:")
    print("  ✅ Users WITH dietary preferences: Search works")
    print("  ❌ Users WITHOUT dietary preferences: Search crashes")
    print()
    print("Follow the workshop to fix this using GitHub agents!")
    print("="*60)
