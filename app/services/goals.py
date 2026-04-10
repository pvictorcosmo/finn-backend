"""Servico de metas e salario."""

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.models import Salary, BudgetGoal, Category, Transaction
from app.core.utils import format_brl, get_date_range


def set_salary(db: Session, amount: float) -> str:
    salary = db.query(Salary).first()
    if salary:
        salary.amount = amount
    else:
        salary = Salary(id=1, amount=amount)
        db.add(salary)
    db.commit()

    goals = db.query(BudgetGoal).order_by(BudgetGoal.percentage.desc()).all()
    response = f"Salario definido: {format_brl(amount)}\n\nSuas metas 50-30-20:\n"
    for goal in goals:
        goal_amount = amount * (goal.percentage / 100)
        response += f"\n{goal.label} ({goal.percentage:.0f}%): {format_brl(goal_amount)}"
    return response


def query_goals(db: Session) -> str:
    salary = db.query(Salary).first()
    if not salary or salary.amount == 0:
        return "Voce ainda nao definiu seu salario. Diga: 'meu salario e X reais'"

    goals = db.query(BudgetGoal).order_by(BudgetGoal.percentage.desc()).all()
    month_start, _ = get_date_range("month")

    response = f"Metas do mes - Salario: {format_brl(salary.amount)}\n"

    for goal in goals:
        goal_amount = salary.amount * (goal.percentage / 100)
        spent = (
            db.query(func.sum(Transaction.amount))
            .join(Category)
            .filter(Category.goal_group == goal.group_name, Transaction.date >= month_start)
            .scalar()
            or 0
        )
        remaining = goal_amount - spent
        pct = (spent / goal_amount * 100) if goal_amount > 0 else 0

        if pct >= 100:
            status = "ESTOURADO"
        elif pct >= 80:
            status = "Atencao"
        else:
            status = "OK"

        response += f"\n{goal.label} ({goal.percentage:.0f}%)"
        response += f"\n   {format_brl(spent)} / {format_brl(goal_amount)} ({pct:.0f}%) {status}"
        if remaining > 0:
            response += f"\n   Restam: {format_brl(remaining)}"
        response += "\n"

    return response
