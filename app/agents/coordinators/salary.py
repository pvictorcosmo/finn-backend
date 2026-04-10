"""Coordinator de salário — extrai o valor do salário."""

from app.agents.orchestrator import call_llm

PROMPT = """Você extrai o valor do salário de mensagens em português.
Retorne APENAS um JSON com o campo:
- "amount": valor numérico do salário (float)

Exemplos:
"meu salário é 5000" → {"amount": 5000.0}
"ganho 3500 por mês" → {"amount": 3500.0}
"recebo 8000 reais" → {"amount": 8000.0}"""


def extract(message: str) -> dict:
    return call_llm(PROMPT, message)
