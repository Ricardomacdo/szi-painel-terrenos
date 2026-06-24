import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import random
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SZI | Monitoramento de Terrenos",
    layout="wide",
    page_icon="🏢",
)

# ── CSS BOTÃO FLUTUANTE ────────────────────────────────────────────────────────
st.markdown("""
<style>
.stFloatingChatButton {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 999;
}
.css-1vbk1k5 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 50%;
    width: 60px;
    height: 60px;
    font-size: 24px;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.css-1vbk1k5:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}
</style>
""", unsafe_allow_html=True)

PIPEFY_PIPE_ID   = "304543320"
PIPEDRIVE_DOMAIN = "seazone-fd92b9"
PIPEDRIVE_PIPE   = 45
SCORE_MINIMO     = 320
ROI_BENCHMARK    = 12.0  # % a.a.

# 22 etapas reais
FASES_FUNIL = [
    "Não Iniciado", "Falta Informação", "Sem Zoneamento",
    "Triagem de terrenos", "Análise Preliminar",
    "Fila de EM", "EM Iniciado", "EM Análise de ROI",
    "EM Relatório de Proposta", "Pré Proposta", "EM Finalizado",
    "Fila de Análise Private", "Análise Private Finalizada",
    "Fila de EP", "EP Iniciado", "EP Orçamento Prévio",
    "EP Revisão de ROI", "Revisão Análise Private", "EP Finalizado",
    "Perdido", "Ganho", "Excluídos",
]
FASES_SEQUENCIAIS = FASES_FUNIL[:19]
FASES_SAIDA       = {"Perdido", "Ganho", "Excluídos"}

REGIOES = {
    "Florianópolis": {
        "Jurerê Internacional":   {"micro_score": 10, "interesse": 5, "ticket_cap": 80_000},
        "Jurerê":                 {"micro_score": 9,  "interesse": 5, "ticket_cap": 75_000},
        "Canasvieiras":           {"micro_score": 8,  "interesse": 5, "ticket_cap": 70_000},
        "Ingleses":               {"micro_score": 8,  "interesse": 4, "ticket_cap": 65_000},
        "Santinho":               {"micro_score": 7,  "interesse": 4, "ticket_cap": 60_000},
        "Ponta das Canas":        {"micro_score": 7,  "interesse": 3, "ticket_cap": 55_000},
        "Cachoeira do Bom Jesus": {"micro_score": 6,  "interesse": 3, "ticket_cap": 55_000},
        "Campeche":               {"micro_score": 8,  "interesse": 5, "ticket_cap": 70_000},
        "Lagoa da Conceição":     {"micro_score": 9,  "interesse": 5, "ticket_cap": 75_000},
        "Barra da Lagoa":         {"micro_score": 8,  "interesse": 4, "ticket_cap": 65_000},
        "Rio Vermelho":           {"micro_score": 7,  "interesse": 4, "ticket_cap": 60_000},
        "Trindade":               {"micro_score": 6,  "interesse": 3, "ticket_cap": 55_000},
        "Itacorubi":              {"micro_score": 6,  "interesse": 3, "ticket_cap": 55_000},
        "João Paulo":             {"micro_score": 7,  "interesse": 4, "ticket_cap": 60_000},
        "Córrego Grande":         {"micro_score": 6,  "interesse": 3, "ticket_cap": 55_000},
        "Centro":                 {"micro_score": 7,  "interesse": 4, "ticket_cap": 65_000},
        "Coqueiros":              {"micro_score": 7,  "interesse": 4, "ticket_cap": 65_000},
        "Estreito":               {"micro_score": 6,  "interesse": 3, "ticket_cap": 60_000},
        "Capoeiras":              {"micro_score": 5,  "interesse": 2, "ticket_cap": 50_000},
    },
    "São José": {
        "Kobrasol":  {"micro_score": 6, "interesse": 3, "ticket_cap": 55_000},
        "Barreiros": {"micro_score": 5, "interesse": 2, "ticket_cap": 50_000},
        "Campinas":  {"micro_score": 5, "interesse": 2, "ticket_cap": 50_000},
        "Roçado":    {"micro_score": 5, "interesse": 2, "ticket_cap": 50_000},
    },
    "Palhoça": {
        "Pedra Branca": {"micro_score": 7, "interesse": 4, "ticket_cap": 60_000},
        "Passa Vinte":  {"micro_score": 5, "interesse": 2, "ticket_cap": 50_000},
        "Aririú":       {"micro_score": 4, "interesse": 2, "ticket_cap": 45_000},
    },
    "Biguaçu": {
        "Centro Biguaçu": {"micro_score": 4, "interesse": 2, "ticket_cap": 45_000},
        "Prado":          {"micro_score": 4, "interesse": 1, "ticket_cap": 40_000},
    },
    "Governador Celso Ramos": {
        "Armação":    {"micro_score": 8, "interesse": 4, "ticket_cap": 65_000},
        "Ganchos":    {"micro_score": 7, "interesse": 3, "ticket_cap": 60_000},
        "Praia Seca": {"micro_score": 6, "interesse": 3, "ticket_cap": 55_000},
    },
    "Bombinhas": {
        "Bombas":           {"micro_score": 8, "interesse": 4, "ticket_cap": 65_000},
        "Bombinhas Centro": {"micro_score": 9, "interesse": 5, "ticket_cap": 70_000},
    },
    "Porto Belo": {
        "Centro Porto Belo": {"micro_score": 7, "interesse": 3, "ticket_cap": 60_000},
        "Perequê":           {"micro_score": 6, "interesse": 3, "ticket_cap": 55_000},
    },
    "Itapema": {
        "Meia Praia":     {"micro_score": 9, "interesse": 5, "ticket_cap": 75_000},
        "Centro Itapema": {"micro_score": 8, "interesse": 4, "ticket_cap": 65_000},
    },
    "Balneário Camboriú": {
        "Centro BC": {"micro_score": 10, "interesse": 5, "ticket_cap": 90_000},
        "Nações":    {"micro_score": 8,  "interesse": 4, "ticket_cap": 70_000},
        "Ariribá":   {"micro_score": 7,  "interesse": 3, "ticket_cap": 60_000},
    },
}

# Equipe real
ANALISTAS_PROSP  = ["Ricardo", "Gabriel"]
ANALISTAS_AP     = ["Emanuelle Stephany", "Júlia Guzzo", "Thais Lee Cleaver"]
ANALISTA_PRIVATE = "Maria Luiza Gonzales"
COORD_ANALISE    = "Maria Santos Guimarães"
ANALISTAS        = ANALISTAS_PROSP

CORRETORES = [
    "João Silva", "Maria Oliveira", "Pedro Santos", "Ana Costa",
    "Carlos Lima", "Fernanda Rocha", "Bruno Alves", "Juliana Melo",
    "Rafael Souza", "Patrícia Nunes", "Diego Ferreira", "Camila Torres",
    "Marcelo Vieira", "Larissa Dias", "Thiago Barbosa", "Vanessa Cunha",
    "Lucas Moreira", "Beatriz Lopes", "Rodrigo Pires", "Amanda Carvalho",
]
TIPOLOGIAS  = ["R1", "PP4", "R8", "R16"]
ZONEAMENTOS = ["ARP", "ARP-0", "AVL", "AMC", "ACI", "ARE", "ARM", "ARP-E"]
EP_TIPOS    = ["In-house", "Terceirizado"]

# ── GATE AP ───────────────────────────────────────────────────────────────────
def check_gate_ap(interesse: int, micro_score: int):
    """Retorna (passa: bool, motivo: str) pelas regras reais de gate AP."""
    if interesse == 5:
        return True, "Interesse 5 → qualquer micro passa"
    elif interesse == 4:
        if micro_score >= 7:
            return True,  f"Interesse 4 + Micro {micro_score} ≥ 7 → passa"
        else:
            return False, f"Interesse 4 + Micro {micro_score} < 7 → Backup"
    elif interesse == 3:
        if micro_score >= 8:
            return True,  f"Interesse 3 + Micro {micro_score} ≥ 8 → passa"
        else:
            return False, f"Interesse 3 + Micro {micro_score} < 8 → Backup"
    elif interesse in (1, 2):
        if micro_score == 10:
            return True,  f"Interesse {interesse} + Micro 10 → auto-passa"
        elif micro_score >= 8:
            return True,  f"Interesse {interesse} + Micro {micro_score} ≥ 8 → condicional"
        else:
            return False, f"Interesse {interesse} + Micro {micro_score} < 8 → não passa"
    return False, "Dados insuficientes"

# ── SEMÁFORO DE TEMPO ─────────────────────────────────────────────────────────
def semaforo_dias(d):
    if pd.isna(d):
        return "—"
    d = int(d)
    if d < 7:
        return f"🟢 {d}d"
    elif d < 15:
        return f"🟡 {d}d"
    else:
        return f"🔴 {d}d"

# ── TOKENS ────────────────────────────────────────────────────────────────────
def _secret(key: str) -> str:
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""

# ── PIPEFY API ────────────────────────────────────────────────────────────────
PIPEFY_QUERY = """
query Cards($pipeId: ID!, $after: String) {
  allCards(pipeId: $pipeId, first: 50, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        id title done
        current_phase { name }
        created_at updated_at
        fields { name value }
      }
    }
  }
}
"""

def _field(fields, *keys):
    for k in keys:
        for fk, fv in fields.items():
            if k.lower() in fk.lower() and fv:
                try:
                    return float(str(fv).replace("R$","").replace(".","").replace(",",".").strip())
                except (ValueError, TypeError):
                    return fv
    return None

def _field_str(fields, *keys):
    for k in keys:
        for fk, fv in fields.items():
            if k.lower() in fk.lower() and fv:
                return str(fv).strip()
    return None

