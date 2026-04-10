"""Coordinator de consultas — extrai period e category."""

from app.agents.orchestrator import call_llm

PROMPT = """Você interpreta consultas financeiras em português.
Retorne APENAS um JSON com os campos:
- "period": "month", "week" ou "today"
- "category": nome da categoria ou null (para todas)

Exemplos:
"quanto gastei esse mês" → {"period": "month", "category": null}
"gastos da semana em alimentação" → {"period": "week", "category": "alimentação"}
"gastos de hoje" → {"period": "today", "category": null}

Se não especificar período, use "month". Se não especificar categoria, use null."""


def extract(message: str) -> dict:
    result = call_llm(PROMPT, message, model="llama-3.1-8b-instant")
    return {
        "period": result.get("period", "month"),
        "category": result.get("category"),
    }
