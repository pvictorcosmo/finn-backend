"""Servico de categorias."""

from sqlalchemy.orm import Session

from app.core.models import Category
from app.core.utils import format_brl


def find_or_create(db: Session, name: str) -> Category:
    normalized = name.lower().strip()
    category = db.query(Category).filter(Category.name == normalized).first()
    if not category:
        category = Category(name=normalized)
        db.add(category)
        db.commit()
        db.refresh(category)
    return category


def list_all(db: Session) -> str:
    categories = db.query(Category).order_by(Category.name).all()
    response = "Categorias:\n"
    for cat in categories:
        response += f"\n{cat.name}"
        if cat.budget:
            response += f" (limite: {format_brl(cat.budget.limit)})"
    return response
