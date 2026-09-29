# FitBuddy AI Fitness Plan Generator

A complete FastAPI + SQLite + Jinja/vanilla-JS application that generates structured 7-day fitness plans and nutrition/recovery tips with Google Gemini.

## Features

- Responsive browser UI
- FastAPI backend
- SQLite persistence through SQLAlchemy
- User/profile upsert
- Structured Gemini JSON output validated with Pydantic
- Plan regeneration from user feedback
- Nutrition/recovery tip endpoint
- Health-oriented guardrails and input validation
- Works without a Gemini key in demo mode using a deterministic local plan
- Automated API/model tests

## Safety behavior

This demo generates individualized fitness plans only for adults (18+). The backend rejects plan generation for users under 18. The app is not medical advice and should not be used to diagnose or treat injuries or medical conditions.

## Project structure

```text
FitBuddy/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   └── services/
│       ├── __init__.py
│       └── ai_service.py
├── templates/
│   └── index.html
├── static/
│   ├── css/styles.css
│   └── js/app.js
├── tests/
│   ├── __init__.py
│   └── test_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## VS Code setup

### 1. Open the folder

Open `FitBuddy` in VS Code.

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows CMD:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Gemini

Copy `.env.example` to `.env`.

Windows:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Set:

```env
GOOGLE_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-2.5-flash
```

If `GOOGLE_API_KEY` is blank, the app still runs in local demo mode.

### 5. Run

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

API docs: `http://127.0.0.1:8000/docs`

## Testing

```bash
pytest -q
```

Tests use a temporary SQLite database and do not require a Gemini API key.

## API endpoints

- `GET /health`
- `GET /api/users/{user_id}`
- `POST /api/users`
- `POST /api/plans/generate`
- `GET /api/users/{user_id}/plans/latest`
- `POST /api/plans/{plan_id}/revise`
- `GET /api/nutrition-tip?goal=...`

## Gemini integration

The project uses Google's `google-genai` Python SDK and asks Gemini for JSON conforming to a Pydantic schema. The backend validates the returned structure before returning it to the browser.

If the Gemini call fails, the API returns a controlled error and does not expose the API key.

## Production notes

For production, add authentication, CSRF protection if cookie sessions are introduced, rate limiting, HTTPS, secret management, PostgreSQL, migrations, audit logging, and stronger privacy controls.
