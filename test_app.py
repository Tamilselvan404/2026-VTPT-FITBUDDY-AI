import os
os.environ["DATABASE_URL"] = "sqlite:///./test_fitbuddy.db"
os.environ["GOOGLE_API_KEY"] = ""

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def teardown_module():
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove("./test_fitbuddy.db")
    except FileNotFoundError:
        pass

def adult_payload():
    return {
        "name": "Test User",
        "age": 25,
        "gender": "prefer not to say",
        "weight_kg": 70,
        "goal": "general fitness",
        "intensity": "beginner",
    }

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["gemini_configured"] is False

def test_homepage():
    response = client.get("/")
    assert response.status_code == 200

def test_minor_is_rejected():
    payload = adult_payload()
    payload["age"] = 17
    response = client.post("/api/plans/generate", json=payload)
    assert response.status_code == 403

def test_demo_plan_generation_and_latest():
    response = client.post("/api/plans/generate", json=adult_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "demo"
    assert len(body["plan"]["days"]) == 7
    assert body["plan_id"] > 0

    latest = client.get(f"/api/users/{body['user_id']}/plans/latest")
    assert latest.status_code == 200
    assert latest.json()["plan_id"] == body["plan_id"]

def test_plan_revision():
    generated = client.post("/api/plans/generate", json=adult_payload()).json()
    response = client.post(
        f"/api/plans/{generated['plan_id']}/revise",
        json={"feedback": "Keep the sessions shorter and emphasize recovery."},
    )
    assert response.status_code == 200
    assert response.json()["plan_id"] == generated["plan_id"]

def test_nutrition_tip():
    response = client.get("/api/nutrition-tip?goal=strength")
    assert response.status_code == 200
    assert response.json()["tip"]
