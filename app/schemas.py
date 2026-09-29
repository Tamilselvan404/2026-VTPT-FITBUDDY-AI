from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Goal = Literal["general fitness", "strength", "endurance", "mobility", "weight management"]
Intensity = Literal["beginner", "moderate", "advanced"]
Gender = Literal["female", "male", "non-binary", "prefer not to say"]

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    age: int = Field(ge=13, le=100)
    gender: Gender
    weight_kg: float = Field(gt=20, le=400)
    goal: Goal
    intensity: Intensity

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.strip().split())

class UserRead(UserCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Exercise(BaseModel):
    name: str
    sets: int = Field(ge=1, le=10)
    reps: str
    rest_seconds: int = Field(ge=0, le=600)
    notes: str = ""

class DayPlan(BaseModel):
    day: str
    focus: str
    duration_minutes: int = Field(ge=5, le=180)
    exercises: list[Exercise] = Field(min_length=1, max_length=12)

class WorkoutPlan(BaseModel):
    title: str
    summary: str
    safety_notes: list[str] = Field(min_length=1, max_length=8)
    days: list[DayPlan] = Field(min_length=7, max_length=7)

class PlanResponse(BaseModel):
    plan_id: int
    user_id: int
    source: str
    plan: WorkoutPlan

class PlanRevisionRequest(BaseModel):
    feedback: str = Field(min_length=3, max_length=1000)

class NutritionTipResponse(BaseModel):
    tip: str

class HealthResponse(BaseModel):
    status: str
    gemini_configured: bool
    model: str
