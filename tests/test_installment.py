"""Testes para app/services/installment.py"""

from app.services.installment import add, list_active, process_monthly
from app.core.models import Installment, Transaction


def test_add_installment(db):
    result = add(db, "celular", "lazer", 12, 100.0)
    assert "12x" in result
    assert "R$ 100,00" in result
    assert "R$ 1.200,00" in result

    inst = db.query(Installment).first()
    assert inst.total_installments == 12
    assert inst.paid_installments == 1
    assert inst.active is True

    # First installment creates a transaction
    txn = db.query(Transaction).first()
    assert txn.amount == 100.0
    assert "1/12" in txn.description


def test_add_single_installment(db):
    add(db, "livro", "lazer", 1, 50.0)
    inst = db.query(Installment).first()
    assert inst.active is False  # 1x não precisa ficar ativa


def test_list_active_empty(db):
    result = list_active(db)
    assert "Nenhuma" in result


def test_list_active_with_data(db):
    add(db, "celular", "lazer", 12, 100.0)
    result = list_active(db)
    assert "celular" in result
    assert "1/12" in result


def test_process_monthly(db):
    add(db, "celular", "lazer", 3, 100.0)
    result = process_monthly(db)
    assert "1 parcela(s)" in result

    inst = db.query(Installment).first()
    assert inst.paid_installments == 2
    assert inst.active is True


def test_process_monthly_finishes_installment(db):
    add(db, "livro", "lazer", 2, 50.0)
    process_monthly(db)  # Pays 2/2

    inst = db.query(Installment).first()
    assert inst.paid_installments == 2
    assert inst.active is False
