"""Coordinator de gastos — extrai amount, category e description."""

from app.agents.orchestrator import call_llm

PROMPT = """Você extrai dados de gastos de mensagens em português.
Retorne APENAS um JSON com os campos:
- "amount": valor numérico (float)
- "category": categoria do gasto (string, lowercase)
- "description": descrição curta (string)

Categorias válidas: alimentação, transporte, lazer, saúde, educação, moradia, assinaturas, outros.
Se a categoria não estiver na lista, mapeie para a mais próxima.

Exemplos:
"gastei 50 no ifood" → {"amount": 50.0, "category": "alimentação", "description": "ifood"}
"paguei 30 de uber" → {"amount": 30.0, "category": "transporte", "description": "uber"}
"200 reais de conta de luz" → {"amount": 200.0, "category": "moradia", "description": "conta de luz"}"""


def extract(message: str) -> dict:
    return call_llm(PROMPT, message)
