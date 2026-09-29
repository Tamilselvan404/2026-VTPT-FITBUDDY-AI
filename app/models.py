from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(40))
    weight_kg: Mapped[float] = mapped_column(Float)
    goal: Mapped[str] = mapped_column(String(80))
    intensity: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    plans: Mapped[list["WorkoutPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content_json: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="gemini")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="plans")
    feedback: Mapped[list["PlanFeedback"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )

class PlanFeedback(Base):
    __tablename__ = "plan_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("workout_plans.id"), index=True)
    feedback_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="feedback")
