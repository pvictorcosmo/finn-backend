"""Servico de resumo diario."""

from datetime import datetime
from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.models import Transaction, Budget
from app.core.utils import format_brl, get_date_range, format_date


def build_daily(db: Session) -> str:
    today_start, today_end = get_date_range("today")
    month_start, _ = get_date_range("month")

    today_txns = db.query(Transaction).filter(Transaction.date >= today_start, Transaction.date <= today_end).all()
    month_txns = db.query(Transaction).filter(Transaction.date >= month_start).all()

    now = datetime.now()
    response = f"Resumo do dia - {format_date(now)}\n"

    if not today_txns:
        response += "\nNenhum gasto registrado hoje."
    else:
        by_cat: dict[str, dict] = {}
        today_total = 0
        for t in today_txns:
            key = t.category.name
            if key not in by_cat:
                by_cat[key] = {"total": 0, "count": 0}
            by_cat[key]["total"] += t.amount
            by_cat[key]["count"] += 1
            today_total += t.amount

        for name, data in by_cat.items():
            label = "transacao" if data["count"] == 1 else "transacoes"
            response += f"\n{name}: {format_brl(data['total'])} ({data['count']} {label})"
        response += f"\n\nTotal hoje: {format_brl(today_total)}"

    month_total = sum(t.amount for t in month_txns)
    response += f"\nTotal do mes: {format_brl(month_total)}"

    budgets = db.query(Budget).all()
    month_by_cat: dict[str, float] = defaultdict(float)
    for t in month_txns:
        month_by_cat[t.category.name] += t.amount

    alerts = []
    for budget in budgets:
        spent = month_by_cat.get(budget.category.name, 0)
        pct = (spent / budget.limit) * 100 if budget.limit > 0 else 0
        if pct >= 100:
            alerts.append(f"{budget.category.name}: ESTOURADO! {format_brl(spent)} / {format_brl(budget.limit)}")
        elif pct >= 80:
            alerts.append(f"{budget.category.name}: {pct:.0f}% - {format_brl(spent)} / {format_brl(budget.limit)}")
        else:
            alerts.append(f"{budget.category.name}: {pct:.0f}% - {format_brl(spent)} / {format_brl(budget.limit)}")

    if alerts:
        response += f"\n\nLimites:\n" + "\n".join(alerts)
    return response


def help_message() -> str:
    return """ZapFinance - Comandos:

Adicionar gasto:
"Gastei 50 no ifood"
"Paguei 30 de uber"

Compra parcelada:
"Comprei celular, 12 parcelas de 100"

Gasto fixo mensal:
"Pago 1000 de aluguel por mes"
"Minha internet e 120 mensais"

Consultar gastos:
"Quanto gastei esse mes?"

Listar transacoes:
"Minhas transacoes"

Ver parcelas:
"Minhas parcelas"

Ver gastos fixos:
"Meus gastos fixos"

Definir limite:
"Limite de 500 para alimentacao"

Definir salario:
"Meu salario e 5000 reais"

Consultar metas:
"Minhas metas"

Ver categorias:
"Categorias"

Apagar ultima:
"Apagar ultimo" ou "Desfazer"

Remover gasto fixo:
"Cancelar netflix\""""
