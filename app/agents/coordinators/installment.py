"""Coordinator de parcelas — extrai dados de compras parceladas."""

from app.agents.orchestrator import call_llm

PROMPT = """Você extrai dados de compras parceladas de mensagens em português.
Retorne APENAS um JSON com os campos:
- "description": descrição do item comprado (string)
- "category": categoria do gasto (string, lowercase)
- "installments": número de parcelas (integer)
- "installment_amount": valor de cada parcela (float)

Categorias válidas: alimentação, transporte, lazer, saúde, educação, moradia, assinaturas, outros.
Se a categoria não estiver na lista, mapeie para a mais próxima.

Exemplos:
"comprei um celular, 12 parcelas de 100" → {"description": "celular", "category": "outros", "installments": 12, "installment_amount": 100.0}
"parcelei uma tv em 10x de 200" → {"description": "tv", "category": "lazer", "installments": 10, "installment_amount": 200.0}
"comprei um sofá em 6 vezes de 150 reais" → {"description": "sofá", "category": "moradia", "installments": 6, "installment_amount": 150.0}
"notebook 24x 250" → {"description": "notebook", "category": "outros", "installments": 24, "installment_amount": 250.0}
"geladeira parcelada 8x de 400" → {"description": "geladeira", "category": "moradia", "installments": 8, "installment_amount": 400.0}"""


def extract(message: str) -> dict:
    return call_llm(PROMPT, message)
