# FlavorHub Recipe Manager - Brownfield Application

> **Warning:** This codebase has **intentional issues** for the workshop. Do NOT use in production!

## About This Codebase

This is FlavorHub's legacy Recipe Manager - a 2-year-old application with technical debt. It has:

- ✅ Working recipe search (mostly)
- ❌ Production bug: Crashes for users without dietary restrictions
- ❌ 847-line monolith in `search.py`
- ❌ No input validation
- ❌ Zero test coverage
- ❌ Performance issues (280ms average searches)
- ❌ No documentation

**Your mission:** Fix the crisis and modernize this system using GitHub agents.

---

## The Bug (Issue #247)

**Error:**
```
TypeError: 'NoneType' object is not iterable
  File "search.py", line 145, in filter_by_dietary
```

**Impact:** 30% of searches failing (users without dietary preferences)

---

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (or SQLite for workshop)

### Install Dependencies
```bash
cd recipe-manager
pip install -r requirements.txt
```

### Initialize Database
```bash
python init_db.py
```

### Run Application
```bash
python main.py
```

API runs on: `http://localhost:8000`

---

## Project Structure

```
recipe-manager/
├── main.py              # FastAPI application entry
├── search.py            # 847-line monolith (THE PROBLEM)
├── models.py            # User and Recipe models
├── database.py          # Database connection
├── api/
│   └── routes.py        # API endpoints
├── requirements.txt     # Dependencies
└── init_db.py          # Database setup script
```

---

## Known Issues

1. **🔴 CRITICAL:** Null pointer exception in dietary restrictions filter
2. **🟠 HIGH:** Search performance degrading (280ms average)
3. **🟠 HIGH:** No test coverage
4. **🟡 MEDIUM:** 847-line god object in search.py
5. **🟡 MEDIUM:** No input validation
6. **🟢 LOW:** Missing API documentation

**Fix these using the workshop exercises!**

---

## API Endpoints

### Search Recipes
```bash
POST /api/search
Content-Type: application/json

{
  "query": "pasta",
  "dietary_restrictions": ["vegan"],  # This can be null (BUG!)
  "cuisine": "Italian",
  "max_prep_time": 30
}
```

---

## Workshop Usage

This codebase is designed for the **"Agent-Driven Spec Development"** workshop. 

**Timeline:** 3:00 PM (bug discovered) → 5:00 PM (crisis resolved)

Follow workshop experiments to:
1. Create Issue #247 with agent skills
2. Analyze root cause with custom agents
3. Design solution with Spec Kit
4. Implement refactoring with Copilot CLI
5. Validate with /speckit.analyze

---

## DO NOT

- ❌ Use in production
- ❌ Fix bugs manually (let agents guide you through workshop)
- ❌ Refactor before completing Experiment 3 (need spec first!)

---

## License

Educational use only. Part of GitHub Copilot workshop materials.
