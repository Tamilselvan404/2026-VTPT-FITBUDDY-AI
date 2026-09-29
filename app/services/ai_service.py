from __future__ import annotations

import json
from typing import Optional
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None
from pydantic import ValidationError
from ..config import get_settings
from ..schemas import WorkoutPlan

settings = get_settings()
_client: Optional[genai.Client] = None

if settings.google_api_key.strip() and genai is not None:
    _client = genai.Client(api_key=settings.google_api_key.strip())

DAYS = [
    ("Day 1", "Full body"),
    ("Day 2", "Cardio + core"),
    ("Day 3", "Upper body"),
    ("Day 4", "Recovery + mobility"),
    ("Day 5", "Lower body"),
    ("Day 6", "Full body conditioning"),
    ("Day 7", "Rest + gentle mobility"),
]

def _demo_plan(name: str, goal: str, intensity: str) -> WorkoutPlan:
    beginner = intensity == "beginner"
    sets = 2 if beginner else 3
    reps = "8-12" if goal in {"strength", "general fitness"} else "30-45 sec"

    exercise_sets = {
        "Full body": [
            ("Bodyweight squat", sets, reps, 60),
            ("Incline push-up", sets, reps, 60),
            ("Glute bridge", sets, reps, 45),
            ("Bird dog", sets, reps, 45),
        ],
        "Cardio + core": [
            ("Brisk walk", 1, "20-30 min", 0),
            ("Dead bug", sets, reps, 45),
            ("Side plank", sets, "15-30 sec/side", 45),
        ],
        "Upper body": [
            ("Incline push-up", sets, reps, 60),
            ("Resistance-band row", sets, reps, 60),
            ("Wall slide", sets, reps, 45),
        ],
        "Recovery + mobility": [
            ("Easy walk", 1, "15-20 min", 0),
            ("Cat-cow", 2, "6-8", 30),
            ("Hip flexor stretch", 2, "20-30 sec/side", 30),
        ],
        "Lower body": [
            ("Chair squat", sets, reps, 60),
            ("Step-up", sets, reps, 60),
            ("Calf raise", sets, reps, 45),
        ],
        "Full body conditioning": [
            ("Sit-to-stand", sets, reps, 60),
            ("Wall push-up", sets, reps, 60),
            ("March in place", 3, "45 sec", 45),
        ],
        "Rest + gentle mobility": [
            ("Gentle walk", 1, "10-20 min", 0),
            ("Easy full-body mobility", 2, "5-8 min", 30),
        ],
    }

    days = []
    for day, focus in DAYS:
        exercises = [
            {
                "name": name_,
                "sets": sets_,
                "reps": reps_,
                "rest_seconds": rest,
                "notes": "Stop if you feel pain; keep movements controlled.",
            }
            for name_, sets_, reps_, rest in exercise_sets[focus]
        ]
        days.append({
            "day": day,
            "focus": focus,
            "duration_minutes": 25 if focus in {"Rest + gentle mobility", "Recovery + mobility"} else 35,
            "exercises": exercises,
        })

    return WorkoutPlan(
        title=f"{name}'s 7-Day FitBuddy Plan",
        summary=f"A conservative {intensity} plan oriented toward {goal}. Build consistency first and adjust gradually.",
        safety_notes=[
            "This is general wellness guidance, not medical advice.",
            "Warm up before training and use controlled technique.",
            "Stop and seek appropriate professional advice if exercise causes concerning pain, dizziness, or other unusual symptoms.",
        ],
        days=days,
    )

def _gemini_plan(name: str, age: int, gender: str, weight_kg: float, goal: str, intensity: str) -> WorkoutPlan:
    if _client is None:
        return _demo_plan(name, goal, intensity)

    prompt = f"""
Create a safe, conservative 7-day fitness plan for an adult.

Profile:
- Name: {name}
- Age: {age}
- Gender: {gender}
- Weight: {weight_kg:.1f} kg
- Goal: {goal}
- Intensity: {intensity}

Requirements:
- Return exactly 7 days.
- Favor broadly applicable exercises that need little equipment.
- Do not prescribe extreme calorie restriction, dehydration, supplements, or unsafe challenges.
- Do not diagnose conditions or claim the plan treats disease.
- Include at least one recovery/rest-oriented day.
- Use sensible volume for the requested intensity.
- Include a safety note that pain or concerning symptoms are reasons to stop and seek appropriate professional advice.
- Keep reps practical and avoid impossible precision.
"""

    response = _client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=WorkoutPlan,
            temperature=0.4,
        ),
    )

    if getattr(response, "parsed", None) is not None:
        parsed = response.parsed
        return parsed if isinstance(parsed, WorkoutPlan) else WorkoutPlan.model_validate(parsed)

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        return WorkoutPlan.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise RuntimeError(f"Gemini returned invalid structured data: {exc}") from exc

def generate_plan(name: str, age: int, gender: str, weight_kg: float, goal: str, intensity: str) -> tuple[WorkoutPlan, str]:
    plan = _gemini_plan(name, age, gender, weight_kg, goal, intensity)
    return plan, "gemini" if _client else "demo"

def revise_plan(current_plan: WorkoutPlan, feedback: str) -> tuple[WorkoutPlan, str]:
    if _client is None:
        revised = current_plan.model_copy(deep=True)
        revised.summary = f"{current_plan.summary} Revision requested: {feedback}"
        revised.safety_notes = list(dict.fromkeys(
            revised.safety_notes + ["Revision is based on user feedback and should be adjusted conservatively."]
        ))
        return revised, "demo"

    prompt = f"""
Revise this existing adult fitness plan according to the user's feedback.

Current plan:
{current_plan.model_dump_json(indent=2)}

User feedback:
{feedback}

Keep the plan safe and practical. Do not introduce extreme dieting, dangerous challenges, medical treatment claims, or unsafe exercise prescriptions. Preserve useful parts that the feedback does not ask to change.
"""

    response = _client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=WorkoutPlan,
            temperature=0.35,
        ),
    )

    if getattr(response, "parsed", None) is not None:
        parsed = response.parsed
        return (
            parsed if isinstance(parsed, WorkoutPlan) else WorkoutPlan.model_validate(parsed),
            "gemini",
        )

    return WorkoutPlan.model_validate_json(response.text), "gemini"

def nutrition_tip(goal: str) -> str:
    if _client is None:
        return {
            "general fitness": "Build meals around regular, varied foods and include a protein source, fruits or vegetables, and enough fluids.",
            "strength": "Include a protein-rich food at regular meals and pair it with carbohydrate sources that support your training.",
            "endurance": "Regular meals containing carbohydrates and fluids can help support endurance sessions and recovery.",
            "mobility": "Stay hydrated and keep meals varied, with enough protein and colorful plant foods to support recovery.",
            "weight management": "Focus on regular balanced meals, fiber-rich foods, and sustainable habits rather than aggressive restriction.",
        }.get(goal, "Choose varied, balanced meals and stay hydrated.")

    prompt = (
        f"Give one concise, practical nutrition or recovery tip for an adult "
        f"whose fitness goal is {goal}. No calorie-cutting extremes, supplements, or medical claims."
    )
    response = _client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3),
    )
    return (response.text or "").strip() or "Choose varied, balanced meals and stay hydrated."
