"""Servico de gastos (transacoes)."""

from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.models import Category, Transaction, Budget, Salary, BudgetGoal
from app.core.utils import format_brl, get_date_range, get_month_name, format_date
from app.services.category import find_or_create


def add(db: Session, amount: float, category_name: str, description: str) -> str:
    category = find_or_create(db, category_name)

    transaction = Transaction(amount=amount, description=description, category_id=category.id)
    db.add(transaction)
    db.commit()

    month_start, _ = get_date_range("month")
    month_total = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.category_id == category.id, Transaction.date >= month_start)
        .scalar()
        or 0
    )

    response = f"Adicionado: {format_brl(amount)} em {category.name} ({description})"
    response += f"\nTotal do mes em {category.name}: {format_brl(month_total)}"

    budget = db.query(Budget).filter(Budget.category_id == category.id).first()
    if budget:
        percentage = (month_total / budget.limit) * 100
        response += f" / {format_brl(budget.limit)}"
        if percentage >= 100:
            response += f"\n\nLIMITE ESTOURADO! Voce ultrapassou {category.name} em {format_brl(month_total - budget.limit)}"
        elif percentage >= 80:
            response += f"\n\nAtencao: {percentage:.0f}% do limite de {category.name} utilizado"

    goal_group = category.goal_group or "desejos"
    salary = db.query(Salary).first()
    if salary and salary.amount > 0:
        goal = db.query(BudgetGoal).filter(BudgetGoal.group_name == goal_group).first()
        if goal:
            goal_amount = salary.amount * (goal.percentage / 100)
            group_spent = (
                db.query(func.sum(Transaction.amount))
                .join(Category)
                .filter(Category.goal_group == goal_group, Transaction.date >= month_start)
                .scalar()
                or 0
            )
            goal_pct = (group_spent / goal_amount * 100) if goal_amount > 0 else 0
            response += f"\n\nMeta {goal.label} ({goal.percentage:.0f}%): {format_brl(group_spent)} / {format_brl(goal_amount)} ({goal_pct:.0f}%)"
            if goal_pct >= 100:
                response += " - META ESTOURADA!"
            elif goal_pct >= 80:
                response += " - Atencao!"

    return response


def query_spending(db: Session, period: str, category_name: str | None) -> str:
    start, end = get_date_range(period)
    query = db.query(Transaction).filter(Transaction.date >= start, Transaction.date <= end)

    if category_name:
        cat = db.query(Category).filter(Category.name == category_name.lower().strip()).first()
        if cat:
            query = query.filter(Transaction.category_id == cat.id)

    transactions = query.all()
    if not transactions:
        return "Nenhum gasto encontrado nesse periodo."

    by_category: dict[str, dict] = {}
    for t in transactions:
        key = t.category.name
        if key not in by_category:
            by_category[key] = {"total": 0, "count": 0}
        by_category[key]["total"] += t.amount
        by_category[key]["count"] += 1

    period_label = "hoje" if period == "today" else "esta semana" if period == "week" else get_month_name(datetime.now())

    response = f"Gastos de {period_label}:\n"
    grand_total = 0
    for name, data in by_category.items():
        label = "transacao" if data["count"] == 1 else "transacoes"
        response += f"\n{name}: {format_brl(data['total'])} ({data['count']} {label})"
        grand_total += data["total"]

    response += f"\n\nTotal: {format_brl(grand_total)}"

    budgets = db.query(Budget).all()
    alerts = []
    for budget in budgets:
        cat_data = by_category.get(budget.category.name)
        if cat_data:
            pct = (cat_data["total"] / budget.limit) * 100
            if pct >= 100:
                alerts.append(f"{budget.category.name}: ESTOURADO ({format_brl(cat_data['total'])} / {format_brl(budget.limit)})")
            elif pct >= 80:
                alerts.append(f"{budget.category.name}: {pct:.0f}% ({format_brl(cat_data['total'])} / {format_brl(budget.limit)})")

    if alerts:
        response += "\n\n" + "\n".join(alerts)
    return response


def set_budget(db: Session, category_name: str, limit: float) -> str:
    category = find_or_create(db, category_name)
    budget = db.query(Budget).filter(Budget.category_id == category.id).first()
    if budget:
        budget.limit = limit
    else:
        budget = Budget(category_id=category.id, limit=limit)
        db.add(budget)
    db.commit()
    return f"Limite de {format_brl(limit)} definido para {category.name}"


def list_transactions(db: Session, period: str, category_name: str | None, limit: int) -> str:
    start, end = get_date_range(period)
    query = db.query(Transaction).filter(Transaction.date >= start, Transaction.date <= end)

    if category_name:
        cat = db.query(Category).filter(Category.name == category_name.lower().strip()).first()
        if cat:
            query = query.filter(Transaction.category_id == cat.id)

    transactions = query.order_by(Transaction.date.desc()).limit(limit).all()
    if not transactions:
        return "Nenhuma transacao encontrada nesse periodo."

    response = "Ultimas transacoes:\n"
    for t in transactions:
        response += f"\n{format_date(t.date)} - {format_brl(t.amount)} - {t.description} ({t.category.name})"
    return response


def delete_last(db: Session) -> str:
    last = db.query(Transaction).order_by(Transaction.created_at.desc()).first()
    if not last:
        return "Nenhuma transacao encontrada para apagar."
    response = f"Transacao removida: {format_brl(last.amount)} - {last.description} ({last.category.name})"
    db.delete(last)
    db.commit()
    return response
