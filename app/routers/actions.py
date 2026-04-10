"""Funções de ação no banco de dados. Usadas pelos agentes e pelos endpoints REST."""

from datetime import datetime
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.models import Category, Transaction, Budget, Salary, BudgetGoal, Installment, RecurringExpense
from app.core.utils import format_brl, get_date_range, get_month_name, format_date


def find_or_create_category(db: Session, name: str) -> Category:
    normalized = name.lower().strip()
    category = db.query(Category).filter(Category.name == normalized).first()
    if not category:
        category = Category(name=normalized)
        db.add(category)
        db.commit()
        db.refresh(category)
    return category


def add_expense(db: Session, amount: float, category_name: str, description: str) -> str:
    category = find_or_create_category(db, category_name)

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

    response = f"✅ Adicionado: {format_brl(amount)} em {category.emoji} {category.name} ({description})"
    response += f"\n📊 Total do mês em {category.name}: {format_brl(month_total)}"

    budget = db.query(Budget).filter(Budget.category_id == category.id).first()
    if budget:
        percentage = (month_total / budget.limit) * 100
        response += f" / {format_brl(budget.limit)}"

        if percentage >= 100:
            response += f"\n\n🚨 *LIMITE ESTOURADO!* Você ultrapassou o limite de {category.name} em {format_brl(month_total - budget.limit)}"
        elif percentage >= 80:
            response += f"\n\n⚠️ Atenção: {percentage:.0f}% do limite de {category.name} utilizado"

    # Mostrar progresso da meta 50-30-20
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
            response += f"\n\n🎯 Meta *{goal.label}* ({goal.percentage:.0f}%): {format_brl(group_spent)} / {format_brl(goal_amount)} ({goal_pct:.0f}%)"
            if goal_pct >= 100:
                response += " 🚨 META ESTOURADA!"
            elif goal_pct >= 80:
                response += " ⚠️"

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
        return "📊 Nenhum gasto encontrado nesse período."

    by_category: dict[str, dict] = {}
    for t in transactions:
        key = t.category.name
        if key not in by_category:
            by_category[key] = {"emoji": t.category.emoji, "total": 0, "count": 0}
        by_category[key]["total"] += t.amount
        by_category[key]["count"] += 1

    period_label = "hoje" if period == "today" else "esta semana" if period == "week" else get_month_name(datetime.now())

    response = f"📊 *Gastos de {period_label}:*\n"
    grand_total = 0
    for name, data in by_category.items():
        label = "transação" if data["count"] == 1 else "transações"
        response += f"\n{data['emoji']} {name}: {format_brl(data['total'])} ({data['count']} {label})"
        grand_total += data["total"]

    response += f"\n\n💰 *Total: {format_brl(grand_total)}*"

    budgets = db.query(Budget).all()
    alerts = []
    for budget in budgets:
        cat_data = by_category.get(budget.category.name)
        if cat_data:
            pct = (cat_data["total"] / budget.limit) * 100
            if pct >= 100:
                alerts.append(f"🚨 {budget.category.name}: ESTOURADO ({format_brl(cat_data['total'])} / {format_brl(budget.limit)})")
            elif pct >= 80:
                alerts.append(f"⚠️ {budget.category.name}: {pct:.0f}% ({format_brl(cat_data['total'])} / {format_brl(budget.limit)})")

    if alerts:
        response += "\n\n" + "\n".join(alerts)
    return response


def set_budget(db: Session, category_name: str, limit: float) -> str:
    category = find_or_create_category(db, category_name)
    budget = db.query(Budget).filter(Budget.category_id == category.id).first()
    if budget:
        budget.limit = limit
    else:
        budget = Budget(category_id=category.id, limit=limit)
        db.add(budget)
    db.commit()
    return f"✅ Limite de {format_brl(limit)} definido para {category.emoji} {category.name}"


def list_categories(db: Session) -> str:
    categories = db.query(Category).order_by(Category.name).all()
    response = "📋 *Categorias:*\n"
    for cat in categories:
        response += f"\n{cat.emoji} {cat.name}"
        if cat.budget:
            response += f" (limite: {format_brl(cat.budget.limit)})"
    return response


