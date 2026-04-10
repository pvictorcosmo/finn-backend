"""Testes para app/services/goals.py"""

from app.services.goals import set_salary, query_goals
from app.services.expense import add
from app.core.models import Salary


def test_set_salary(db):
    result = set_salary(db, 8000.0)
    assert "R$ 8.000,00" in result
    assert "50-30-20" in result

    salary = db.query(Salary).first()
    assert salary.amount == 8000.0


def test_set_salary_updates_existing(db):
    set_salary(db, 5000.0)
    set_salary(db, 7000.0)
    salaries = db.query(Salary).all()
    assert len(salaries) == 1
    assert salaries[0].amount == 7000.0


def test_query_goals_no_salary(db):
    # Reset salary to 0
    salary = db.query(Salary).first()
    salary.amount = 0
    db.commit()

    result = query_goals(db)
    assert "nao definiu" in result


def test_query_goals_with_spending(db):
    add(db, 500.0, "alimentação", "mercado")
    result = query_goals(db)
    assert "Necessidades Essenciais" in result
    assert "R$ 500,00" in result


def test_query_goals_shows_all_groups(db):
    result = query_goals(db)
    assert "Necessidades Essenciais" in result
    assert "Desejos" in result
    assert "Poupança" in result or "Poupanca" in result
