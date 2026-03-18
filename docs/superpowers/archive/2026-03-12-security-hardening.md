# Security Hardening Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove live API keys from version control, fix CORS wildcard, and add backend input validation.

**Architecture:** The backend uses `pydantic-settings` to read `.env` — the env file is already wired correctly, it just needs to be untracked from git. CORS is a one-liner change in `main.py`. Input validation is added via Pydantic `Field` constraints on existing request models.

**Tech Stack:** Python 3.x, FastAPI, Pydantic v2, git

---

## Chunk 1: Untrack .env and rotate keys

### Task 1: Remove backend/.env from git tracking

**Files:**
- Modify: `.gitignore`
- Delete from git index: `backend/.env`

- [ ] **Step 1: Check what's currently tracked**

```bash
git -C /Users/pratyush/F1-Insight-Hub ls-files backend/.env
```
Expected output: `backend/.env` (confirms it is tracked)

- [ ] **Step 2: Ensure .gitignore has the right entries**

Open `.gitignore` and confirm these lines exist (add if missing):
```
.env
backend/.env
*.env
```

- [ ] **Step 3: Remove the file from git's index without deleting it from disk**

```bash
git rm --cached backend/.env
```
Expected: `rm 'backend/.env'`

- [ ] **Step 4: Verify the file still exists on disk but is no longer tracked**

```bash
ls backend/.env && git status backend/.env
```
Expected: file exists, git status shows nothing (not staged, not tracked)

- [ ] **Step 5: Commit the untracking**

```bash
git add .gitignore
git commit -m "security: untrack backend/.env and ensure gitignore covers all .env files"
```

---

### Task 2: Rotate the exposed API keys

> This must happen **after** Task 1 so the new keys never appear in tracked files.

- [ ] **Step 1: Rotate OpenWeatherMap key**
  - Go to https://home.openweathermap.org/api_keys
  - Delete the key `2b36c333fce580db70db43cf9726157d`
  - Generate a new key
  - Update `backend/.env`: `OPENWEATHER_API_KEY=<new_key>`

- [ ] **Step 2: Rotate Gemini key**
  - Go to https://aistudio.google.com/app/apikey
  - Delete `AIzaSyBv5zPsetAFjf_f_iGTs9EEtjhSSiwKAho`
  - Generate a new key
  - Update `backend/.env`: `GEMINI_API_KEY=<new_key>`

- [ ] **Step 3: Verify backend still starts with new keys**

```bash
cd /Users/pratyush/F1-Insight-Hub/backend
uvicorn app.main:app --port 8000
```
Expected: `F1 backend ready` in logs, no `KeyError` or auth failures

- [ ] **Step 4: Scrub keys from .env.example**

Open `backend/.env.example`. Replace any real key values with placeholders:
```
GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_API_KEY=your_openweathermap_api_key_here
```

- [ ] **Step 5: Commit**

```bash
git add backend/.env.example
git commit -m "security: replace real keys in .env.example with placeholders"
```

---

## Chunk 2: CORS and input validation

### Task 3: Restrict CORS to known origins

**Files:**
- Modify: `backend/app/main.py:47-53`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add allowed_origins to Settings**

Open `backend/app/config.py`. Add one field to `Settings`:

```python
class Settings(BaseSettings):
    openweather_api_key: str = ""
    google_api_key: str = ""
    jolpica_base: str = "https://api.jolpi.ca/ergast/f1"
    cache_db_path: str = ""
    fastf1_cache_dir: str = ""
    log_level: str = "INFO"
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}
```

- [ ] **Step 2: Wire allowed_origins into CORS middleware**

Open `backend/app/main.py`. Replace lines 47-53:

```python
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )
```

- [ ] **Step 3: Verify CORS works for localhost dev**

```bash
cd /Users/pratyush/F1-Insight-Hub/backend
uvicorn app.main:app --port 8000
```

Then in another terminal:
```bash
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS http://localhost:8000/health -v 2>&1 | grep "Access-Control"
```
Expected: `Access-Control-Allow-Origin: http://localhost:5173`

- [ ] **Step 4: Test that a disallowed origin is rejected**

```bash
curl -H "Origin: http://evil.com" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS http://localhost:8000/health -v 2>&1 | grep "Access-Control"
```
Expected: No `Access-Control-Allow-Origin` header (blocked)

- [ ] **Step 5: Add your production domain to .env.example**

```bash
# In backend/.env.example add:
ALLOWED_ORIGINS=["http://localhost:5173","https://your-production-domain.com"]
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/main.py backend/app/config.py backend/.env.example
git commit -m "security: restrict CORS to known origins via config"
```

---

### Task 4: Add input validation to predict endpoints

**Files:**
- Modify: `backend/app/routers/predict.py`

- [ ] **Step 1: Read the current predict router**

```bash
cat backend/app/routers/predict.py
```

Note the current request body models and which fields accept year/round/race values.

- [ ] **Step 2: Add Field constraints to request models**

For any Pydantic model that accepts `year`, add:
```python
from pydantic import BaseModel, Field

class SomePredictRequest(BaseModel):
    year: int = Field(default=2024, ge=1950, le=2100)
    race: str = Field(min_length=1, max_length=100)
    # ... other fields
```

For string fields that map to known enums (session type, compound), add `pattern` or `Literal`:
```python
from typing import Literal
session: Literal["FP1", "FP2", "FP3", "Q", "SQ", "S", "R"] = "Q"
```

- [ ] **Step 3: Verify FastAPI auto-validates**

Start the server and send a bad request:
```bash
curl -X POST http://localhost:8000/api/predict/driver \
  -H "Content-Type: application/json" \
  -d '{"year": 1800, "driver": "VER"}'
```
Expected: `422 Unprocessable Entity` with validation error details

- [ ] **Step 4: Test valid request still works**

```bash
curl -X POST http://localhost:8000/api/predict/driver \
  -H "Content-Type: application/json" \
  -d '{"year": 2024, "driver": "VER", "track": "Monaco", "weather": "dry", "team": "Red Bull"}'
```
Expected: `200 OK` with prediction data

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/predict.py
git commit -m "security: add Pydantic field validation to predict endpoints"
```