def list_transactions(db: Session, period: str, category_name: str | None, limit: int) -> str:
    start, end = get_date_range(period)
    query = db.query(Transaction).filter(Transaction.date >= start, Transaction.date <= end)

    if category_name:
        cat = db.query(Category).filter(Category.name == category_name.lower().strip()).first()
        if cat:
            query = query.filter(Transaction.category_id == cat.id)

    transactions = query.order_by(Transaction.date.desc()).limit(limit).all()
    if not transactions:
        return "📋 Nenhuma transação encontrada nesse período."

    response = "📋 *Últimas transações:*\n"
    for t in transactions:
        response += f"\n{t.category.emoji} {format_date(t.date)} - {format_brl(t.amount)} - {t.description} ({t.category.name})"
    return response


def delete_last(db: Session) -> str:
    last = db.query(Transaction).order_by(Transaction.created_at.desc()).first()
    if not last:
        return "❌ Nenhuma transação encontrada para apagar."
    response = f"🗑️ Transação removida: {format_brl(last.amount)} - {last.description} ({last.category.name})"
    db.delete(last)
    db.commit()
    return response


def add_installment_action(
    db: Session, description: str, category_name: str,
    total_installments: int, installment_amount: float,
) -> str:
    category = find_or_create_category(db, category_name)
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

    # Lançar parcela do mês atual como transação
    transaction = Transaction(
        amount=installment_amount,
        description=f"{description} (1/{total_installments})",
        category_id=category.id,
    )
    db.add(transaction)
    db.commit()

    response = f"✅ Parcela registrada!\n"
    response += f"📦 {category.emoji} {description}\n"
    response += f"💳 {total_installments}x de {format_brl(installment_amount)} = {format_brl(total_amount)}\n"
    response += f"📌 Parcela 1/{total_installments} lançada neste mês"

    if total_installments > 1:
        response += f"\n🔄 As próximas {total_installments - 1} parcelas serão lançadas automaticamente"

    return response


def list_installments_action(db: Session) -> str:
    installments = db.query(Installment).filter(Installment.active == True).all()
    if not installments:
        return "📋 Nenhuma parcela ativa no momento."

    response = "📋 *Parcelas ativas:*\n"
    total_monthly = 0
    for inst in installments:
        remaining = inst.total_installments - inst.paid_installments
        response += f"\n📦 {inst.category.emoji} {inst.description}"
        response += f"\n   {format_brl(inst.installment_amount)}/mês — {inst.paid_installments}/{inst.total_installments} pagas"
        response += f"\n   Restam: {remaining} parcelas ({format_brl(remaining * inst.installment_amount)})\n"
        total_monthly += inst.installment_amount

    response += f"\n💳 *Total mensal em parcelas: {format_brl(total_monthly)}*"
    return response


def process_monthly_installments(db: Session) -> str:
    """Lança as parcelas do mês para todos os parcelamentos ativos. Chamado pelo cron."""
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
    return f"✅ {launched} parcela(s) lançada(s) automaticamente"


def add_recurring_action(db: Session, description: str, category_name: str, amount: float) -> str:
    category = find_or_create_category(db, category_name)

    # Verifica se ja existe um gasto fixo com mesma descricao
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

    # Lanca transacao do mes atual
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


def list_recurring_action(db: Session) -> str:
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


def remove_recurring_action(db: Session, description: str) -> str:
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


def process_monthly_recurring(db: Session) -> str:
    """Lanca os gastos fixos do mes. Chamado pelo cron."""
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


def set_salary_action(db: Session, amount: float) -> str:
    salary = db.query(Salary).first()
    if salary:
        salary.amount = amount
    else:
        salary = Salary(id=1, amount=amount)
        db.add(salary)
    db.commit()

    goals = db.query(BudgetGoal).order_by(BudgetGoal.percentage.desc()).all()
    response = f"✅ Salário definido: {format_brl(amount)}\n\n🎯 *Suas metas 50-30-20:*\n"
    for goal in goals:
        goal_amount = amount * (goal.percentage / 100)
        response += f"\n{goal.emoji} {goal.label} ({goal.percentage:.0f}%): {format_brl(goal_amount)}"
    return response


