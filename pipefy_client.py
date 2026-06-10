"""
Cliente Pipefy para o Painel SZI Terrenos.
Busca campos de documentos (Polígono, Matrícula) diretamente dos cards.
"""
import json
import requests
import warnings
warnings.filterwarnings("ignore")

PIPEFY_URL   = "https://app.pipefy.com/queries"
PIPEFY_PIPE  = "304543320"


def _load_token() -> str:
    """Carrega token do Pipefy — secrets Streamlit ou variável de ambiente."""
    import os
    try:
        import streamlit as st
        token = st.secrets.get("PIPEFY_TOKEN", "")
        if token:
            return str(token)
    except Exception:
        pass
    return os.environ.get("PIPEFY_TOKEN", "")


def _query(q: str, token: str) -> dict:
    r = requests.post(
        PIPEFY_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": q},
        timeout=30,
        verify=False,
    )
    r.raise_for_status()
    return r.json()


def get_docs_by_card_ids(card_ids: list[str]) -> dict[str, dict]:
    """
    Dado uma lista de id_do_card (IDs reais do Pipefy),
    retorna dict {card_id: {poligono_ok, poligono_url, matricula_valor}}.
    """
    token = _load_token()
    if not token:
        return {}

    result = {}
    # Pipefy não suporta busca em lote por IDs — consulta um a um (em lotes de 10)
    for card_id in card_ids:
        try:
            q = f"""{{
              card(id: {card_id}) {{
                id
                fields {{
                  name
                  value
                  field {{ type }}
                }}
              }}
            }}"""
            data = _query(q, token)
            card = data.get("data", {}).get("card", {})
            if not card:
                continue

            poligono_ok  = False
            poligono_url = None
            matricula    = None

            for f in card.get("fields", []):
                nome = (f.get("name") or "").lower()
                val  = f.get("value")

                if "pol" in nome and f["field"]["type"] == "attachment":
                    if val:
                        try:
                            urls = json.loads(val) if isinstance(val, str) else val
                            if urls:
                                poligono_ok  = True
                                poligono_url = urls[0] if isinstance(urls, list) else urls
                        except Exception:
                            poligono_ok = bool(val)

                if "matr" in nome:
                    matricula = str(val).strip() if val else None

            result[str(card_id)] = {
                "poligono_ok":  poligono_ok,
                "poligono_url": poligono_url,
                "matricula":    matricula,
            }
        except Exception:
            continue

    return result
