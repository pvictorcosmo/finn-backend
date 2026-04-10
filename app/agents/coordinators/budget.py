"""Coordinator de orçamento — extrai category e limit."""

from app.agents.orchestrator import call_llm

PROMPT = """Você extrai dados de limites de orçamento de mensagens em português.
Retorne APENAS um JSON com os campos:
- "category": categoria (string, lowercase)
- "limit": valor do limite (float)

Categorias válidas: alimentação, transporte, lazer, saúde, educação, moradia, assinaturas, outros.

Exemplos:
"limite de 500 reais para alimentação" → {"category": "alimentação", "limit": 500.0}
"definir 1000 reais de transporte" → {"category": "transporte", "limit": 1000.0}"""


def extract(message: str) -> dict:
    return call_llm(PROMPT, message)
