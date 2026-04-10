"""Servico de parcelas."""

from sqlalchemy.orm import Session

from app.core.models import Installment, Transaction
from app.core.utils import format_brl
from app.services.category import find_or_create


def add(db: Session, description: str, category_name: str, total_installments: int, installment_amount: float) -> str:
    category = find_or_create(db, category_name)
    total_amount = total_installments * installment_amount

    installment = Installment(
        description=description,
        category_id=category.id,
        total_amount=total_amount,
        installment_amount=installment_amount,
        total_installments=total_installments,
        paid_installments=1,
        active=total_installments > 1,
    )
    db.add(installment)

    transaction = Transaction(
        amount=installment_amount,
        description=f"{description} (1/{total_installments})",
        category_id=category.id,
    )
    db.add(transaction)
    db.commit()

    response = f"Parcela registrada!\n"
    response += f"{category.name} - {description}\n"
    response += f"{total_installments}x de {format_brl(installment_amount)} = {format_brl(total_amount)}\n"
    response += f"Parcela 1/{total_installments} lancada neste mes"

    if total_installments > 1:
        response += f"\nAs proximas {total_installments - 1} parcelas serao lancadas automaticamente"

    return response


def list_active(db: Session) -> str:
    installments = db.query(Installment).filter(Installment.active == True).all()
    if not installments:
        return "Nenhuma parcela ativa no momento."

    response = "Parcelas ativas:\n"
    total_monthly = 0
    for inst in installments:
        remaining = inst.total_installments - inst.paid_installments
        response += f"\n{inst.category.name} - {inst.description}"
        response += f"\n   {format_brl(inst.installment_amount)}/mes - {inst.paid_installments}/{inst.total_installments} pagas"
        response += f"\n   Restam: {remaining} parcelas ({format_brl(remaining * inst.installment_amount)})\n"
        total_monthly += inst.installment_amount

    response += f"\nTotal mensal em parcelas: {format_brl(total_monthly)}"
    return response


def process_monthly(db: Session) -> str:
    """Lanca as parcelas do mes. Chamado pelo cron."""
    installments = db.query(Installment).filter(Installment.active == True).all()
    launched = 0

    for inst in installments:
        inst.paid_installments += 1
        transaction = Transaction(
            amount=inst.installment_amount,
            description=f"{inst.description} ({inst.paid_installments}/{inst.total_installments})",
            category_id=inst.category_id,
        )
        db.add(transaction)
        launched += 1

        if inst.paid_installments >= inst.total_installments:
            inst.active = False

    db.commit()
    return f"{launched} parcela(s) lancada(s)"
