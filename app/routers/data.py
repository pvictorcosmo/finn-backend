from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import Category, Transaction, Installment, RecurringExpense
from app.core.utils import get_date_range

router = APIRouter(tags=["data"])


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.name).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "emoji": c.emoji,
            "budget": c.budget.limit if c.budget else None,
            "goal_group": c.goal_group or "desejos",
        }
        for c in categories
    ]


@router.get("/transactions")
def get_transactions(
    period: str = "month",
    category: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    start, end = get_date_range(period)
    query = db.query(Transaction).filter(Transaction.date >= start, Transaction.date <= end)

    if category:
        cat = db.query(Category).filter(Category.name == category.lower().strip()).first()
        if cat:
            query = query.filter(Transaction.category_id == cat.id)

    transactions = query.order_by(Transaction.date.desc()).limit(limit).all()
    return [
        {
            "id": t.id,
            "amount": t.amount,
            "description": t.description,
            "category": t.category.name,
            "emoji": t.category.emoji,
            "date": t.date.isoformat(),
        }
        for t in transactions
    ]


@router.get("/installments")
def get_installments(active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(Installment)
    if active_only:
        query = query.filter(Installment.active == True)
    installments = query.order_by(Installment.created_at.desc()).all()
    return [
        {
            "id": i.id,
            "description": i.description,
            "category": i.category.name,
            "emoji": i.category.emoji,
            "total_amount": i.total_amount,
            "installment_amount": i.installment_amount,
            "total_installments": i.total_installments,
            "paid_installments": i.paid_installments,
            "remaining_installments": i.total_installments - i.paid_installments,
            "remaining_amount": (i.total_installments - i.paid_installments) * i.installment_amount,
            "active": i.active,
        }
        for i in installments
    ]


@router.get("/recurring")
def get_recurring(db: Session = Depends(get_db)):
    recurring = db.query(RecurringExpense).filter(RecurringExpense.active == True).order_by(RecurringExpense.amount.desc()).all()
    return [
        {
            "id": r.id,
            "description": r.description,
            "category": r.category.name,
            "emoji": r.category.emoji,
            "amount": r.amount,
        }
        for r in recurring
    ]
