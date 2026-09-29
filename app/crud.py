import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from . import models, schemas

def get_user(db: Session, user_id: int):
    return db.get(models.User, user_id)

def get_user_by_name(db: Session, name: str):
    return db.scalar(select(models.User).where(models.User.name == name))

def upsert_user(db: Session, data: schemas.UserCreate):
    user = get_user_by_name(db, data.name)
    if user is None:
        user = models.User(**data.model_dump())
        db.add(user)
    else:
        for key, value in data.model_dump().items():
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

def create_plan(db: Session, user_id: int, plan: schemas.WorkoutPlan, source: str):
    record = models.WorkoutPlan(
        user_id=user_id,
        content_json=plan.model_dump_json(),
        source=source,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_latest_plan(db: Session, user_id: int):
    return db.scalar(
        select(models.WorkoutPlan)
        .where(models.WorkoutPlan.user_id == user_id)
        .order_by(models.WorkoutPlan.created_at.desc())
        .limit(1)
    )

def get_plan(db: Session, plan_id: int):
    return db.get(models.WorkoutPlan, plan_id)

def save_feedback(db: Session, plan_id: int, feedback: str):
    item = models.PlanFeedback(plan_id=plan_id, feedback_text=feedback)
    db.add(item)
    db.commit()
    return item

def replace_plan_content(db: Session, plan: models.WorkoutPlan, content: schemas.WorkoutPlan, source: str):
    plan.content_json = content.model_dump_json()
    plan.source = source
    db.commit()
    db.refresh(plan)
    return plan

def decode_plan(record: models.WorkoutPlan) -> schemas.WorkoutPlan:
    return schemas.WorkoutPlan.model_validate(json.loads(record.content_json))
