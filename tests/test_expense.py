"""Testes para app/services/expense.py"""

from datetime import datetime

from app.services.expense import add, set_budget, delete_last, query_spending
from app.core.models import Transaction, Budget
from app.services.category import find_or_create


def test_add_expense(db):
    result = add(db, 50.0, "alimentação", "ifood")
    assert "R$ 50,00" in result
    assert "alimentação" in result
    assert "ifood" in result

    txn = db.query(Transaction).first()
    assert txn.amount == 50.0
    assert txn.description == "ifood"


def test_add_expense_creates_category_if_missing(db):
    result = add(db, 100.0, "roupas", "camiseta")
    assert "roupas" in result
    txn = db.query(Transaction).filter(Transaction.description == "camiseta").first()
    assert txn is not None


def test_add_expense_budget_alert_80_percent(db):
    set_budget(db, "alimentação", 100.0)
    result = add(db, 85.0, "alimentação", "restaurante")
    assert "85%" in result or "Atencao" in result


def test_add_expense_budget_alert_exceeded(db):
    set_budget(db, "alimentação", 100.0)
    result = add(db, 120.0, "alimentação", "mercado")
    assert "ESTOURADO" in result


def test_set_budget_new(db):
    result = set_budget(db, "alimentação", 500.0)
    assert "R$ 500,00" in result
    budget = db.query(Budget).first()
    assert budget.limit == 500.0


def test_set_budget_update(db):
    set_budget(db, "alimentação", 500.0)
    set_budget(db, "alimentação", 800.0)
    budgets = db.query(Budget).all()
    assert len(budgets) == 1
    assert budgets[0].limit == 800.0


def test_delete_last(db):
    add(db, 30.0, "transporte", "uber")
    add(db, 50.0, "alimentação", "ifood")
    result = delete_last(db)
    assert "Transacao removida" in result
    assert db.query(Transaction).count() == 1


def test_delete_last_empty(db):
    result = delete_last(db)
    assert "Nenhuma" in result


def test_query_spending_empty(db):
    result = query_spending(db, "month", None)
    assert "Nenhum" in result


def test_query_spending_with_data(db):
    # Set explicit local dates to avoid SQLite UTC vs local mismatch
    cat = find_or_create(db, "alimentação")
    now = datetime.now()
    db.add(Transaction(amount=50.0, description="ifood", category_id=cat.id, date=now))
    db.add(Transaction(amount=30.0, description="restaurante", category_id=cat.id, date=now))
    db.commit()
    result = query_spending(db, "month", None)
    assert "R$ 80,00" in result


def test_query_spending_by_category(db):
    cat1 = find_or_create(db, "alimentação")
    cat2 = find_or_create(db, "transporte")
    now = datetime.now()
    db.add(Transaction(amount=50.0, description="ifood", category_id=cat1.id, date=now))
    db.add(Transaction(amount=30.0, description="uber", category_id=cat2.id, date=now))
    db.commit()
    result = query_spending(db, "month", "alimentação")
    assert "R$ 50,00" in result
    assert "uber" not in result