def query_goals_action(db: Session) -> str:
    salary = db.query(Salary).first()
    if not salary or salary.amount == 0:
        return "❌ Você ainda não definiu seu salário. Diga: 'meu salário é X reais'"

    goals = db.query(BudgetGoal).order_by(BudgetGoal.percentage.desc()).all()
    month_start, _ = get_date_range("month")

    response = f"🎯 *Metas do mês - Salário: {format_brl(salary.amount)}*\n"

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
            status = "🚨 ESTOURADO"
        elif pct >= 80:
            status = "⚠️"
        else:
            status = "✅"

        response += f"\n{goal.emoji} *{goal.label}* ({goal.percentage:.0f}%)"
        response += f"\n   {format_brl(spent)} / {format_brl(goal_amount)} ({pct:.0f}%) {status}"
        if remaining > 0:
            response += f"\n   Restam: {format_brl(remaining)}"
        response += "\n"

    return response


def help_message() -> str:
    return """🤖 *ZapFinance - Comandos:*

💸 *Adicionar gasto:*
"Gastei 50 no ifood"
"Paguei 30 de uber"

💳 *Compra parcelada:*
"Comprei celular, 12 parcelas de 100"
"Parcelei TV em 10x de 200"

📊 *Consultar gastos:*
"Quanto gastei esse mês?"
"Gastos da semana"

📋 *Listar transações:*
"Minhas transações"

📋 *Ver parcelas ativas:*
"Minhas parcelas"

🎯 *Definir limite:*
"Limite de 500 reais para alimentação"

💰 *Definir salário:*
"Meu salário é 5000 reais"

🎯 *Consultar metas 50-30-20:*
"Minhas metas" ou "Como estão minhas metas?"

📂 *Ver categorias:*
"Categorias"

🗑️ *Apagar última:*
"Apagar último" ou "Desfazer\""""


def build_daily_summary(db: Session) -> str:
    today_start, today_end = get_date_range("today")
    month_start, _ = get_date_range("month")

    today_txns = db.query(Transaction).filter(Transaction.date >= today_start, Transaction.date <= today_end).all()
    month_txns = db.query(Transaction).filter(Transaction.date >= month_start).all()

    now = datetime.now()
    response = f"📊 *Resumo do dia - {format_date(now)}*\n"

    if not today_txns:
        response += "\nNenhum gasto registrado hoje."
    else:
        by_cat: dict[str, dict] = {}
        today_total = 0
        for t in today_txns:
            key = t.category.name
            if key not in by_cat:
                by_cat[key] = {"emoji": t.category.emoji, "total": 0, "count": 0}
            by_cat[key]["total"] += t.amount
            by_cat[key]["count"] += 1
            today_total += t.amount

        for name, data in by_cat.items():
            label = "transação" if data["count"] == 1 else "transações"
            response += f"\n{data['emoji']} {name}: {format_brl(data['total'])} ({data['count']} {label})"
        response += f"\n\n💰 *Total hoje: {format_brl(today_total)}*"

    month_total = sum(t.amount for t in month_txns)
    response += f"\n💰 *Total do mês: {format_brl(month_total)}*"

    budgets = db.query(Budget).all()
    month_by_cat: dict[str, float] = defaultdict(float)
    for t in month_txns:
        month_by_cat[t.category.name] += t.amount

    alerts = []
    for budget in budgets:
        spent = month_by_cat.get(budget.category.name, 0)
        pct = (spent / budget.limit) * 100 if budget.limit > 0 else 0
        if pct >= 100:
            alerts.append(f"🚨 {budget.category.emoji} {budget.category.name}: ESTOURADO! {format_brl(spent)} / {format_brl(budget.limit)}")
        elif pct >= 80:
            alerts.append(f"⚠️ {budget.category.emoji} {budget.category.name}: {pct:.0f}% - {format_brl(spent)} / {format_brl(budget.limit)}")
        else:
            alerts.append(f"✅ {budget.category.emoji} {budget.category.name}: {pct:.0f}% - {format_brl(spent)} / {format_brl(budget.limit)}")

    if alerts:
        response += f"\n\n📈 *Limites:*\n" + "\n".join(alerts)
    return response
