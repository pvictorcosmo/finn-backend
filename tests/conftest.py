"""Fixtures compartilhadas para testes — usa SQLite in-memory."""

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
import app.core.models  # noqa: F401 — registra todos os models no metadata
from app.core.models import Category, Salary, BudgetGoal

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture
def db():
    """Cria banco SQLite in-memory para cada teste."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    Session = sessionmaker(bind=TEST_ENGINE)
    session = Session()

    # Seed mínimo
    categories = [
        Category(id=1, name="alimentação", emoji="🍔", goal_group="essenciais"),
        Category(id=2, name="transporte", emoji="🚗", goal_group="essenciais"),
        Category(id=3, name="lazer", emoji="🎮", goal_group="desejos"),
        Category(id=4, name="moradia", emoji="🏠", goal_group="essenciais"),
    ]
    for cat in categories:
        session.add(cat)

    session.add(Salary(id=1, amount=5000))

    goals = [
        BudgetGoal(group_name="essenciais", label="Necessidades Essenciais", emoji="🏠", percentage=50),
        BudgetGoal(group_name="desejos", label="Desejos", emoji="🎮", percentage=30),
        BudgetGoal(group_name="poupanca", label="Poupança e Investimentos", emoji="💰", percentage=20),
    ]
    for goal in goals:
        session.add(goal)

    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=TEST_ENGINE)
