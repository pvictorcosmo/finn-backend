"""Testes dos endpoints REST via TestClient."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.core.db import Base, get_db
import app.core.models  # noqa: F401
from app.core.models import Category, Salary, BudgetGoal
from app.routers import data, goals


@pytest.fixture
def client():
    """Cria app mínimo sem lifespan (evita seed/scheduler)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    # Seed
    session = Session()
    session.add(Category(name="alimentação", emoji="🍔", goal_group="essenciais"))
    session.add(Category(name="lazer", emoji="🎮", goal_group="desejos"))
    session.add(Salary(id=1, amount=5000))
    session.add(BudgetGoal(group_name="essenciais", label="Necessidades", emoji="🏠", percentage=50))
    session.add(BudgetGoal(group_name="desejos", label="Desejos", emoji="🎮", percentage=30))
    session.add(BudgetGoal(group_name="poupanca", label="Poupança", emoji="💰", percentage=20))
    session.commit()
    session.close()

    def override_get_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app = FastAPI()
    app.include_router(data.router)
    app.include_router(goals.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_categories(client):
    response = client.get("/categories")
    assert response.status_code == 200
    result = response.json()
    assert len(result) >= 2
    names = [c["name"] for c in result]
    assert "alimentação" in names


def test_get_transactions_empty(client):
    response = client.get("/transactions")
    assert response.status_code == 200
    assert response.json() == []


def test_get_salary(client):
    response = client.get("/salary")
    assert response.status_code == 200
    assert "amount" in response.json()


def test_set_salary(client):
    response = client.put("/salary", json={"amount": 8000})
    assert response.status_code == 200
    assert response.json()["amount"] == 8000


def test_get_goals(client):
    response = client.get("/goals")
    assert response.status_code == 200
    result = response.json()
    assert "salary" in result
    assert "goals" in result


def test_get_goals_status(client):
    response = client.get("/goals/status")
    assert response.status_code == 200
    result = response.json()
    assert "goals" in result
    assert len(result["goals"]) >= 2


def test_get_installments_empty(client):
    response = client.get("/installments")
    assert response.status_code == 200
    assert response.json() == []


def test_get_recurring_empty(client):
    response = client.get("/recurring")
    assert response.status_code == 200
    assert response.json() == []