@st.cache_data(ttl=0, show_spinner="Buscando dados do Pipefy…")
def fetch_pipefy(token: str) -> pd.DataFrame:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    rows, cursor, has_next = [], None, True
    while has_next:
        variables = {"pipeId": PIPEFY_PIPE_ID}
        if cursor:
            variables["after"] = cursor
        resp = requests.post("https://app.pipefy.com/queries",
                             json={"query": PIPEFY_QUERY, "variables": variables},
                             headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", {}).get("allCards", {})
        for edge in data.get("edges", []):
            node   = edge["node"]
            fields = {f["name"]: f["value"] for f in node.get("fields", [])}
            phase  = node.get("current_phase", {}).get("name", "")
            status = ("Ganho"   if node.get("done") else
                      "Perdido" if phase == "Perdido" else
                      "Excluído" if phase == "Excluídos" else "Aberto")
            id_seq  = _field_str(fields, "id terreno", "código", "cod.", "número", "num.")
            card_id = f"{int(id_seq):04d}" if id_seq and str(id_seq).isdigit() else node["id"]
            rows.append({
                "id": card_id, "terreno": node["title"],
                "fase_atual": phase, "status": status,
                "data_entrada": node.get("created_at","")[:10],
                "data_fase":    node.get("updated_at","")[:10],
                "score":    _field(fields,"score","land score","pontuação"),
                "preco":    _field(fields,"preço","valor","price"),
                "area_m2":  _field(fields,"área","area","m²"),
                "cota_terreno": _field(fields,"cota"),
                "roi_est":  _field(fields,"roi"),
                "interesse": _field(fields,"interesse"),
                "cidade":      _field_str(fields,"cidade","city","município"),
                "microrregiao":_field_str(fields,"micro","região","region"),
                "analista":    _field_str(fields,"analista","responsável","owner"),
                "corretor":    _field_str(fields,"corretor","broker","canal"),
                "matricula":   _field_str(fields,"matrícula","matricula"),
                "zoneamento":  _field_str(fields,"zoneamento","zone"),
                "to":   _field(fields,"taxa de ocupação","t.o","to "),
                "ia":   _field(fields,"índice de aproveitamento","i.a","ia "),
                "tipologia": _field_str(fields,"tipologia","tipo"),
                "andares":   _field(fields,"andares","pavimentos","floors"),
            })
        page_info = data.get("pageInfo", {})
        has_next  = page_info.get("hasNextPage", False)
        cursor    = page_info.get("endCursor")
    df = pd.DataFrame(rows)
    df["data_entrada"] = pd.to_datetime(df["data_entrada"], errors="coerce")
    df["data_fase"]    = pd.to_datetime(df["data_fase"],    errors="coerce")
    df["dias_na_fase"] = (datetime.today() - df["data_fase"]).dt.days
    return df

@st.cache_data(ttl=0, show_spinner="Buscando Pipedrive…")
def fetch_pipedrive(token: str) -> pd.DataFrame:
    url = f"https://{PIPEDRIVE_DOMAIN}.pipedrive.com/api/v1/deals"
    rows, start = [], 0
    while True:
        params = {"pipeline_id": PIPEDRIVE_PIPE, "status": "all_not_deleted",
                  "limit": 500, "start": start, "api_token": token}
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        for d in (body.get("data") or []):
            rows.append({"deal_id": d.get("id"), "terreno": d.get("title",""),
                         "status_pd": d.get("status",""),
                         "corretor": (d.get("person_id") or {}).get("name",""),
                         "valor_pd": d.get("value")})
        if not body.get("additional_data",{}).get("pagination",{}).get("more_items_in_collection"):
            break
        start += 500
    return pd.DataFrame(rows)

# ── DADOS NEKT ────────────────────────────────────────────────────────────────
def _parse_br_money(s) -> float | None:
    """Converte '7.100.000,00' → 7100000.0"""
    if not s or str(s).strip() in ("", "0,00", "0"):
        return None
    try:
        return float(str(s).replace("R$","").replace(" ","")
                     .replace(".","").replace(",",".").strip())
    except Exception:
        return None

def _temp_to_interesse(t) -> int | None:
    """Mapeia temperatura → interesse 1-5 (aproximado)."""
    return {"Quente": 4, "Morno": 3, "Frio": 2}.get(str(t).strip(), None)

@st.cache_data(ttl=0, show_spinner="Buscando dados do Nekt…")
def fetch_nekt_data() -> pd.DataFrame:
    """Carrega dados reais do Pipefy via Nekt MCP e normaliza para o painel."""
    from nekt_client import get_painel_data
    raw = get_painel_data()
    if not raw:
        return pd.DataFrame()

    import re

    ETAPAS_OK = {
        "Não Iniciado", "Falta Informação", "Sem Zoneamento",
        "Triagem de terrenos", "Análise Preliminar",
        "Fila de EM", "EM Iniciado", "EM Análise de ROI",
        "EM Relatório de Proposta", "Pré Proposta", "EM Finalizado",
        "Fila de Análise Private", "Análise Private Finalizada",
        "Fila de EP", "EP Iniciado", "EP Orçamento Prévio",
        "EP Revisão de ROI", "Revisão Análise Private", "EP Finalizado",
    }

    def _is_valid_name(s):
        """Retorna True se parece um nome de pessoa (não data/número)."""
        if not s:
            return False
        s = str(s).strip()
        if len(s) > 60 or len(s) < 3:
            return False
        # Rejeita datas (dd/mm/yyyy) e números
        if re.match(r'^\d', s):
            return False
        return True

    # Mapeamento de analistas → label de exibição
    ANALISTA_MAP = {
        "Ricardo Macedo":              "Farmer",
        "Gabriel Carlos Gouvea de Souza": "Key Account",
    }
    # Analistas a excluir completamente
    ANALISTAS_EXCLUIR = {"Davi Millan", "Eduardo Farias"}

    rows = []
    today = datetime.today()

    for r in raw:
        # Filtro de qualidade: ignora linhas com etapa inválida
        etapa_r = str(r.get("etapa", "")).strip()
        if etapa_r not in ETAPAS_OK:
            continue

        # Filtra analistas excluídos
        analista_raw = r.get("analista", "") or ""
        if analista_raw.strip() in ANALISTAS_EXCLUIR:
            continue
        # Identificação
        card_id = str(r.get("ids", r.get("id_do_card", "")))
        endereco = r.get("endereco", "") or ""
        bairro   = r.get("bairro",   "") or ""
        cidade_r = r.get("cidade",   "") or ""
        # Remove sufixo "Cidade, UF, Bairro" do campo bairro
        bairro_limpo = bairro.replace(cidade_r, "").strip().lstrip(",").strip()

        # Status e fase
        status_r   = r.get("status", "Aberto")

        # Scores
        score_320_v   = r.get("score_320")
        score_micro_v = r.get("score_micro")
        score_total_v = r.get("score_total")
        interesse_v   = _temp_to_interesse(r.get("temperatura_da_negociacao"))

        # Financeiro
        preco_v = _parse_br_money(r.get("valor"))
        roi_v_raw = r.get("roi_ap") or r.get("roi_em") or ""
        roi_v   = _parse_br_money(roi_v_raw)
        ticket_v = _parse_br_money(r.get("ticket_medio_ap"))

        # Área
        try:
            area_v = float(str(r.get("area_total_m2") or 0).replace(",", "."))
        except Exception:
            area_v = None

        # Datas
        def _parse_date(s):
            if not s:
                return None
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(str(s)[:len(fmt)], fmt)
                except Exception:
                    continue
            return None

        data_entrada_v = _parse_date(r.get("data_insercao") or r.get("criado_em"))
        atualizado_v   = _parse_date(r.get("atualizado_em"))
        data_fase_v    = atualizado_v  # proxy para data de entrada na fase atual
        dias_na_fase_v = (today - atualizado_v).days if atualizado_v else None

        rows.append({
            "id":          card_id,
            "terreno":     endereco[:60] if endereco else f"Terreno {card_id}",
            "cidade":      cidade_r.split(",")[0].strip() if cidade_r else "",
            "microrregiao": bairro_limpo or bairro,
            "estado":      r.get("estado", ""),
            "endereco":    endereco,
            "fase_atual":  etapa_r,
            "status":      status_r,
            "score":       score_320_v,
            "score_micro": score_micro_v,
            "score_total": score_total_v,
            "interesse":   interesse_v,
            "temperatura": r.get("temperatura_da_negociacao"),
            "preco":       preco_v,
            "area_m2":     area_v,
            "roi_est":     roi_v,
            "cota_terreno": ticket_v,
            "ticket_cap":  None,
            "analista":    ANALISTA_MAP.get(analista_raw.strip(), analista_raw if _is_valid_name(analista_raw) else ""),
            "analista_ap": None,
            "analista_em": None,
            "corretor":    r.get("parceiro", ""),
            "canal":       r.get("canal", ""),
            "tem_matricula": None,
            "zoneamento":  "",
            "tipologia":   "",
            "andares":     None,
            "to":          None,
            "ia":          None,
            "num_unidades": None,
            "triagem_inicial": r.get("triagem_inicial", ""),
            "link_pasta":  r.get("link_da_pasta_do_terreno", ""),
            "id_do_card":  str(r.get("id_do_card", "") or ""),
            "data_entrada": data_entrada_v,
            "data_fase":    data_fase_v,
            "dias_na_fase": dias_na_fase_v,
            "motivo_perda": r.get("motivo_de_perda", ""),
            # EM — Estudo de Massa
            "etapa_em":    str(r.get("etapa_de_projeto",  "") or ""),
            "roi_em_val":  _parse_br_money(r.get("roi_em")),
            # EP — Estudo Preliminar
            "etapa_ep":    str(r.get("etapa_de_proposta", "") or ""),
            # Private
            "etapa_private": str(r.get("etapa_de_private", "") or ""),
            "_ap": None, "_em": None, "_private": None, "_ep": None, "_docs": None,
        })

    df = pd.DataFrame(rows)
    df["id"] = df["id"].astype(str)
    return df

# ── DADOS DEMO ────────────────────────────────────────────────────────────────
@st.cache_data
def demo_data() -> pd.DataFrame:
    random.seed(42)
    dist = {
        "Não Iniciado": 8, "Falta Informação": 12, "Sem Zoneamento": 10,
        "Triagem de terrenos": 18, "Análise Preliminar": 28,
        "Fila de EM": 12, "EM Iniciado": 10, "EM Análise de ROI": 7,
        "EM Relatório de Proposta": 5, "Pré Proposta": 4, "EM Finalizado": 6,
        "Fila de Análise Private": 4, "Análise Private Finalizada": 3,
        "Fila de EP": 3, "EP Iniciado": 3, "EP Orçamento Prévio": 2,
        "EP Revisão de ROI": 2, "Revisão Análise Private": 1, "EP Finalizado": 2,
        "Perdido": 25, "Ganho": 6, "Excluídos": 4,
    }

    def _status(f):
        return ("Perdido" if f == "Perdido" else
                "Ganho"   if f == "Ganho"   else
                "Excluído" if f == "Excluídos" else "Aberto")

    regioes_flat = [(c, m, i) for c, ms in REGIOES.items() for m, i in ms.items()]
    fase_ordem   = {f: i for i, f in enumerate(FASES_FUNIL)}

    rows, idx = [], 1
    for fase, qtd in dist.items():
        for _ in range(qtd):
            cidade, micro, info = random.choice(regioes_flat)
            interesse   = info["interesse"]
            micro_score = info["micro_score"]
            ticket_cap  = info["ticket_cap"]
            fi          = fase_ordem.get(fase, 0)

            area_m2      = random.randint(400, 10_000)
            andares      = random.randint(4, 18)
            num_unidades = andares * random.randint(2, 6)
            preco        = random.randint(2_000_000, 40_000_000)
            cota_terreno = round(preco / num_unidades, 2)
            roi_est      = round(random.uniform(8, 22), 1)
            score        = random.randint(200, 480)
            to_val       = round(random.uniform(0.45, 0.70), 2)
            ia_val       = round(random.uniform(1.5, 4.0), 2)
            area_rem     = round(area_m2 * (1 - to_val), 1)
            tipologia    = random.choice(TIPOLOGIAS)
            zoneamento   = random.choice(ZONEAMENTOS)
            data_in      = datetime.today() - timedelta(days=random.randint(0, 180))
            tem_mat      = random.random() > 0.12

            # Data de entrada na fase atual (simulada)
            dias_acumulados = fi * random.randint(1, 5)
            data_fase = data_in + timedelta(days=dias_acumulados)
            if data_fase > datetime.today():
                data_fase = datetime.today() - timedelta(days=random.randint(0, 3))
            dias_na_fase = max(0, (datetime.today() - data_fase).days)

            ap_data = em_data = private_data = ep_data = None

            if fi >= fase_ordem.get("Análise Preliminar", 99):
                ap_data = {
                    "ap_data":       (data_in + timedelta(days=random.randint(1,5))).strftime("%d/%m/%Y"),
                    "ap_to":         f"{to_val:.0%}",
                    "ap_ia":         f"{ia_val:.2f}",
                    "ap_area_rem":   f"{area_rem:.0f} m²",
                    "ap_recuos":     f"Frontal {random.randint(3,6)}m / Lateral {random.randint(1,3)}m / Fundo {random.randint(2,4)}m",
                    "ap_ticket":     f"R$ {cota_terreno:,.0f}",
                    "ap_zoneamento": zoneamento,
                    "ap_tipologia":  tipologia,
                }

            if fi >= fase_ordem.get("EM Iniciado", 99):
                em_data = {
                    "em_data_inicio": (data_in + timedelta(days=random.randint(5,20))).strftime("%d/%m/%Y"),
                    "em_arquiteto":   random.choice(["Emanuelle S.", "Júlia G.", "Thais L."]),
                    "em_andares":     andares,
                    "em_unidades":    num_unidades,
                    "em_tipologia":   tipologia,
                    "em_area_util":   f"{area_m2 * ia_val:.0f} m²",
                    "em_cub_tipo":    tipologia,
                    "em_majoracao":   "1.85 (SC)",
                    "em_roi":         f"{roi_est:.1f}% a.a.",
                }

            if fi >= fase_ordem.get("Fila de Análise Private", 99):
                private_data = {
                    "priv_analista": "Maria Luiza Gonzales",
                    "priv_data":     (data_in + timedelta(days=random.randint(20,40))).strftime("%d/%m/%Y"),
                    "priv_status":   random.choice(["Aprovado", "Em análise", "Condicionado"]),
                    "priv_obs":      random.choice([
                        "Garantidores aprovaram VGV e estrutura",
                        "Aguardando complemento de documentação",
                        "Aprovado com condicionante de matrícula",
                    ]),
                }

            if fi >= fase_ordem.get("EP Iniciado", 99):
                ep_data = {
                    "ep_tipo":        random.choice(EP_TIPOS),
                    "ep_data_inicio": (data_in + timedelta(days=random.randint(40,60))).strftime("%d/%m/%Y"),
                    "ep_orcamento":   f"R$ {random.randint(50_000, 300_000):,.0f}",
                    "ep_prazo_dias":  random.randint(30, 60),
                    "ep_roi_rev":     f"{roi_est - random.uniform(0,2):.1f}% a.a.",
                    "ep_status":      random.choice(["Em andamento", "Aguardando revisão", "Finalizado"]),
                }

            analista_prosp = random.choice(ANALISTAS_PROSP)
            analista_ap    = random.choice(ANALISTAS_AP) if ap_data  else None
            analista_em    = random.choice(ANALISTAS_AP) if em_data  else None

            area_doc_v  = area_m2 + random.choice([-random.randint(1,50), 0, 0, 0, random.randint(1,30)])
            end_cadastro = f"{micro}, {cidade}"
            end_doc      = end_cadastro if random.random() > 0.15 else f"{random.choice(['Rua das Flores','Av. Central','Rua do Porto'])}, {cidade}"
            area_ok      = abs(area_doc_v - area_m2) <= 5
            end_ok       = end_doc == end_cadastro

            docs_data = {
                "matricula": {
                    "nome": "Matrícula do Imóvel", "anexado": tem_mat, "ok": tem_mat,
                    "divergencia": None if tem_mat else "Documento não anexado",
                },
                "iptu": {
                    "nome": "IPTU", "anexado": random.random() > 0.20,
                    "area_doc": area_doc_v, "area_cad": area_m2, "ok": area_ok,
                    "divergencia": None if area_ok else f"Área: documento={area_doc_v}m² ≠ cadastro={area_m2}m²",
                },
                "escritura": {
                    "nome": "Escritura / Contrato", "anexado": random.random() > 0.30,
                    "ok": True, "divergencia": None,
                },
                "certidao_area": {
                    "nome": "Certidão de Área", "anexado": random.random() > 0.35,
                    "area_doc": area_doc_v, "area_cad": area_m2, "ok": area_ok,
                    "divergencia": None if area_ok else f"Área: documento={area_doc_v}m² ≠ cadastro={area_m2}m²",
                },
                "localizacao": {
                    "nome": "Comprovante de Localização", "anexado": random.random() > 0.25,
                    "end_doc": end_doc, "end_cad": end_cadastro, "ok": end_ok,
                    "divergencia": None if end_ok else f"Localização: '{end_doc}' ≠ '{end_cadastro}'",
                },
                "foto": {
                    "nome": "Fotos do Terreno", "anexado": random.random() > 0.20,
                    "ok": True, "divergencia": None,
                },
                "zoneamento_doc": {
                    "nome": "Certidão de Zoneamento", "anexado": random.random() > 0.40,
                    "ok": True, "divergencia": None,
                },
                "certidao_onus": {
                    "nome": "Certidão de Ônus Reais", "anexado": random.random() > 0.45,
                    "ok": True, "divergencia": None,
                },
            }

            if ap_data:
                ap_data["ap_analista"] = analista_ap
            if em_data:
                em_data["em_analista"] = analista_em
            if private_data:
                private_data["priv_analista"] = ANALISTA_PRIVATE

            rows.append({
                "id": f"{idx:04d}", "terreno": f"Terreno {cidade[:3].upper()}-{idx:04d}",
                "cidade": cidade, "microrregiao": micro,
                "interesse": interesse, "score_micro": micro_score,
                "score": score, "fase_atual": fase, "status": _status(fase),
                "preco": preco, "area_m2": area_m2,
                "num_unidades": num_unidades, "cota_terreno": cota_terreno,
                "roi_est": roi_est, "ticket_cap": ticket_cap,
                "tem_matricula": tem_mat,
                "analista":    analista_prosp,
                "analista_ap": analista_ap,
                "analista_em": analista_em,
                "corretor": random.choice(CORRETORES),
                "zoneamento": zoneamento, "tipologia": tipologia,
                "andares": andares, "to": to_val, "ia": ia_val,
                "data_entrada": data_in,
                "data_fase":    data_fase,
                "dias_na_fase": dias_na_fase,
                "_ap": ap_data, "_em": em_data,
                "_private": private_data, "_ep": ep_data,
                "_docs": docs_data,
            })
            idx += 1

    df = pd.DataFrame(rows)
    df["id"] = df["id"].astype(str)
    return df

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔗 Fonte de Dados")
    fonte = st.radio("Fonte:", ["🛢️ Nekt (dados reais)", "🎲 Demonstração"], index=0)
    if fonte == "🛢️ Nekt (dados reais)":
        try:
            from nekt_client import test_connection
            ok, msg = test_connection()
            if ok:
                st.success(f"✅ Nekt conectado")
            else:
                st.error(f"❌ {msg}")
        except Exception as e:
            st.error(f"❌ Erro: {e}")
    st.divider()
    st.header("Filtros")

# ── CARREGAR DADOS ────────────────────────────────────────────────────────────
DEMO = False
df_pd_raw = pd.DataFrame()

if fonte == "🛢️ Nekt (dados reais)":
    try:
        df_raw = fetch_nekt_data()
        if df_raw.empty:
            st.warning("Nekt retornou dados vazios — exibindo demonstração.")
            df_raw = demo_data()
            DEMO = True
    except Exception as e:
        st.error(f"Erro ao conectar ao Nekt: {e}")
        df_raw = demo_data()
        DEMO = True
else:
    df_raw = demo_data()
    DEMO = True

# ── FILTRO FARMER ──────────────────────────────────────────────────────────────
# Exibe apenas terrenos do Farmer (Ricardo Macedo)
df_raw = df_raw[df_raw["analista"] == "Farmer"].copy()

# ── RENDER CARD (estilo Pipefy) ───────────────────────────────────────────────
def render_card(row):
    fase_atual  = row.get("fase_atual", "")
    status      = row.get("status", "")
    score_v     = row.get("score", None)
    interesse_v = row.get("interesse", None)
    micro_v     = row.get("score_micro", None)
    dias_v      = row.get("dias_na_fase", None)
    is_saida    = fase_atual in FASES_SAIDA
    cor_status  = {"Aberto":"🟢","Perdido":"🔴","Ganho":"🏆","Excluído":"⚫"}.get(status,"⚪")

    # ── Cabeçalho ──────────────────────────────────────────────────────────
    data_entrada_fmt = (pd.to_datetime(row.get("data_entrada")).strftime("%d/%m/%Y")
                        if pd.notna(row.get("data_entrada")) else "—")
    id_do_card = str(row.get("id_do_card", "") or "")
    pipefy_url = f"https://app.pipefy.com/pipes/{PIPEFY_PIPE_ID}#cards/{id_do_card}" if id_do_card else ""

    col_head, col_btn = st.columns([5, 1])
    with col_head:
        st.markdown(f"""
        <div style="background:#1e293b;border-radius:8px;padding:16px 20px;margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <span style="color:#94a3b8;font-size:13px">ID: {row['id']}</span>
                    <h2 style="color:#f1f5f9;margin:4px 0">{row['terreno']}</h2>
                    <span style="color:#94a3b8;font-size:13px">{row.get('cidade','')} · {row.get('microrregiao','')}</span>
                </div>
                <div style="text-align:right">
                    <div style="font-size:24px">{cor_status}</div>
                    <div style="color:#f1f5f9;font-weight:bold">{status}</div>
                    <div style="color:#94a3b8;font-size:13px">Entrada: {data_entrada_fmt}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_btn:
        if pipefy_url:
            st.link_button("🔗 Abrir no Pipefy", pipefy_url, width='stretch')

    # ── Blocos de destaque: Qualificação · Gate AP · Semáforo ──────────────
    is_qualif  = pd.notna(score_v) and float(score_v) >= SCORE_MINIMO
    qual_cor   = "#10b981" if is_qualif else "#ef4444"
    qual_txt   = "✅ QUALIFICADO" if is_qualif else "⚠️ ABAIXO DA RÉGUA"
    score_str  = str(int(float(score_v))) if pd.notna(score_v) else "—"
    diff_score = int(float(score_v)) - SCORE_MINIMO if pd.notna(score_v) else None
    diff_txt   = (f"{'+' if diff_score >= 0 else ''}{diff_score} vs mínimo {SCORE_MINIMO}"
                  if diff_score is not None else f"mínimo {SCORE_MINIMO}")

    gate_html = ""
    if pd.notna(interesse_v) and pd.notna(micro_v):
        passa, motivo = check_gate_ap(int(float(interesse_v)), int(float(micro_v)))
        gc = "#10b981" if passa else "#f59e0b"
        gt = "✅ PASSA NO GATE AP" if passa else "⚠️ VAI PARA BACKUP"
        gate_html = f"""
        <div style="flex:1;background:{gc}22;border:2px solid {gc};border-radius:6px;padding:10px 14px;text-align:center">
            <div style="color:{gc};font-size:15px;font-weight:bold">{gt}</div>
            <div style="color:#94a3b8;font-size:12px;margin-top:2px">{motivo}</div>
        </div>"""

    sem_html = ""
    if pd.notna(dias_v):
        d   = int(dias_v)
        sc  = "#10b981" if d < 7 else "#f59e0b" if d < 15 else "#ef4444"
        st_ = "🟢 Em dia" if d < 7 else "🟡 Atenção" if d < 15 else "🔴 Travado"
        sem_html = f"""
        <div style="flex:1;background:{sc}22;border:2px solid {sc};border-radius:6px;padding:10px 14px;text-align:center">
            <div style="color:{sc};font-size:15px;font-weight:bold">{st_}</div>
            <div style="color:#94a3b8;font-size:12px;margin-top:2px">{d} dias nesta fase</div>
        </div>"""

    st.markdown(f"""
    <div style="display:flex;gap:8px;margin-bottom:12px">
        <div style="flex:1;background:{qual_cor}22;border:2px solid {qual_cor};border-radius:6px;padding:10px 14px;text-align:center">
            <div style="color:{qual_cor};font-size:16px;font-weight:bold">{qual_txt}</div>
            <div style="color:#94a3b8;font-size:12px;margin-top:2px">Score: {score_str} · {diff_txt}</div>
        </div>
        {gate_html}
        {sem_html}
    </div>
    """, unsafe_allow_html=True)

    # ── Fase atual ─────────────────────────────────────────────────────────
    fc = {"Ganho":"#10b981","Perdido":"#ef4444","Excluídos":"#6b7280"}.get(fase_atual,"#0ea5e9")
    st.markdown(
        f"<div style='background:{fc}22;border-left:4px solid {fc};padding:8px 12px;"
        f"border-radius:4px;margin-bottom:12px'>"
        f"<b style='color:{fc}'>📍 Fase Atual:</b> <span style='color:#f1f5f9'>{fase_atual}</span></div>",
        unsafe_allow_html=True)

    # ── Progresso no funil ─────────────────────────────────────────────────
    if not is_saida and fase_atual in FASES_SEQUENCIAIS:
        idx_atual = FASES_SEQUENCIAIS.index(fase_atual)
        cols_p    = st.columns(len(FASES_SEQUENCIAIS))
        for i, f in enumerate(FASES_SEQUENCIAIS):
            with cols_p[i]:
                if i < idx_atual:
                    st.markdown(f"<div style='text-align:center;font-size:9px;color:#10b981'>✅<br>{f}</div>", unsafe_allow_html=True)
                elif i == idx_atual:
                    st.markdown(f"<div style='text-align:center;font-size:9px;font-weight:bold;color:#0ea5e9;border:1px solid #0ea5e9;border-radius:4px;padding:2px'>🔄<br>{f}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:center;font-size:9px;color:#475569'>⬜<br>{f}</div>", unsafe_allow_html=True)
        st.markdown("")

    st.markdown("---")

    # ── Localização · Classificação · Área · Financeiro ────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("**📍 Localização**")
    col1.write(f"Cidade: **{row.get('cidade','—')}**")
    col1.write(f"Microrregião: **{row.get('microrregiao','—')}**")
    col1.write(f"Zoneamento: **{row.get('zoneamento','—')}**")

    col2.markdown("**🎯 Classificação**")
    col2.write(f"Score: **{score_str}** {'✅' if is_qualif else '⚠️'}")
    col2.write(f"Interesse: **{row.get('interesse','—')}/5**")
    col2.write(f"Score Micro: **{row.get('score_micro','—')}/10**")
    col2.write(f"Tipologia: **{row.get('tipologia','—')}**")

    col3.markdown("**📐 Área e Projeto**")
    col3.write(f"Área: **{row.get('area_m2',0):,.0f} m²**")
    col3.write(f"Andares: **{row.get('andares','—')}**")
    col3.write(f"Unidades: **{row.get('num_unidades','—')}**")
    col3.write(f"TO: **{row.get('to',0):.0%}**" if pd.notna(row.get("to")) else "TO: —")
    col3.write(f"IA: **{row.get('ia',0):.2f}**" if pd.notna(row.get("ia")) else "IA: —")

    col4.markdown("**💰 Financeiro**")
    col4.write(f"Preço: **R$ {row.get('preco',0):,.0f}**" if pd.notna(row.get("preco")) else "Preço: —")
    col4.write(f"Cota: **R$ {row.get('cota_terreno',0):,.0f}**" if pd.notna(row.get("cota_terreno")) else "Cota: —")
    roi_v = row.get("roi_est")
    roi_ic = "🟢" if pd.notna(roi_v) and roi_v >= ROI_BENCHMARK else "🔴"
    col4.write(f"ROI: {roi_ic} **{roi_v:.1f}% a.a.**" if pd.notna(roi_v) else "ROI: —")
    col4.write(f"Matrícula: {'✅' if row.get('tem_matricula') else '❌'}")

    st.markdown("---")

    # ── Equipe ─────────────────────────────────────────────────────────────
    st.markdown("**👥 Equipe Responsável**")
    eq1, eq2, eq3, eq4 = st.columns(4)
    eq1.metric("Executivo de Canais", row.get("analista","—"))
    eq2.metric("Corretor",             row.get("corretor","—"))
    eq3.metric("Responsável AP",       row.get("analista_ap","—") or "—")
    eq4.metric("Responsável EM",       row.get("analista_em","—") or "—")

    # ── Documentos ─────────────────────────────────────────────────────────
    docs = row.get("_docs")
    if docs:
        st.markdown("---")
        st.markdown("**📁 Documentos**")
        d_cols = st.columns(4)
        for i, (_, doc) in enumerate(docs.items()):
            with d_cols[i % 4]:
                if not doc.get("anexado"):
                    st.markdown(f"❌ ~~{doc['nome']}~~")
                elif not doc.get("ok"):
                    st.markdown(f"⚠️ **{doc['nome']}**")
                    st.caption(doc.get("divergencia",""))
                else:
                    st.markdown(f"✅ {doc['nome']}")

        if "iptu" in docs and docs["iptu"].get("anexado"):
            ac = docs["iptu"]["area_cad"]; ad = docs["iptu"]["area_doc"]
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Área Cadastrada",   f"{ac} m²")
            mc2.metric("Área no Documento", f"{ad} m²")
            mc3.metric("Diferença", f"{abs(ad-ac)} m²",
                       delta_color="inverse" if abs(ad-ac) > 5 else "off")

        if "localizacao" in docs and docs["localizacao"].get("anexado"):
            lc1, lc2 = st.columns(2)
            lc1.metric("Localização Cadastrada",   docs["localizacao"]["end_cad"])
            lc2.metric("Localização no Documento", docs["localizacao"]["end_doc"])
            if not docs["localizacao"]["ok"]:
                st.error("⚠️ Divergência de localização detectada!")

    # ── AP ──────────────────────────────────────────────────────────────────
    ap = row.get("_ap")
    if ap:
        st.markdown("---")
        st.markdown(f"**📐 Análise Preliminar (AP)** — {ap.get('ap_analista','—')} · {ap.get('ap_data','—')}")
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Zoneamento",        ap.get("ap_zoneamento","—"))
        a1.metric("Tipologia",         ap.get("ap_tipologia","—"))
        a2.metric("TO",                ap.get("ap_to","—"))
        a2.metric("IA",                ap.get("ap_ia","—"))
        a3.metric("Área Remanescente", ap.get("ap_area_rem","—"))
        a3.metric("Recuos",            ap.get("ap_recuos","—"))
        a4.metric("Ticket (Cota)",     ap.get("ap_ticket","—"))

    # ── EM ──────────────────────────────────────────────────────────────────
    em = row.get("_em")
    if em:
        st.markdown("---")
        st.markdown(f"**🏗️ Estudo de Massa (EM)** — {em.get('em_analista','—')} · {em.get('em_data_inicio','—')}")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Arquiteto",     em.get("em_arquiteto","—"))
        e1.metric("Andares",       em.get("em_andares","—"))
        e2.metric("Unidades",      em.get("em_unidades","—"))
        e2.metric("Área Útil",     em.get("em_area_util","—"))
        e3.metric("Tipologia CUB", em.get("em_cub_tipo","—"))
        e3.metric("Majoração",     em.get("em_majoracao","—"))
        e4.metric("ROI (EM)",      em.get("em_roi","—"))

    # ── Análise Private ─────────────────────────────────────────────────────
    priv = row.get("_private")
    if priv:
        st.markdown("---")
        st.markdown(f"**🔐 Análise Private** — {priv.get('priv_analista','—')} · {priv.get('priv_data','—')}")
        p1, p2, p3 = st.columns(3)
        p1.metric("Status Private", priv.get("priv_status","—"))
        p2.metric("Analista",       priv.get("priv_analista","—"))
        p3.metric("Data",           priv.get("priv_data","—"))
        st.info(f"📝 {priv.get('priv_obs','')}")

    # ── EP ──────────────────────────────────────────────────────────────────
    ep = row.get("_ep")
    if ep:
        st.markdown("---")
        st.markdown(f"**📑 Estudo Preliminar (EP)** — {ep.get('ep_tipo','—')} · {ep.get('ep_data_inicio','—')}")
        ep1, ep2, ep3, ep4 = st.columns(4)
        ep1.metric("Tipo EP",      ep.get("ep_tipo","—"))
        ep2.metric("Orçamento",    ep.get("ep_orcamento","—"))
        ep3.metric("ROI Revisado", ep.get("ep_roi_rev","—"))
        ep4.metric("Status",       ep.get("ep_status","—"))


# ── CABEÇALHO ─────────────────────────────────────────────────────────────────
st.title("🏢 SZI | Monitoramento de Terrenos")
fonte_label = "Nekt (dados reais)" if not DEMO else "Demonstração"
st.caption(f"Fonte: {fonte_label} · Pipe {PIPEFY_PIPE_ID}  —  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
if DEMO:
    st.info("Modo demonstração — selecione 'Nekt (dados reais)' na barra lateral para ver os dados reais.", icon="ℹ️")

# ── ABAS ──────────────────────────────────────────────────────────────────────
tab_dash, tab_analistas, tab_ficha, tab_alertas, tab_matricula, tab_pesquisa = st.tabs([
    "📊 Dashboard", "👤 Executivo de Canais", "🔍 Ficha do Terreno", "⚠️ Alertas", "📋 Validar Matrícula", "📞 Pesquisa Corretores"
])

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    with st.sidebar:
        status_sel = st.multiselect("Status:",
            options=df_raw["status"].dropna().unique().tolist(),
            default=df_raw["status"].dropna().unique().tolist())
        cidade_sel = st.multiselect("Cidade:",
            options=sorted(df_raw["cidade"].dropna().unique().tolist()),
            default=sorted(df_raw["cidade"].dropna().unique().tolist()))
        analista_sel = st.multiselect("Executivo de Canais:",
            options=sorted(df_raw["analista"].dropna().unique().tolist()),
            default=sorted(df_raw["analista"].dropna().unique().tolist()))
        fase_sel = st.multiselect("Fase:",
            options=FASES_FUNIL,
            default=[f for f in FASES_FUNIL if f in df_raw["fase_atual"].values])
        st.divider()
        score_vals    = pd.to_numeric(df_raw["score"], errors="coerce").dropna()
        score_min_raw = int(score_vals.min()) if not score_vals.empty else 0
        score_max_raw = int(score_vals.max()) if not score_vals.empty else 500
        score_range   = st.slider("Faixa de Score:",
            min_value=score_min_raw, max_value=score_max_raw,
            value=(score_min_raw, score_max_raw), step=10)

    score_num_raw = pd.to_numeric(df_raw["score"], errors="coerce")
    mask = (df_raw["status"].isin(status_sel)
            & df_raw["fase_atual"].isin(fase_sel)
            & df_raw["cidade"].isin(cidade_sel)
            & df_raw["analista"].isin(analista_sel)
            & ((score_num_raw >= score_range[0]) | score_num_raw.isna())
            & ((score_num_raw <= score_range[1]) | score_num_raw.isna()))
    df = df_raw[mask].copy()

    score_num = pd.to_numeric(df["score"], errors="coerce")
    dias_num  = pd.to_numeric(df.get("dias_na_fase", pd.Series(dtype=float)), errors="coerce") if "dias_na_fase" in df.columns else pd.Series(dtype=float)

    total         = len(df)
    qualificados  = int((score_num >= SCORE_MINIMO).sum())
    falta_info    = int((df["fase_atual"] == "Falta Informação").sum())
    backups       = int(((score_num < SCORE_MINIMO) & (df["status"] == "Aberto")).sum())
    sem_matricula = int((~df["tem_matricula"].fillna(False).astype(bool)).sum()) if "tem_matricula" in df.columns and not df["tem_matricula"].isna().all() else 0
    travados      = int((dias_num >= 15).sum()) if not dias_num.empty else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("No Funil",                  total)
    c2.metric(f"Qualificados (≥{SCORE_MINIMO})", qualificados)
    c3.metric("Falta Informação",          falta_info,    delta_color="inverse")
    c4.metric("Backup",                    backups)
    c5.metric("Sem Matrícula",             sem_matricula, delta_color="inverse")
    c6.metric("🔴 Travados (≥15d)",        travados,      delta_color="inverse")

    # ── INSIGHTS DE IA ────────────────────────────────────────────────────────
    with st.expander("🤖 Análise IA do Funil", expanded=True):
        if st.button("Gerar análise", key="btn_insights"):
            try:
                from ai_client import ask_claude

                # --- dados de contexto ---
                travados_nomes = df[dias_num >= 15][["id","terreno","fase_atual","dias_na_fase"]].to_dict("records") if not dias_num.empty else []

                # campos faltantes por terreno em Falta Informação
                CAMPOS_VERIFICAR = {
                    "preco":              "Valor/Preço",
                    "area_m2":            "Área (m²)",
                    "dimensao_terreno":   "Dimensões",
                    "pasta_documentos":   "Pasta de documentos",
                    "triagem_inicial":    "Triagem inicial",
                }
                fi_rows = df[df["fase_atual"] == "Falta Informação"]
                falta_info_detalhado = []
                for _, r in fi_rows.iterrows():
                    faltando = [label for col, label in CAMPOS_VERIFICAR.items()
                                if not r.get(col) or str(r.get(col,"")).strip() in ("","None","nan","0","0.0")]
                    falta_info_detalhado.append({
                        "id": r.get("id",""),
                        "terreno": r.get("terreno",""),
                        "cidade": r.get("cidade",""),
                        "corretor": r.get("corretor",""),
                        "campos_faltantes": faltando,
                    })

                # terrenos com score alto ainda parados na triagem
                oportunidades = df[
                    (pd.to_numeric(df["score"], errors="coerce") >= SCORE_MINIMO) &
                    (df["fase_atual"].isin(["Não Iniciado","Triagem de terrenos","Análise Preliminar"]))
                ][["id","terreno","cidade","score","fase_atual","dias_na_fase"]].to_dict("records")

                contexto = f"""Você é o copiloto do Ricardo, Analista de Prospecção de Terrenos da Seazone Investimentos.

=== ESTADO DO FUNIL (hoje) ===
- Total no funil: {total} terrenos
- Qualificados (score ≥{SCORE_MINIMO}): {qualificados}
- Backup (abaixo da régua): {backups}
- Sem matrícula: {sem_matricula}

=== TRAVADOS (≥15 dias sem movimentação) ===
{travados_nomes if travados_nomes else "Nenhum terreno travado."}

=== FALTA INFORMAÇÃO — CAMPOS ESPECÍFICOS FALTANDO ===
{falta_info_detalhado if falta_info_detalhado else "Nenhum terreno com informação faltante."}

=== OPORTUNIDADES — score alto ainda na triagem ===
{oportunidades if oportunidades else "Nenhuma oportunidade identificada."}

=== TAREFA ===
Monte um PLANO DO DIA para o Ricardo em 4 seções:

**1. 🚨 Ações urgentes** — o que fazer primeiro (travados + falta info)
**2. 📋 Mensagens para corretores** — para cada terreno em Falta Informação, escreva uma mensagem direta no WhatsApp pedindo exatamente os campos que faltam (use o nome do terreno/cidade)
**3. 🚀 Oportunidades do dia** — terrenos qualificados que podem avançar no funil hoje
**4. 📊 Saúde do funil** — avaliação geral em 3 linhas + 1 recomendação estratégica

Seja direto, prático e use dados concretos. Português brasileiro."""

                with st.spinner("Montando plano do dia..."):
                    analise = ask_claude(contexto)
                st.markdown(analise)
            except Exception as e:
                st.error(f"Configure ANTHROPIC_API_KEY nos secrets do Streamlit Cloud. Erro: {e}")

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📊 Funil — 22 etapas")
        if not df.empty:
            fc = (df["fase_atual"].value_counts()
                  .reindex(FASES_FUNIL, fill_value=0).reset_index())
            fc.columns = ["Fase", "Qtd"]
            fc = fc[fc["Qtd"] > 0]
            fig1 = px.bar(fc, x="Fase", y="Qtd", text="Qtd",
                          color_discrete_sequence=["#0ea5e9"])
            fig1.update_layout(xaxis_tickangle=-45, height=400, margin=dict(b=140))
            st.plotly_chart(fig1, width='stretch')

    with col_b:
        st.subheader("🎯 Score — régua ≥ 320")
        sdf = df[score_num.notna()].copy()
        sdf["score"] = pd.to_numeric(sdf["score"])
        if not sdf.empty:
            fig2 = px.histogram(sdf, x="score", nbins=30,
                                color_discrete_sequence=["#6366f1"])
            fig2.add_vline(x=SCORE_MINIMO, line_dash="dash", line_color="red",
                           annotation_text=f"Mínimo ({SCORE_MINIMO})",
                           annotation_position="top right")
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, width='stretch')

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("🗺️ Cidade / Microrregião")
        if not df.empty:
            mc = (df.groupby(["cidade","microrregiao"]).size()
                  .reset_index(name="Total")
                  .sort_values("Total", ascending=False).head(20))
            fig3 = px.bar(mc, x="microrregiao", y="Total", color="cidade",
                          text="Total", barmode="stack")
            fig3.update_layout(xaxis_tickangle=-45, height=400, margin=dict(b=130))
            st.plotly_chart(fig3, width='stretch')

    with col_d:
        st.subheader("👤 Executivo de Canais")
        if not df.empty:
            ac = df.groupby("analista").agg(Terrenos=("terreno","count")).reset_index()
            ac_disp = ac.rename(columns={"analista": "Executivo de Canais"})
            fig4 = px.bar(ac_disp, x="Executivo de Canais", y="Terrenos", text="Terrenos",
                          color="Executivo de Canais",
                          color_discrete_sequence=["#0ea5e9","#10b981"])
            fig4.update_layout(showlegend=False, height=400, xaxis_title="")
            st.plotly_chart(fig4, width='stretch')

    st.markdown("---")
    st.subheader("📋 Todos os Terrenos")

    # ── Filtros da tabela ──────────────────────────────────────────────────
    exec_canais_opcoes = sorted([a for a in df["analista"].dropna().unique() if a])
    filtro_exec = st.radio(
        "Executivo de Canais:",
        options=["Todos"] + exec_canais_opcoes,
        horizontal=True,
        key="filtro_exec_todos",
    )

    f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
    with f1:
        fases_disponiveis = [f for f in FASES_FUNIL if f in df["fase_atual"].values]
        filtro_fase = st.selectbox(
            "Fase",
            options=["Todas"] + fases_disponiveis,
            key="filtro_fase_todos",
        )
    with f2:
        filtro_status = st.selectbox(
            "Status",
            options=["Todos", "Aberto", "Fechado"],
            key="filtro_status_todos",
        )
    with f3:
        cidade_opcoes = sorted([c for c in df["cidade"].dropna().unique() if c])
        filtro_cidade = st.selectbox(
            "Cidade",
            options=["Todas"] + cidade_opcoes,
            key="filtro_cidade_todos",
        )
    with f4:
        busca_id = st.text_input(
            "🔎 Buscar por ID",
            placeholder="Ex: 7463",
            key="busca_id_todos",
        )

    # Aplica filtros
    df_tabela = df.copy()
    if filtro_exec != "Todos":
        df_tabela = df_tabela[df_tabela["analista"] == filtro_exec]
    if filtro_fase != "Todas":
        df_tabela = df_tabela[df_tabela["fase_atual"] == filtro_fase]
    if filtro_status == "Aberto":
        df_tabela = df_tabela[df_tabela["status"] == "Aberto"]
    elif filtro_status == "Fechado":
        df_tabela = df_tabela[df_tabela["status"].isin(["Ganho", "Perdido", "Excluído", "Excluídos"])]
    if filtro_cidade != "Todas":
        df_tabela = df_tabela[df_tabela["cidade"] == filtro_cidade]
    if busca_id.strip():
        df_tabela = df_tabela[df_tabela["id"].astype(str).str.contains(busca_id.strip(), case=False, na=False)]

    st.caption(f"{len(df_tabela)} terreno(s) encontrado(s)")

    # Inclui id_do_card para usar no link (separado do id de exibição)
    cols_show = [c for c in [
        "id_do_card","id","terreno","cidade","microrregiao","fase_atual","status",
        "score","dias_na_fase",
        "etapa_em",
        "etapa_ep",
        "data_entrada",
    ] if c in df_tabela.columns]

    df_disp = df_tabela[cols_show].copy().reset_index(drop=True)

    # Coluna de link para o Pipefy (separada do ID numérico)
    def _build_url(row):
        card_id = str(row.get("id_do_card", "") or "").strip()
        if not card_id or card_id == "nan":
            card_id = str(row.get("id", "") or "").strip()
        if card_id and card_id != "nan":
            return f"https://app.pipefy.com/pipes/{PIPEFY_PIPE_ID}#cards/{card_id}"
        return ""
    df_disp["id_do_card"] = df_tabela.reset_index(drop=True).apply(_build_url, axis=1)

    if "roi_em_val" in df_disp:
        df_disp["roi_em_val"] = pd.to_numeric(df_disp["roi_em_val"], errors="coerce").apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) and x > 0 else "—")
    if "data_entrada" in df_disp:
        df_disp["data_entrada"] = pd.to_datetime(
            df_disp["data_entrada"], errors="coerce").dt.strftime("%d/%m/%Y")
    if "dias_na_fase" in df_disp:
        df_disp["dias_na_fase"] = df_disp["dias_na_fase"].apply(semaforo_dias)
    for col_etapa in ("etapa_em", "etapa_ep"):
        if col_etapa in df_disp.columns:
            df_disp[col_etapa] = df_disp[col_etapa].fillna("—").astype(str)
            df_disp.loc[df_disp[col_etapa] == "", col_etapa] = "—"

    df_disp.rename(columns={
        "id":"ID","id_do_card":"🔗",
        "terreno":"Terreno","cidade":"Cidade","microrregiao":"Microrregião",
        "fase_atual":"Fase","status":"Status","score":"Score",
        "dias_na_fase":"⏱ Dias na Fase",
        "etapa_em":"Etapa EM","roi_em_val":"ROI EM",
        "etapa_ep":"Etapa EP",
        "data_entrada":"Entrada",
    }, inplace=True)

    st.dataframe(
        df_disp,
        width='stretch',
        hide_index=True,
        column_config={
            "ID": st.column_config.TextColumn("ID"),
            "🔗": st.column_config.LinkColumn(
                "🔗",
                help="Abre o card no Pipefy",
                display_text="Abrir ↗",
            ),
        },
    )

    # Botão de download
    col_dl1, col_dl2 = st.columns([6, 1])
    with col_dl2:
        csv_bytes = df_tabela[cols_show].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar CSV",
            data=csv_bytes,
            file_name=f"terrenos_szi_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — POR ANALISTA
# ══════════════════════════════════════════════════════════════════════════════
with tab_analistas:
    st.subheader("👤 Terrenos por Executivo de Canais")

    for analista in sorted(df_raw["analista"].dropna().unique().tolist()):
        df_an    = df_raw[df_raw["analista"] == analista].copy()
        score_an = pd.to_numeric(df_an["score"], errors="coerce")
        dias_an  = pd.to_numeric(df_an.get("dias_na_fase", pd.Series(dtype=float)), errors="coerce") if "dias_na_fase" in df_an.columns else pd.Series(dtype=float)

        total_an    = len(df_an)
        ativos_an   = int((df_an["status"] == "Aberto").sum())
        qualif_an   = int((score_an >= SCORE_MINIMO).sum())
        ganhos_an   = int((df_an["status"] == "Ganho").sum())
        perdidos_an = int((df_an["status"] == "Perdido").sum())
        travados_an = int((dias_an >= 15).sum()) if not dias_an.empty else 0

        st.markdown("---")
        st.markdown(f"### 🧑‍💼 {analista}")

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Terrenos",              total_an)
        m2.metric("Ativos no Funil",             ativos_an)
        m3.metric(f"Qualificados (≥{SCORE_MINIMO})", qualif_an)
        m4.metric("Ganhos",                      ganhos_an)
        m5.metric("Perdidos",                    perdidos_an)
        m6.metric("🔴 Travados (≥15d)",          travados_an, delta_color="inverse")

        # ── ANÁLISE IA POR EXECUTIVO ──────────────────────────────────────────
        if st.button(f"🤖 Analisar carteira de {analista}", key=f"btn_ia_{analista}"):
            try:
                from ai_client import ask_claude
                fases_an = df_an["fase_atual"].value_counts().to_dict()
                travados_lista = df_an[dias_an >= 15][["id","terreno","fase_atual"]].to_dict("records") if not dias_an.empty else []
                contexto_an = f"""Carteira do executivo {analista}:
- Total: {total_an} terrenos | Ativos: {ativos_an} | Qualificados (≥{SCORE_MINIMO}): {qualif_an}
- Ganhos: {ganhos_an} | Perdidos: {perdidos_an}
- Travados (≥15 dias): {travados_an} → {travados_lista}
- Distribuição por fase: {fases_an}

Faça uma análise da carteira deste executivo: como está o desempenho? Quais terrenos merecem atenção imediata? Qual a recomendação de próximos passos?"""
                with st.spinner(f"Analisando carteira de {analista}..."):
                    analise_an = ask_claude(contexto_an)
                st.markdown(analise_an)
            except Exception as e:
                st.error(f"Erro na análise IA: {e}")

        col_esq, col_dir = st.columns([1, 2])

        with col_esq:
            st.markdown("**Distribuição por Fase**")
            fc_an = (df_an["fase_atual"].value_counts()
                     .reindex(FASES_FUNIL, fill_value=0).reset_index())
            fc_an.columns = ["Fase", "Qtd"]
            fc_an = fc_an[fc_an["Qtd"] > 0]
            fig_an = px.bar(fc_an, x="Qtd", y="Fase", orientation="h",
                            text="Qtd", color_discrete_sequence=["#0ea5e9"],
                            height=400)
            fig_an.update_layout(
                yaxis={"categoryorder": "array", "categoryarray": FASES_FUNIL[::-1]},
                margin=dict(l=160))
            st.plotly_chart(fig_an, width='stretch')

        with col_dir:
            st.markdown("**Todos os Terrenos Indicados** — clique no ID para abrir no Pipefy")
            cols_an = [c for c in [
                "id_do_card","id","terreno","cidade","microrregiao","fase_atual","status",
                "score","dias_na_fase","corretor","data_entrada",
            ] if c in df_an.columns]
            df_an_disp = df_an[cols_an].copy().reset_index(drop=True)

            # Coluna de link para o Pipefy
            def _build_url_an(row):
                card_id = str(row.get("id_do_card", "") or "").strip()
                if not card_id or card_id == "nan":
                    card_id = str(row.get("id", "") or "").strip()
                if card_id and card_id != "nan":
                    return f"https://app.pipefy.com/pipes/{PIPEFY_PIPE_ID}#cards/{card_id}"
                return ""
            df_an_disp["id_do_card"] = df_an.reset_index(drop=True).apply(_build_url_an, axis=1)

            if "data_entrada" in df_an_disp:
                df_an_disp["data_entrada"] = pd.to_datetime(
                    df_an_disp["data_entrada"], errors="coerce").dt.strftime("%d/%m/%Y")
            if "dias_na_fase" in df_an_disp:
                df_an_disp["dias_na_fase"] = df_an_disp["dias_na_fase"].apply(semaforo_dias)

            def _cst(s):
                return {"Aberto":"🟢","Ganho":"🏆","Perdido":"🔴","Excluído":"⚫"}.get(s,"⚪")
            df_an_disp["status"] = df_an_disp["status"].apply(lambda s: f"{_cst(s)} {s}")

            df_an_disp.rename(columns={
                "id":"ID","id_do_card":"🔗",
                "terreno":"Terreno","cidade":"Cidade",
                "microrregiao":"Microrregião","fase_atual":"Fase Atual",
                "status":"Status","score":"Score","dias_na_fase":"⏱ Dias",
                "corretor":"Corretor","data_entrada":"Entrada",
            }, inplace=True)

            st.dataframe(
                df_an_disp,
                width='stretch',
                hide_index=True,
                key=f"sel_{analista}",
                column_config={
                    "ID": st.column_config.TextColumn("ID"),
                    "🔗": st.column_config.LinkColumn(
                        "🔗",
                        help="Abre o card no Pipefy",
                        display_text="Abrir ↗",
                    ),
                },
            )

# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — FICHA DO TERRENO
# ══════════════════════════════════════════════════════════════════════════════
with tab_ficha:
    st.subheader("🔍 Busca de Terreno")
    col_busca, col_tipo = st.columns([3, 1])
    with col_tipo:
        tipo_busca = st.radio("Buscar por:", ["ID", "Nome"], horizontal=True)
    with col_busca:
        termo = st.text_input("", placeholder="Ex: 0042 (ID) ou nome do terreno")

    if not termo:
        st.info("Digite o ID ou nome do terreno acima para ver a ficha completa.")
    else:
        if tipo_busca == "ID":
            resultado = df_raw[df_raw["id"].str.upper() == termo.strip().upper()]
        else:
            resultado = df_raw[df_raw["terreno"].str.contains(termo.strip(), case=False, na=False)]

        if resultado.empty:
            st.warning(f"Nenhum terreno encontrado para '{termo}'.")
        else:
            if len(resultado) > 1:
                opcoes = resultado["id"].tolist()
                sel_id = st.selectbox("Mais de um resultado — selecione:", opcoes)
                row = resultado[resultado["id"] == sel_id].iloc[0]
            else:
                row = resultado.iloc[0]

            st.markdown("---")
            render_card(row)
            st.markdown("---")
            st.caption(f"Entrada: {pd.to_datetime(row.get('data_entrada')).strftime('%d/%m/%Y') if pd.notna(row.get('data_entrada')) else '—'}")

            # ── ANÁLISE IA DO TERRENO ──────────────────────────────────────
            st.markdown("---")
            st.subheader("🤖 Análise IA")

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("Analisar este terreno com IA", key="btn_analise_terreno"):
                    try:
                        from ai_client import ask_about_terreno
                        info = f"""Terreno: {row.get('terreno','—')} (ID: {row.get('id','—')})
Localização: {row.get('cidade','—')} · {row.get('microrregiao','—')} · Zoneamento: {row.get('zoneamento','—')}
Score: {row.get('score','—')} (mínimo: {SCORE_MINIMO}) · Interesse: {row.get('interesse','—')}/5 · Score Micro: {row.get('score_micro','—')}/10
Área: {row.get('area_m2','—')} m² · Preço: R$ {row.get('preco',0):,.0f}
Cota terreno: R$ {row.get('cota_terreno',0):,.0f} · ROI estimado: {row.get('roi_est','—')}% a.a.
Fase atual: {row.get('fase_atual','—')} · Dias na fase: {row.get('dias_na_fase','—')}
Executivo de Canais: {row.get('analista','—')} · Corretor: {row.get('corretor','—')}
Matrícula: {'Sim' if row.get('tem_matricula') else 'Não'}"""
                        with st.spinner("Analisando terreno..."):
                            analise = ask_about_terreno(info, "Avalie este terreno: vale prosseguir? Quais são os pontos fortes, riscos e próximos passos recomendados?")
                        st.markdown(analise)
                    except Exception as e:
                        st.error(f"Configure ANTHROPIC_API_KEY nos secrets do Streamlit Cloud. Erro: {e}")

            with col_btn2:
                if st.button("📎 Ler documentos do Pipefy", key="btn_ler_docs"):
                    card_id_ficha = str(row.get("id_do_card", "") or "").strip()
                    if not card_id_ficha:
                        st.warning("ID do card Pipefy não disponível para este terreno.")
                    else:
                        with st.spinner("Buscando e lendo anexos no Pipefy..."):
                            try:
                                from pipefy_client import get_card_attachments_text
                                from ai_client import ask_claude
                                texto_docs = get_card_attachments_text(card_id_ficha)
                                st.markdown(texto_docs)

                                # Se extraiu conteúdo real, passa para IA analisar
                                if "PDF" in texto_docs or "texto" in texto_docs:
                                    info_terreno = f"""Terreno: {row.get('terreno','—')} (ID: {row.get('id','—')})
Localização: {row.get('cidade','—')} · {row.get('microrregiao','—')}
Score: {row.get('score','—')} · Área: {row.get('area_m2','—')} m² · Preço: R$ {row.get('preco',0):,.0f}
Fase: {row.get('fase_atual','—')}

DOCUMENTOS ANEXADOS:
{texto_docs}"""
                                    st.markdown("---")
                                    st.markdown("**🤖 Análise IA dos documentos:**")
                                    with st.spinner("Analisando documentos..."):
                                        analise_docs = ask_claude(
                                            f"{info_terreno}\n\nCom base nos documentos acima, o que você observa? "
                                            f"Há alguma inconsistência entre os dados cadastrados e os documentos? "
                                            f"Pontos de atenção?"
                                        )
                                    st.markdown(analise_docs)
                            except Exception as e:
                                st.error(f"Erro ao ler documentos: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# ABA 4 — ALERTAS
# ══════════════════════════════════════════════════════════════════════════════
with tab_alertas:
    st.subheader("⚠️ Alertas Ativos")

    # Filtro rápido por executivo de canais
    alerta_analista = st.selectbox(
        "Filtrar por Executivo de Canais:",
        options=["Todos"] + sorted(df_raw["analista"].dropna().unique().tolist()),
        index=0,
    )

    df_ativo = df_raw[df_raw["status"] == "Aberto"].copy()
    if alerta_analista != "Todos":
        df_ativo = df_ativo[df_ativo["analista"] == alerta_analista]

    score_a = pd.to_numeric(df_ativo["score"],        errors="coerce")
    cota_a  = pd.to_numeric(df_ativo["cota_terreno"], errors="coerce")
    cap_a   = pd.to_numeric(df_ativo["ticket_cap"],   errors="coerce")
    dias_a  = pd.to_numeric(df_ativo.get("dias_na_fase", pd.Series(dtype=float)), errors="coerce") if "dias_na_fase" in df_ativo.columns else pd.Series(dtype=float)
    alertas = False

    # 🔴 Travados ≥ 15 dias
    if not dias_a.empty:
        travados_df = df_ativo[dias_a >= 15]
        for _, r in travados_df.iterrows():
            st.error(
                f"🔴 **Travado — {r['id']} | {r['terreno']}** · "
                f"{int(r.get('dias_na_fase',0))} dias em '{r.get('fase_atual','')}' · "
                f"Executivo de Canais: {r.get('analista','')} · Parceiro: {r.get('corretor','')}"
            )
            alertas = True

    # Falta Informação — mostra ID, campos faltantes e status do Polígono
    fi_df = df_ativo[df_ativo["fase_atual"] == "Falta Informação"]
    if not fi_df.empty:
        st.markdown("### ℹ️ Falta Informação")

        # Busca status do Polígono direto do Pipefy
        pipefy_docs = {}
        try:
            from pipefy_client import get_docs_by_card_ids
            card_ids = fi_df["id_do_card"].dropna().astype(str).tolist()
            if card_ids:
                with st.spinner("Verificando polígonos no Pipefy..."):
                    pipefy_docs = get_docs_by_card_ids(card_ids)
        except Exception:
            pass

        for _, r in fi_df.iterrows():
            faltando = []
            valor_raw = str(r.get("valor","") or "").strip()
            if not valor_raw or valor_raw in ("0,00","0.00","0",""):
                faltando.append("Valor/Preço")
            area_raw = r.get("area_m2") or r.get("area_total_m_")
            if not area_raw or str(area_raw).strip() in ("","0","0.0"):
                faltando.append("Área")
            dim_raw = str(r.get("dimensao_do_terreno","") or "").strip()
            if not dim_raw or dim_raw.lower() in ("","xx","x","—"):
                faltando.append("Dimensões do terreno")
            if not str(r.get("id_zoneamento","") or "").strip():
                faltando.append("Zoneamento")
            if not str(r.get("contato_do_parceiro","") or "").strip():
                faltando.append("Contato do parceiro")
            if not str(r.get("link_da_pasta_do_terreno","") or "").strip():
                faltando.append("Pasta de documentos")
            if not str(r.get("triagem_inicial","") or "").strip():
                faltando.append("Triagem inicial")

            # Status do Polígono via Pipefy
            card_id_str = str(r.get("id_do_card","") or "")
            doc_info    = pipefy_docs.get(card_id_str, {})
            if doc_info:
                if doc_info.get("poligono_ok"):
                    poligono_txt = "✅ Polígono anexado"
                    if doc_info.get("poligono_url"):
                        poligono_txt += f" — [ver arquivo]({doc_info['poligono_url']})"
                else:
                    poligono_txt = "❌ Polígono não anexado"
                    faltando.insert(0, "Polígono")
                matricula_val = doc_info.get("matricula")
                matricula_txt = f"Matrícula: **{matricula_val}**" if matricula_val else "Matrícula: —"
            else:
                poligono_txt  = "⚠️ Polígono: não verificado (configure PIPEFY_TOKEN)"
                matricula_txt = ""

            faltando_txt = " · ".join(f"❌ {f}" for f in faltando) if faltando else "✅ Campos básicos preenchidos"
            dias_fi  = int(r.get("dias_na_fase", 0) or 0)
            pip_url  = f"https://app.pipefy.com/pipes/{PIPEFY_PIPE_ID}#cards/{card_id_str or r.get('id','')}"

            st.error(
                f"**ID {r['id']} | {r['terreno']}** — {r.get('cidade','')} · "
                f"Executivo: {r.get('analista','')} · {dias_fi}d nesta fase\n\n"
                f"{faltando_txt}\n\n"
                f"{poligono_txt}  {('· ' + matricula_txt) if matricula_txt else ''}\n\n"
                f"[🔗 Abrir no Pipefy]({pip_url})"
            )
            alertas = True

    # Sem Matrícula
    if "tem_matricula" in df_ativo.columns and not df_ativo["tem_matricula"].isna().all():
        for _, r in df_ativo[~df_ativo["tem_matricula"].fillna(False).astype(bool)].iterrows():
            st.error(
                f"**Sem Matrícula — {r['id']} | {r['terreno']}** · "
                f"{r.get('cidade','')} · Risco jurídico ao investidor"
            )
            alertas = True

    # Score abaixo da régua
    for _, r in df_ativo[(score_a < SCORE_MINIMO) &
                          df_ativo["fase_atual"].isin(["Análise Preliminar","Triagem de terrenos"])].iterrows():
        st.warning(
            f"**Score {r['score']} abaixo da régua — {r['id']} | {r['terreno']}** · "
            f"Interesse {r.get('interesse','?')}, Micro {r.get('score_micro','?')} · "
            f"Fase: {r['fase_atual']} · Considerar Backup"
        )
        alertas = True

    # Cota acima do cap
    for _, r in df_ativo[cota_a > cap_a].iterrows():
        st.warning(
            f"**Cota acima do cap — {r['id']} | {r['terreno']}** · "
            f"Cota R$ {r['cota_terreno']:,.0f} > Cap R$ {r['ticket_cap']:,.0f} · "
            f"{r.get('microrregiao','')}"
        )
        alertas = True

    # Documentos faltando / divergência
    for _, r in df_ativo.iterrows():
        docs = r.get("_docs")
        if not docs:
            continue
        for _, doc in docs.items():
            if not doc.get("anexado"):
                st.error(
                    f"**Doc faltando — {r['id']} | {r['terreno']}** · "
                    f"{doc['nome']} não anexado · "
                    f"Executivo de Canais: {r.get('analista','')} · Fase: {r.get('fase_atual','')}"
                )
                alertas = True
            elif not doc.get("ok") and doc.get("divergencia"):
                st.warning(
                    f"**Divergência doc — {r['id']} | {r['terreno']}** · "
                    f"{doc['nome']}: {doc['divergencia']} · "
                    f"Executivo de Canais: {r.get('analista','')} · Fase: {r.get('fase_atual','')}"
                )
                alertas = True

    if not alertas:
        st.success("Nenhum alerta ativo no momento.")

    if not df_pd_raw.empty:
        st.markdown("---")
        st.subheader("📞 Corretores — Pipedrive")
        st.dataframe(df_pd_raw[["terreno","status_pd","corretor","valor_pd"]].head(50),
                     width='stretch', hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# ABA 5 — VALIDAR MATRÍCULA
# ══════════════════════════════════════════════════════════════════════════════
with tab_matricula:
    st.subheader("📋 Validar Matrícula")
    st.caption("Faça upload da matrícula recebida pelo WhatsApp para validar as informações antes de cadastrar o card.")

    col_card, col_upload = st.columns([1, 1])

    with col_card:
        st.markdown("**1. Selecione o terreno**")
        opcoes_terreno = ["— Novo terreno (sem card) —"] + df_raw["terreno"].dropna().tolist() if not df_raw.empty else ["— Novo terreno (sem card) —"]
        terreno_sel = st.selectbox("Terreno:", opcoes_terreno, key="mat_terreno_sel")

    with col_upload:
        st.markdown("**2. Anexe a matrícula**")
        arquivo = st.file_uploader(
            "Imagem ou PDF da matrícula",
            type=["jpg", "jpeg", "png", "pdf"],
            key="mat_upload"
        )

    st.markdown("---")

    if arquivo is not None:
        if st.button("🔍 Validar Matrícula", key="btn_validar_matricula", type="primary"):
            mime_map = {
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "pdf": "application/pdf"
            }
            ext = arquivo.name.rsplit(".", 1)[-1].lower()
            media_type = mime_map.get(ext, "image/jpeg")

            with st.spinner("Analisando documento com IA..."):
                try:
                    from ai_client import validar_matricula
                    resultado = validar_matricula(arquivo.read(), media_type)
                    st.session_state["mat_resultado"] = resultado
                    st.session_state["mat_terreno"] = terreno_sel
                except Exception as e:
                    st.error(f"Erro ao validar: {e}")
                    st.session_state.pop("mat_resultado", None)

    if "mat_resultado" in st.session_state:
        r = st.session_state["mat_resultado"]
        terreno_nome = st.session_state.get("mat_terreno", "—")

        alertas = r.get("alertas") or []
        if alertas:
            st.error(f"⚠️ {len(alertas)} problema(s) encontrado(s) na matrícula de **{terreno_nome}**")
            for alerta in alertas:
                st.warning(f"• {alerta}")
        else:
            st.success(f"✅ Matrícula de **{terreno_nome}** validada sem divergências.")

        st.markdown("#### Informações extraídas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nº Matrícula", r.get("numero_matricula") or "—")
            st.metric("Status", r.get("status_matricula") or "—")
        with col2:
            st.metric("Proprietário", r.get("proprietario") or "—")
            st.metric("Área (m²)", r.get("area_m2") or "—")
        with col3:
            st.metric("Data de Emissão", r.get("data_emissao") or "—")
            st.metric("Localização", r.get("localizacao") or "—")

        if st.button("🗑️ Limpar resultado", key="btn_limpar_mat"):
            st.session_state.pop("mat_resultado", None)
            st.session_state.pop("mat_terreno", None)
            st.rerun()
    elif arquivo is None:
        st.info("Faça upload de uma matrícula acima para iniciar a validação.")

# ══════════════════════════════════════════════════════════════════════════════
# ABA 6 — PESQUISA CORRETORES
# ══════════════════════════════════════════════════════════════════════════════
with tab_pesquisa:
    st.subheader("📞 Pesquisa de Corretores — Carteira Farmer")

    FARMER_OWNER_ID = 23882201

    # ── Seletor de período ────────────────────────────────────────────────────
    col_per, col_d1, col_d2 = st.columns([2, 2, 2])
    with col_per:
        periodo_sel = st.radio(
            "Período:",
            ["Hoje", "Esta semana", "Este mês", "Personalizado"],
            horizontal=True,
            key="pesq_periodo",
        )

    hoje_p = datetime.today().date()
    if periodo_sel == "Hoje":
        data_ini_p = hoje_p
        data_fim_p = hoje_p
    elif periodo_sel == "Esta semana":
        data_ini_p = hoje_p - timedelta(days=hoje_p.weekday())  # segunda-feira
        data_fim_p = hoje_p
    elif periodo_sel == "Este mês":
        data_ini_p = hoje_p.replace(day=1)
        data_fim_p = hoje_p
    else:
        data_ini_p = hoje_p - timedelta(days=30)
        data_fim_p = hoje_p

    with col_d1:
        data_ini_p = st.date_input(
            "De:",
            value=data_ini_p,
            max_value=hoje_p,
            key="pesq_d_ini",
            disabled=(periodo_sel != "Personalizado"),
        )
    with col_d2:
        data_fim_p = st.date_input(
            "Até:",
            value=data_fim_p,
            max_value=hoje_p,
            key="pesq_d_fim",
            disabled=(periodo_sel != "Personalizado"),
        )

    @st.cache_data(ttl=0, show_spinner="Consultando atividades no Nekt…")
    def fetch_pesquisa_corretores(d_ini_str: str, d_fim_str: str):
        from nekt_client import _load_jwt, init_session, execute_sql
        jwt = _load_jwt()
        if not jwt:
            raise ValueError("JWT não configurado.")
        sid = init_session(jwt)

        d_ini_iso = f"{d_ini_str}T00:00:00Z"
        d_fim_iso = f"{d_fim_str}T23:59:59Z"

        # 1 — Sem resposta (marked_as_done_time é varchar — comparar com string ISO)
        sql_sem_resp = f"""
WITH enviados AS (
  SELECT a.person_id, a.deal_id,
    MAX(from_iso8601_timestamp(a.marked_as_done_time)) AS ultimo_envio
  FROM nekt_operacional_bronze.pipedrive_activities a
  JOIN nekt_operacional_bronze.pipedrive_deals d ON a.deal_id = d.id
  WHERE a.subject = 'SZI - Follow UP Parceiro'
    AND a.done = true AND a.is_deleted = false
    AND a.marked_as_done_time >= '{d_ini_iso}'
    AND a.marked_as_done_time <= '{d_fim_iso}'
    AND d.pipeline_id = 45
  GROUP BY a.person_id, a.deal_id
),
respondidos AS (
  SELECT DISTINCT deal_id FROM nekt_operacional_bronze.pipedrive_activities
  WHERE subject LIKE 'Whatsapp chat%' AND is_deleted = false
    AND add_time >= TIMESTAMP '{d_ini_str} 00:00:00'
)
SELECT p.name AS corretor, e.deal_id,
  CAST(DATE_TRUNC('day', e.ultimo_envio) AS DATE) AS ultimo_fup,
  DATE_DIFF('day', DATE_TRUNC('day', e.ultimo_envio), TIMESTAMP '{d_fim_str} 00:00:00') AS dias_sem_resposta
FROM enviados e
JOIN nekt_operacional_bronze.pipedrive_persons p ON e.person_id = p.id
LEFT JOIN respondidos r ON e.deal_id = r.deal_id
WHERE r.deal_id IS NULL
ORDER BY dias_sem_resposta DESC
"""

        # 2 — Enviaram terrenos (add_time é timestamp — usar TIMESTAMP literal)
        sql_enviaram = f"""
SELECT DISTINCT p.name AS corretor, a.deal_id,
  CAST(DATE_TRUNC('day', a.add_time) AS DATE) AS data_indicacao
FROM nekt_operacional_bronze.pipedrive_activities a
JOIN nekt_operacional_bronze.pipedrive_deals d ON a.deal_id = d.id
JOIN nekt_operacional_bronze.pipedrive_persons p ON a.person_id = p.id
WHERE a.is_deleted = false
  AND a.add_time >= TIMESTAMP '{d_ini_str} 00:00:00'
  AND a.add_time <  TIMESTAMP '{d_fim_str} 23:59:59'
  AND d.pipeline_id = 45
  AND (
    LOWER(a.note) LIKE '%enviou%terreno%'
    OR LOWER(a.note) LIKE '%indicou%terreno%'
    OR LOWER(a.note) LIKE '%mandou%terreno%'
    OR LOWER(a.note) LIKE '%enviou terreno%'
    OR LOWER(a.note) LIKE '%mandou terreno%'
  )
ORDER BY data_indicacao DESC
"""

        # 3 — Vão procurar
        sql_vao = f"""
SELECT DISTINCT p.name AS corretor, a.deal_id,
  CAST(DATE_TRUNC('day', a.add_time) AS DATE) AS data_conversa
FROM nekt_operacional_bronze.pipedrive_activities a
JOIN nekt_operacional_bronze.pipedrive_deals d ON a.deal_id = d.id
JOIN nekt_operacional_bronze.pipedrive_persons p ON a.person_id = p.id
WHERE a.subject LIKE 'Whatsapp chat%'
  AND a.is_deleted = false
  AND a.add_time >= TIMESTAMP '{d_ini_str} 00:00:00'
  AND a.add_time <  TIMESTAMP '{d_fim_str} 23:59:59'
  AND d.pipeline_id = 45
  AND (
    LOWER(a.note) LIKE '%vai procurar%'
    OR LOWER(a.note) LIKE '%vou procurar%'
    OR LOWER(a.note) LIKE '%vou verificar%'
    OR LOWER(a.note) LIKE '%vou ver%'
    OR LOWER(a.note) LIKE '%vou buscar%'
    OR LOWER(a.note) LIKE '%vou olhar%'
    OR LOWER(a.note) LIKE '%vou pesquisar%'
  )
ORDER BY data_conversa DESC
"""

        # 4 — Fora do perfil
        sql_fora = f"""
SELECT DISTINCT p.name AS corretor, a.deal_id,
  CAST(DATE_TRUNC('day', a.add_time) AS DATE) AS data_conversa
FROM nekt_operacional_bronze.pipedrive_activities a
JOIN nekt_operacional_bronze.pipedrive_deals d ON a.deal_id = d.id
JOIN nekt_operacional_bronze.pipedrive_persons p ON a.person_id = p.id
WHERE a.subject LIKE 'Whatsapp chat%'
  AND a.is_deleted = false
  AND a.add_time >= TIMESTAMP '{d_ini_str} 00:00:00'
  AND a.add_time <  TIMESTAMP '{d_fim_str} 23:59:59'
  AND d.pipeline_id = 45
  AND (
    LOWER(a.note) LIKE '%não trabalha%'
    OR LOWER(a.note) LIKE '%nao trabalha%'
    OR LOWER(a.note) LIKE '%não tem%perfil%'
    OR LOWER(a.note) LIKE '%sem interesse%'
    OR LOWER(a.note) LIKE '%fora do perfil%'
    OR LOWER(a.note) LIKE '%não tenho terrenos%'
  )
ORDER BY data_conversa DESC
"""

        results = {}
        for key, sql in [
            ("sem_resposta", sql_sem_resp),
            ("enviaram",     sql_enviaram),
            ("vao_procurar", sql_vao),
            ("fora_perfil",  sql_fora),
        ]:
            try:
                results[key] = execute_sql(sql, jwt, sid)
            except Exception as e:
                results[key] = [{"erro": str(e)}]
        return results

    d_ini_str_p = data_ini_p.strftime("%Y-%m-%d")
    d_fim_str_p = data_fim_p.strftime("%Y-%m-%d")

    st.markdown("---")
    col_btn_p, col_info_p = st.columns([1, 4])
    with col_btn_p:
        rodar_pesquisa = st.button("🔄 Atualizar pesquisa", key="btn_pesquisa", type="primary")
    with col_info_p:
        st.caption(f"Período selecionado: {data_ini_p.strftime('%d/%m/%Y')} a {data_fim_p.strftime('%d/%m/%Y')}")

    if rodar_pesquisa or "pesquisa_cache" in st.session_state:
        if rodar_pesquisa:
            with st.spinner("Consultando atividades no Nekt (pode levar ~30s)..."):
                try:
                    dados = fetch_pesquisa_corretores(d_ini_str_p, d_fim_str_p)
                    st.session_state["pesquisa_cache"] = dados
                    st.session_state["pesquisa_periodo"] = f"{data_ini_p.strftime('%d/%m/%Y')} a {data_fim_p.strftime('%d/%m/%Y')}"
                except Exception as e:
                    st.error(f"Erro ao buscar dados: {e}")
                    dados = None
        else:
            dados = st.session_state.get("pesquisa_cache")

        if dados:
            sem_resp   = [r for r in dados.get("sem_resposta", []) if "erro" not in r]
            enviaram   = [r for r in dados.get("enviaram",     []) if "erro" not in r]
            vao        = [r for r in dados.get("vao_procurar", []) if "erro" not in r]
            fora       = [r for r in dados.get("fora_perfil",  []) if "erro" not in r]

            periodo_exibir = st.session_state.get("pesquisa_periodo", "—")
            st.caption(f"📅 Dados referentes ao período: **{periodo_exibir}**")

            # Resumo
            c1p, c2p, c3p, c4p = st.columns(4)
            c1p.metric("🔴 Sem resposta",   len(sem_resp))
            c2p.metric("✅ Enviaram terrenos", len(enviaram))
            c3p.metric("🔍 Vão procurar",   len(vao))
            c4p.metric("❌ Fora do perfil", len(fora))

            st.markdown("---")

            # 1 — Sem resposta
            with st.expander(f"🔴 Sem resposta — {len(sem_resp)} corretores", expanded=True):
                if sem_resp:
                    df_sr = pd.DataFrame(sem_resp)
                    df_sr["ultimo_fup"] = pd.to_datetime(df_sr["ultimo_fup"], errors="coerce").dt.strftime("%d/%m/%Y")
                    df_sr.rename(columns={
                        "corretor": "Corretor", "deal_id": "Deal ID",
                        "ultimo_fup": "Último FUP", "dias_sem_resposta": "Dias sem resposta"
                    }, inplace=True)
                    st.dataframe(df_sr, use_container_width=True, hide_index=True)
                else:
                    st.success("Nenhum corretor sem resposta no período.")

            # 2 — Enviaram terrenos
            with st.expander(f"✅ Enviaram terrenos — {len(enviaram)} corretores"):
                if enviaram:
                    df_env = pd.DataFrame(enviaram)
                    df_env["data_indicacao"] = pd.to_datetime(df_env["data_indicacao"], errors="coerce").dt.strftime("%d/%m/%Y")
                    df_env.rename(columns={
                        "corretor": "Corretor", "deal_id": "Deal ID",
                        "data_indicacao": "Data indicação"
                    }, inplace=True)
                    st.dataframe(df_env, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum registro de envio de terreno no período.")

            # 3 — Vão procurar
            with st.expander(f"🔍 Disseram que vão procurar — {len(vao)} corretores"):
                if vao:
                    df_vao = pd.DataFrame(vao)
                    df_vao["data_conversa"] = pd.to_datetime(df_vao["data_conversa"], errors="coerce").dt.strftime("%d/%m/%Y")
                    df_vao.rename(columns={
                        "corretor": "Corretor", "deal_id": "Deal ID",
                        "data_conversa": "Data conversa"
                    }, inplace=True)
                    st.dataframe(df_vao, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum registro de intenção de busca no período.")

            # 4 — Fora do perfil
            with st.expander(f"❌ Fora do perfil — {len(fora)} corretores"):
                if fora:
                    df_fora = pd.DataFrame(fora)
                    df_fora["data_conversa"] = pd.to_datetime(df_fora["data_conversa"], errors="coerce").dt.strftime("%d/%m/%Y")
                    df_fora.rename(columns={
                        "corretor": "Corretor", "deal_id": "Deal ID",
                        "data_conversa": "Data conversa"
                    }, inplace=True)
                    st.dataframe(df_fora, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum corretor fora do perfil identificado no período.")

            # Erros de query
            for key, label in [("sem_resposta","Sem resposta"),("enviaram","Enviaram"),
                                ("vao_procurar","Vão procurar"),("fora_perfil","Fora do perfil")]:
                erros = [r for r in dados.get(key, []) if "erro" in r]
                if erros:
                    st.warning(f"⚠️ {label}: {erros[0]['erro']}")
    else:
        st.info("Clique em **Atualizar pesquisa** para carregar os dados mais recentes.")

# ══════════════════════════════════════════════════════════════════════════════
# AI ASSISTANT — CHAT
# ══════════════════════════════════════════════════════════════════════════════

# Inicializa estado
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

# Botão para abrir chat
if st.button("💬 AI Assistant", key="btn_chat", use_container_width=False):
    st.session_state.show_chat = not st.session_state.show_chat

# Chat popup
if st.session_state.show_chat:
    st.markdown("---")
    st.subheader("💬 AI Assistant — Prospecção de Terrenos")
    st.caption("Analise terrenos, gere mensagens para corretores, sugira próximos passos")

    # Histórico
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Digite sua pergunta..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        try:
            from ai_client import ask_claude
            dias_chat = pd.to_numeric(df_raw.get("dias_na_fase", pd.Series(dtype=float)), errors="coerce") if "dias_na_fase" in df_raw.columns else pd.Series(dtype=float)
            score_chat = pd.to_numeric(df_raw["score"], errors="coerce")
            contexto_funil = f"""[CONTEXTO DO FUNIL ATUAL — {datetime.now().strftime('%d/%m/%Y %H:%M')}]
Total: {len(df_raw)} terrenos | Qualificados (≥{SCORE_MINIMO}): {int((score_chat >= SCORE_MINIMO).sum())} | Travados (≥15d): {int((dias_chat >= 15).sum())}
Fases: {df_raw['fase_atual'].value_counts().to_dict()}
"""
            prompt_com_contexto = contexto_funil + "\n" + prompt
            with st.spinner("Pensando..."):
                response = ask_claude(prompt_com_contexto, st.session_state.chat_history[:-1])
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Erro: {e}")
            st.session_state.chat_history.append({"role": "assistant", "content": "Erro ao conectar. Tente novamente."})

        st.rerun()

    # Limpar
    if st.session_state.chat_history and st.button("🗑️ Limpar"):
        st.session_state.chat_history = []
        st.rerun()
