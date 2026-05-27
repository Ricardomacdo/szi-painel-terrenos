"""
Cliente para o Nekt MCP Server - Seazone
Autentica via JWT e executa queries SQL via MCP protocol.
"""
import json
import warnings
from functools import lru_cache
import requests

warnings.filterwarnings("ignore")

NEKT_URL = "https://nekt-app-mcp.seazone.com.br/mcp"

def _load_jwt() -> str:
    """Carrega o JWT do arquivo secrets ou variável de ambiente."""
    import os
    # 1. Variável de ambiente
    token = os.environ.get("NEKT_JWT_TOKEN")
    if token:
        return token
    # 2. Arquivo .nekt_secrets
    secrets_path = os.path.join(os.path.dirname(__file__), ".nekt_secrets")
    if os.path.exists(secrets_path):
        with open(secrets_path) as f:
            data = json.load(f)
            return data.get("jwt_token", "")
    # 3. Streamlit secrets (vários formatos aceitos)
    try:
        import streamlit as st
        # Formato simples: NEKT_JWT_TOKEN = "..."
        if "NEKT_JWT_TOKEN" in st.secrets:
            return str(st.secrets["NEKT_JWT_TOKEN"])
        # Formato com seção: [nekt] / jwt_token = "..."
        if "nekt" in st.secrets:
            return str(st.secrets["nekt"]["jwt_token"])
        # Formato plano: jwt_token = "..."
        if "jwt_token" in st.secrets:
            return str(st.secrets["jwt_token"])
    except Exception:
        pass
    return ""

def init_session(jwt: str) -> str:
    """Inicializa sessão MCP e retorna session_id."""
    r = requests.post(
        NEKT_URL,
        json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "szi-painel-terrenos", "version": "1.0"}
            }
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/json, text/event-stream"
        },
        timeout=20,
        verify=False
    )
    r.raise_for_status()
    # Force UTF-8 decoding
    _ = r.content.decode("utf-8", errors="replace")
    return r.headers.get("mcp-session-id", "")

def execute_sql(sql: str, jwt: str, session_id: str) -> list[dict]:
    """Executa SQL via Nekt MCP e retorna lista de dicts."""
    r = requests.post(
        NEKT_URL,
        json={
            "jsonrpc": "2.0", "id": 2,
            "method": "tools/call",
            "params": {"name": "execute_sql", "arguments": {"sql_query": sql}}
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id
        },
        timeout=120,
        verify=False
    )
    r.raise_for_status()
    # Decodifica explicitamente como UTF-8 para evitar Mojibake (latin-1 padrão)
    raw_text = r.content.decode("utf-8", errors="replace")
    for line in raw_text.split("\n"):
        if line.startswith("data:"):
            data = json.loads(line[5:].strip())
            result = data.get("result", {}).get("content", [{}])[0].get("text", "{}")
            parsed = json.loads(result)
            if "error" in parsed:
                raise ValueError(f"SQL error: {parsed['error']}")
            cols = parsed.get("columns", [])
            rows = parsed.get("data", [])
            return [dict(zip(cols, row)) for row in rows]
    return []

def get_painel_data() -> list[dict]:
    """
    Busca todos os cards ativos do funil SZI Terrenos.
    Retorna lista de dicts prontos para o painel.
    """
    jwt = _load_jwt()
    if not jwt:
        raise ValueError("JWT token não configurado. Configure NEKT_JWT_TOKEN ou .nekt_secrets")

    session_id = init_session(jwt)

    ETAPAS_VALIDAS = (
        "'Não Iniciado','Falta Informação','Sem Zoneamento',"
        "'Triagem de terrenos','Análise Preliminar',"
        "'Fila de EM','EM Iniciado','EM Análise de ROI',"
        "'EM Relatório de Proposta','Pré Proposta','EM Finalizado',"
        "'Fila de Análise Private','Análise Private Finalizada',"
        "'Fila de EP','EP Iniciado','EP Orçamento Prévio',"
        "'EP Revisão de ROI','Revisão Análise Private','EP Finalizado'"
    )

    SQL = f"""
    SELECT
        ids,
        id_do_card,
        status,
        etapa,
        etapa_de_projeto,
        etapa_de_proposta,
        etapa_de_private,
        estado,
        cidade,
        bairro,
        endereco,
        CAST(area_total_m_ AS DOUBLE) AS area_total_m2,
        valor,
        canal,
        temperatura_da_negociacao,
        executivo_de_canais                  AS analista,
        parceiro,
        contato_do_parceiro,
        CAST(COALESCE(NULLIF(score_do_terreno,''), '0') AS INTEGER)  AS score_total,
        CAST(COALESCE(NULLIF(score_320,''), '0') AS INTEGER)          AS score_320,
        CAST(COALESCE(NULLIF(score_de_localizacao,''), '0') AS INTEGER) AS score_micro,
        triagem_inicial,
        vgv_ap,
        roi_ap,
        ticket_medio_ap,
        vgv_roi_em,
        _roi_em                               AS roi_em,
        ticket_ideal,
        motivo_de_perda,
        descricao_da_perda,
        resultado,
        link_da_pasta_do_terreno,
        data_de_insercao_do_terreno           AS data_insercao,
        criado_em,
        atualizado_em,
        data_de_entrada_triagem,
        data_de_entrada_em_analise_preliminar,
        data_de_entrada_em_fila_de_em,
        data_de_entrada_em_em_iniciado,
        data_de_entrada_em_em_analise_de_roi,
        data_de_entrada_em_em_finalizado,
        data_de_entrada_em_fila_de_ep,
        data_de_entrada_em_ep_iniciado,
        data_de_entrada_em_ep_finalizado,
        data_de_entrada_em_proposta,
        data_de_entrada_em_primeira_proposta,
        data_de_entrada_em_negociacao,
        data_de_mudanca_de_status_para_ganho,
        data_de_mudanca_de_status_para_viavel,
        data_de_mudanca_de_status_para_inviavel
    FROM nekt_operacional_silver.pipefy_szi_all_cards_transformada_bd_terreno
    WHERE etapa IN ({ETAPAS_VALIDAS})
      AND (executivo_de_canais IS NULL
           OR LENGTH(executivo_de_canais) < 60)
    ORDER BY atualizado_em DESC
    """
    return execute_sql(SQL, jwt, session_id)

def test_connection() -> tuple[bool, str]:
    """Testa a conexão com o Nekt. Retorna (ok, mensagem)."""
    try:
        jwt = _load_jwt()
        if not jwt:
            return False, "JWT não configurado"
        sid = init_session(jwt)
        if not sid:
            return False, "Sessão não iniciada"
        return True, f"Conectado (session: {sid[:8]}...)"
    except Exception as e:
        return False, str(e)
