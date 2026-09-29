from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .config import get_settings
from .database import Base, engine, get_db
from .services import ai_service

settings = get_settings()
Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )

@app.get("/health", response_model=schemas.HealthResponse)
def health():
    return schemas.HealthResponse(
        status="ok",
        gemini_configured=bool(settings.google_api_key.strip()),
        model=settings.gemini_model,
    )

@app.post("/api/users", response_model=schemas.UserRead)
def upsert_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.upsert_user(db, data)

@app.get("/api/users/{user_id}", response_model=schemas.UserRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/plans/generate", response_model=schemas.PlanResponse)
def generate_plan(data: schemas.UserCreate, db: Session = Depends(get_db)):
    if data.age < settings.min_plan_age:
        raise HTTPException(
            status_code=403,
            detail=f"Personalized plan generation is available only for adults aged {settings.min_plan_age}+."
        )

    user = crud.upsert_user(db, data)

    try:
        plan, source = ai_service.generate_plan(
            user.name,
            user.age,
            user.gender,
            user.weight_kg,
            user.goal,
            user.intensity,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI plan generation failed: {exc}") from exc

    record = crud.create_plan(db, user.id, plan, source)

    return schemas.PlanResponse(
        plan_id=record.id,
        user_id=user.id,
        source=source,
        plan=plan,
    )

@app.get("/api/users/{user_id}/plans/latest", response_model=schemas.PlanResponse)
def latest_plan(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    record = crud.get_latest_plan(db, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="No plan found")

    return schemas.PlanResponse(
        plan_id=record.id,
        user_id=user_id,
        source=record.source,
        plan=crud.decode_plan(record),
    )

@app.post("/api/plans/{plan_id}/revise", response_model=schemas.PlanResponse)
def revise_plan(plan_id: int, data: schemas.PlanRevisionRequest, db: Session = Depends(get_db)):
    record = crud.get_plan(db, plan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Plan not found")

    user = crud.get_user(db, record.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    crud.save_feedback(db, plan_id, data.feedback)

    try:
        current = crud.decode_plan(record)
        revised, source = ai_service.revise_plan(current, data.feedback)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI plan revision failed: {exc}") from exc

    record = crud.replace_plan_content(db, record, revised, source)

    return schemas.PlanResponse(
        plan_id=record.id,
        user_id=user.id,
        source=source,
        plan=revised,
    )

@app.get("/api/nutrition-tip", response_model=schemas.NutritionTipResponse)
def get_nutrition_tip(goal: schemas.Goal):
    try:
        return schemas.NutritionTipResponse(tip=ai_service.nutrition_tip(goal))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI tip generation failed: {exc}") from exc
