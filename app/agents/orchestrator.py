"""
Orchestrator — ponto de entrada do sistema de agentes.

Recebe a mensagem do usuário, classifica a intenção e despacha
para o coordinator (agente especializado) correto.
"""

import json
from groq import Groq
from sqlalchemy.orm import Session

from app.core.config import settings
from app.routers.actions import (
    add_expense,
    query_spending,
    set_budget,
    list_categories,
    list_transactions,
    delete_last,
    help_message,
    set_salary_action,
    query_goals_action,
    add_installment_action,
    list_installments_action,
    add_recurring_action,
    list_recurring_action,
    remove_recurring_action,
)

client = Groq(api_key=settings.groq_api_key)

ROUTER_PROMPT = """Você é um agente roteador. Classifique a intenção do usuário.

Retorne APENAS um JSON com o campo "intent". Os intents possíveis são:

- "add_expense" — registrar um gasto único (gastei, paguei)
- "add_installment" — compra parcelada (comprei X em N parcelas de Y, parcelei, Nx de Y)
- "add_recurring" — gasto fixo mensal (pago X de aluguel por mês, minha internet é X, gasto X todo mês de Y)
- "query_spending" — consultar gastos (quanto gastei, meus gastos, resumo)
- "set_budget" — definir limite mensal (limite de X para Y)
- "set_salary" — definir salário (meu salário é X, ganho X, recebo X)
- "query_goals" — consultar metas/progresso 50-30-20 (minhas metas, como estão minhas metas, progresso)
- "list_categories" — ver categorias
- "list_transactions" — ver transações recentes (minhas transações, últimas)
- "list_installments" — ver parcelas ativas (minhas parcelas, parcelas)
- "list_recurring" — ver gastos fixos mensais (meus gastos fixos, contas do mês)
- "remove_recurring" — remover gasto fixo (cancelar aluguel, remover netflix)
- "delete_last" — apagar última transação (apagar, desfazer, remover)
- "help" — não se encaixa em nenhum dos acima"""


def call_llm(system_prompt: str, message: str, model: str = "llama-3.3-70b-versatile") -> dict:
    """Chama a LLM com um system prompt e retorna JSON."""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0,
            max_tokens=256,
            response_format={"type": "json_object"},
        )
        return json.loads(completion.choices[0].message.content or "{}")
    except Exception as e:
        print(f"Erro na LLM: {e}")
        return {}


def _classify_intent(message: str) -> str:
    """Classifica a intenção usando modelo leve e rápido."""
    result = call_llm(ROUTER_PROMPT, message, model="llama-3.1-8b-instant")
    return result.get("intent", "help")


def process_message(message: str, db: Session) -> dict:
    """Orquestra: classifica intenção → despacha para coordinator → retorna resposta."""
    from app.agents.coordinators import expense, query, budget

    intent = _classify_intent(message)
    print(f"🤖 Intent: {intent}")

    match intent:
        case "add_expense":
            data = expense.extract(message)
            if not data.get("amount"):
                return {"intent": intent, "response": help_message()}
            response = add_expense(db, data["amount"], data["category"], data["description"])

        case "query_spending":
            data = query.extract(message)
            response = query_spending(db, data["period"], data.get("category"))

        case "set_budget":
            data = budget.extract(message)
            if not data.get("limit"):
                return {"intent": intent, "response": help_message()}
            response = set_budget(db, data["category"], data["limit"])

        case "list_categories":
            response = list_categories(db)

        case "list_transactions":
            data = query.extract(message)
            response = list_transactions(db, data["period"], data.get("category"), 10)

        case "add_recurring":
            from app.agents.coordinators import recurring as recurring_coord
            data = recurring_coord.extract(message)
            if not data.get("amount"):
                return {"intent": intent, "response": "Nao entendi. Tente: 'pago 1000 de aluguel por mes'"}
            response = add_recurring_action(db, data["description"], data["category"], data["amount"])

        case "list_recurring":
            response = list_recurring_action(db)

        case "remove_recurring":
            from app.agents.coordinators import recurring as recurring_coord
            data = recurring_coord.extract(message)
            response = remove_recurring_action(db, data.get("description", ""))

        case "add_installment":
            from app.agents.coordinators import installment as installment_coord
            data = installment_coord.extract(message)
            if not data.get("installments") or not data.get("installment_amount"):
                return {"intent": intent, "response": "❌ Não entendi a parcela. Tente: 'comprei celular, 12 parcelas de 100'"}
            response = add_installment_action(
                db, data["description"], data["category"],
                data["installments"], data["installment_amount"],
            )

        case "list_installments":
            response = list_installments_action(db)

        case "set_salary":
            from app.agents.coordinators import salary as salary_coord
            data = salary_coord.extract(message)
            if not data.get("amount"):
                return {"intent": intent, "response": "❌ Não entendi o valor do salário. Tente: 'meu salário é 5000'"}
            response = set_salary_action(db, data["amount"])

        case "query_goals":
            response = query_goals_action(db)

        case "delete_last":
            response = delete_last(db)

        case _:
            response = help_message()

    return {"intent": intent, "response": response}
