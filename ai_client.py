"""
Cliente IA para o Painel SZI Terrenos.
Usa o gateway Seazone (hub.seazone.dev) com modelo minimax-m2.7.
"""
import anthropic
from datetime import datetime

ANTHROPIC_BASE_URL = "https://hub.seazone.dev"
AI_MODEL = "minimax-m2.7"

SYSTEM_PROMPT = """
Você é assistente do Ricardo, Analista de Prospecção de Terrenos da Seazone Investimentos.

SEU FLUXO DE TRABALHO:
1. Receber terreno do corretor (WhatsApp)
2. Analisar: localização, valor, metragem
3. Cadastrar no Pipefy
4. Acompanhar andamento

O QUE VERIFICAR EM CADA TERRENO:
- Localização: está dentro do polígono de interesse da Seazone?
- Valor: preço compatível com a região? (cota terreno ≤ ticket cap)
- Metragem: área suficiente para o projeto?
- Score: ≥320 = qualificado
- Gate AP: interesse da região + micro-score

MICRORREGIÕES COM SCORE ALTO:
- Jurerê Internacional (10), Centro BC (10) → Interesse 5
- Meia Praia Itapema (9), Bombinhas Centro (9) → Interesse 5
- Lagoa da Conceição (9), Jurerê (9) → Interesse 5

COMO AJUDAR:
- Avaliar se terreno vale prosseguir (localização + preço + área)
- Calcular se a cota cabe no ticket cap da região
- Sugerir perguntas pro corretor (zoneamento, documentação)
- Redigir mensagem pro corretor (pedir mais info / agradecer)
- Identificar terrenos promising no funil
- Resumo rápido de um terreno específico

IDIOMA: Português brasileiro, direto e prático.
"""

def get_client():
    """Retorna cliente configurado para o gateway Seazone."""
    import os, httpx
    # 1. Streamlit secrets
    try:
        import streamlit as st
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        base_url = st.secrets.get("ANTHROPIC_BASE_URL", ANTHROPIC_BASE_URL)
    except Exception:
        api_key = ""
        base_url = ANTHROPIC_BASE_URL
    # 2. Variável de ambiente
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY não configurado nos secrets")
    # SSL desativado (gateway Seazone usa certificado auto-assinado)
    http_client = httpx.Client(verify=False)
    return anthropic.Anthropic(api_key=api_key, base_url=base_url, http_client=http_client)


def ask_claude(message: str, history: list = None) -> str:
    """
    Envia mensagem para a IA e retorna resposta.

    Args:
        message: Mensagem do usuário
        history: Lista de mensagens anteriores [{"role": "user"/"assistant", "content": "..."}]

    Returns:
        Resposta como string
    """
    client = get_client()

    messages = history.copy() if history else []
    messages.append({"role": "user", "content": message})

    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages
    )

    if response.content:
        return response.content[0].text
    return "Sem resposta do modelo."


def ask_about_terreno(terreno_info: str, pergunta: str = None) -> str:
    """
    Analisa um terreno específico com contexto.

    Args:
        terreno_info: Descrição do terreno (localização, área, preço)
        pergunta: Pergunta específica (opcional)

    Returns:
        Análise como string
    """
    prompt = f"""Analise este terreno:

{terreno_info}

{f"Pergunta: {pergunta}" if pergunta else "O que você observa sobre este terreno?"}"""

    return ask_claude(prompt)
