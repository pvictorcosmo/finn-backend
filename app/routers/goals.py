"""Endpoints para salário e metas 50-30-20."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.db import get_db
from app.core.models import Salary, BudgetGoal, Category, Transaction
from app.core.utils import get_date_range

router = APIRouter(tags=["goals"])


class SalaryRequest(BaseModel):
    amount: float


class GoalUpdateRequest(BaseModel):
    group_name: str
    percentage: float


class GoalsUpdateRequest(BaseModel):
    goals: list[GoalUpdateRequest]


@router.get("/salary")
def get_salary(db: Session = Depends(get_db)):
    salary = db.query(Salary).first()
    return {"amount": salary.amount if salary else 0}


@router.put("/salary")
def set_salary(req: SalaryRequest, db: Session = Depends(get_db)):
    salary = db.query(Salary).first()
    if salary:
        salary.amount = req.amount
    else:
        salary = Salary(id=1, amount=req.amount)
        db.add(salary)
    db.commit()
    return {"amount": salary.amount}


@router.get("/goals")
def get_goals(db: Session = Depends(get_db)):
    goals = db.query(BudgetGoal).order_by(BudgetGoal.percentage.desc()).all()
    salary = db.query(Salary).first()
    salary_amount = salary.amount if salary else 0

    return {
        "salary": salary_amount,
        "goals": [
            {
                "id": g.id,
                "group_name": g.group_name,
                "label": g.label,
                "emoji": g.emoji,
                "percentage": g.percentage,
                "amount": salary_amount * (g.percentage / 100),
            }
            for g in goals
        ],
    }


@router.put("/goals")
def update_goals(req: GoalsUpdateRequest, db: Session = Depends(get_db)):
    total = sum(g.percentage for g in req.goals)
    if abs(total - 100) > 0.01:
        return {"error": "Os percentuais devem somar 100%"}

    for goal_update in req.goals:
        goal = db.query(BudgetGoal).filter(BudgetGoal.group_name == goal_update.group_name).first()
        if goal:
            goal.percentage = goal_update.percentage
    db.commit()

    return get_goals(db)


@router.get("/goals/status")
def get_goals_status(db: Session = Depends(get_db)):
    """Retorna o progresso de cada meta no mês atual."""
    salary = db.query(Salary).first()
    salary_amount = salary.amount if salary else 0
    goals = db.query(BudgetGoal).order_by(BudgetGoal.percentage.desc()).all()

    month_start, _ = get_date_range("month")

    result = []
    for goal in goals:
        goal_amount = salary_amount * (goal.percentage / 100)

        # Soma transações do mês para categorias deste grupo
        spent = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .join(Category)
            .filter(Category.goal_group == goal.group_name, Transaction.date >= month_start)
            .scalar()
        )

        percentage_used = (spent / goal_amount * 100) if goal_amount > 0 else 0

        # Categorias neste grupo
        categories = (
            db.query(Category)
            .filter(Category.goal_group == goal.group_name)
            .order_by(Category.name)
            .all()
        )

        result.append({
            "group_name": goal.group_name,
            "label": goal.label,
            "emoji": goal.emoji,
            "percentage": goal.percentage,
            "goal_amount": goal_amount,
            "spent": float(spent),
            "remaining": goal_amount - float(spent),
            "percentage_used": round(percentage_used, 1),
            "categories": [{"id": c.id, "name": c.name, "emoji": c.emoji} for c in categories],
        })

    return {
        "salary": salary_amount,
        "month_total_spent": sum(r["spent"] for r in result),
        "goals": result,
    }


@router.put("/categories/{category_id}/goal-group")
def update_category_goal_group(
    category_id: int,
    group_name: str,
    db: Session = Depends(get_db),
):
    """Permite mover uma categoria para outro grupo de meta."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return {"error": "Categoria não encontrada"}
    if group_name not in ("essenciais", "desejos", "poupanca"):
        return {"error": "Grupo inválido. Use: essenciais, desejos, poupanca"}
    category.goal_group = group_name
    db.commit()
    return {"id": category.id, "name": category.name, "goal_group": category.goal_group}
