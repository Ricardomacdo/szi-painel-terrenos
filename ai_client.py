"""
Cliente Claude para o Painel SZI Terrenos.
Fornece assistente de IA para análise de terrenos.
"""
import anthropic
from datetime import datetime

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
    """Retorna cliente Anthropic configurado."""
    import streamlit as st
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY não configurado nos secrets")
    return anthropic.Anthropic(api_key=api_key)


def ask_claude(message: str, history: list = None) -> str:
    """
    Envia mensagem para Claude e retorna resposta.

    Args:
        message: Mensagem do usuário
        history: Lista de mensagens anteriores [{"role": "user"/"assistant", "content": "..."}]

    Returns:
        Resposta do Claude como string
    """
    client = get_client()

    # Monta lista de mensagens
    messages = history.copy() if history else []
    messages.append({"role": "user", "content": message})

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages
    )

    return response.content[0].text


def ask_about_terreno(terreno_info: str, pergunta: str = None) -> str:
    """
    Analisa um terreno específico com contexto.
    Args:
        terreno_info: Descrição do terreno (localização, área, preço)
        pergunta: Pergunta específica (opcional)

    Returns:
        Análise do Claude
    """
    prompt = f"""Analise este terreno:

{terreno_info}

{f"Pergunta: {pergunta}" if pergunta else "O que você observa sobre este terreno?"}"""

    return ask_claude(prompt)
