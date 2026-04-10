"""Servico de gastos fixos mensais."""

from sqlalchemy.orm import Session

from app.core.models import RecurringExpense, Transaction, Salary
from app.core.utils import format_brl
from app.services.category import find_or_create


def add(db: Session, description: str, category_name: str, amount: float) -> str:
    category = find_or_create(db, category_name)

    existing = (
        db.query(RecurringExpense)
        .filter(RecurringExpense.description == description.lower().strip(), RecurringExpense.active == True)
        .first()
    )
    if existing:
        existing.amount = amount
        existing.category_id = category.id
        db.commit()
        return f"Gasto fixo atualizado: {description} - {format_brl(amount)}/mes em {category.name}"

    recurring = RecurringExpense(
        description=description.lower().strip(),
        amount=amount,
        category_id=category.id,
    )
    db.add(recurring)

    transaction = Transaction(
        amount=amount,
        description=f"{description} (fixo)",
        category_id=category.id,
    )
    db.add(transaction)
    db.commit()

    response = f"Gasto fixo registrado!\n"
    response += f"{category.name} - {description}: {format_brl(amount)}/mes\n"
    response += f"Lancado {format_brl(amount)} neste mes.\n"
    response += f"Sera lancado automaticamente todo mes."
    return response


def list_active(db: Session) -> str:
    recurring = db.query(RecurringExpense).filter(RecurringExpense.active == True).all()
    if not recurring:
        return "Nenhum gasto fixo cadastrado."

    total = 0
    response = "Gastos fixos mensais:\n"
    for r in recurring:
        response += f"\n{r.category.name} - {r.description}: {format_brl(r.amount)}/mes"
        total += r.amount
    response += f"\n\nTotal fixo mensal: {format_brl(total)}"

    salary = db.query(Salary).first()
    if salary and salary.amount > 0:
        pct = (total / salary.amount) * 100
        response += f"\n({pct:.0f}% do salario)"

    return response


def remove(db: Session, description: str) -> str:
    if not description:
        return "Qual gasto fixo deseja remover? Diga o nome, ex: 'cancelar aluguel'"

    normalized = description.lower().strip()
    recurring = (
        db.query(RecurringExpense)
        .filter(RecurringExpense.active == True, RecurringExpense.description.ilike(f"%{normalized}%"))
        .first()
    )
    if not recurring:
        return f"Gasto fixo '{description}' nao encontrado."

    recurring.active = False
    db.commit()
    return f"Gasto fixo removido: {recurring.description} ({format_brl(recurring.amount)}/mes)"


def process_monthly(db: Session) -> str:
    """Lanca gastos fixos do mes. Chamado pelo cron."""
    recurring = db.query(RecurringExpense).filter(RecurringExpense.active == True).all()
    launched = 0
    for r in recurring:
        transaction = Transaction(
            amount=r.amount,
            description=f"{r.description} (fixo)",
            category_id=r.category_id,
        )
        db.add(transaction)
        launched += 1
    db.commit()
    return f"{launched} gasto(s) fixo(s) lancado(s)"
