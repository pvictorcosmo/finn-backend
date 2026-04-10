"""Testes para app/services/recurring.py"""

from app.services.recurring import add, list_active, remove, process_monthly
from app.core.models import RecurringExpense, Transaction


def test_add_recurring(db):
    result = add(db, "aluguel", "moradia", 1500.0)
    assert "registrado" in result
    assert "R$ 1.500,00" in result

    rec = db.query(RecurringExpense).first()
    assert rec.amount == 1500.0
    assert rec.active is True

    # Creates transaction for current month
    txn = db.query(Transaction).first()
    assert txn.amount == 1500.0
    assert "fixo" in txn.description


def test_add_recurring_updates_existing(db):
    add(db, "aluguel", "moradia", 1500.0)
    result = add(db, "aluguel", "moradia", 1800.0)
    assert "atualizado" in result

    recs = db.query(RecurringExpense).all()
    assert len(recs) == 1
    assert recs[0].amount == 1800.0


def test_list_active_empty(db):
    result = list_active(db)
    assert "Nenhum" in result


def test_list_active_with_data(db):
    add(db, "aluguel", "moradia", 1500.0)
    add(db, "internet", "moradia", 120.0)
    result = list_active(db)
    assert "aluguel" in result
    assert "internet" in result
    assert "R$ 1.620,00" in result


def test_remove(db):
    add(db, "netflix", "lazer", 55.0)
    result = remove(db, "netflix")
    assert "removido" in result

    rec = db.query(RecurringExpense).first()
    assert rec.active is False


def test_remove_not_found(db):
    result = remove(db, "spotify")
    assert "nao encontrado" in result


def test_remove_empty_description(db):
    result = remove(db, "")
    assert "Qual gasto fixo" in result


def test_process_monthly(db):
    add(db, "aluguel", "moradia", 1500.0)
    initial_count = db.query(Transaction).count()

    result = process_monthly(db)
    assert "1 gasto(s)" in result
    assert db.query(Transaction).count() == initial_count + 1
