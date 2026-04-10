"""Coordinator de gastos fixos — extrai dados de despesas recorrentes mensais."""

from app.agents.orchestrator import call_llm

PROMPT = """Você extrai dados de gastos fixos mensais de mensagens em português.
Retorne APENAS um JSON com os campos:
- "description": descrição do gasto fixo (string)
- "category": categoria do gasto (string, lowercase)
- "amount": valor mensal (float)

Categorias válidas: alimentação, transporte, lazer, saúde, educação, moradia, assinaturas, outros.
Se a categoria não estiver na lista, mapeie para a mais próxima.

Exemplos:
"pago 1000 de aluguel por mês" → {"description": "aluguel", "category": "moradia", "amount": 1000.0}
"minha internet é 120 por mês" → {"description": "internet", "category": "assinaturas", "amount": 120.0}
"gasto 500 de mercado todo mês" → {"description": "mercado", "category": "alimentação", "amount": 500.0}
"academia 90 reais mensais" → {"description": "academia", "category": "saúde", "amount": 90.0}
"netflix 55 por mês" → {"description": "netflix", "category": "assinaturas", "amount": 55.0}
"condomínio 400" → {"description": "condomínio", "category": "moradia", "amount": 400.0}"""


def extract(message: str) -> dict:
    return call_llm(PROMPT, message)
