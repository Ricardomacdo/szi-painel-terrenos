"""
Cliente Pipefy para o Painel SZI Terrenos.
- Verifica documentos (Polígono) nos cards
- Lê e extrai texto dos anexos para análise IA
"""
import io
import json
import requests
import warnings
warnings.filterwarnings("ignore")

PIPEFY_URL  = "https://app.pipefy.com/queries"
PIPEFY_PIPE = "304543320"


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


def _extract_pdf_text(content: bytes) -> str:
    """Extrai texto de um PDF em bytes. Retorna string ou mensagem de erro."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            textos = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    textos.append(t.strip())
            return "\n".join(textos) if textos else "[PDF sem texto extraível]"
    except ImportError:
        return "[pdfplumber não instalado]"
    except Exception as e:
        return f"[Erro ao extrair PDF: {e}]"


def _download_file(url: str, token: str) -> tuple[bytes, str]:
    """
    Baixa um arquivo de URL do Pipefy.
    Retorna (conteúdo_bytes, mime_type).
    """
    # Tenta primeiro sem auth (URLs pre-signed do S3)
    try:
        r = requests.get(url, timeout=30, verify=False)
        if r.status_code == 200:
            mime = r.headers.get("Content-Type", "")
            return r.content, mime
    except Exception:
        pass

    # Tenta com Bearer token
    try:
        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
            verify=False,
        )
        if r.status_code == 200:
            mime = r.headers.get("Content-Type", "")
            return r.content, mime
    except Exception:
        pass

    return b"", ""


def _read_attachment(url: str, nome: str, token: str) -> str:
    """Baixa e extrai texto de um anexo. Retorna texto legível."""
    content, mime = _download_file(url, token)
    if not content:
        return f"[Não foi possível baixar: {nome}]"

    ext = nome.lower().rsplit(".", 1)[-1] if "." in nome else ""

    if "pdf" in mime or ext == "pdf":
        texto = _extract_pdf_text(content)
        return f"=== {nome} (PDF) ===\n{texto}"

    if "text" in mime or ext in ("txt", "csv", "md"):
        try:
            return f"=== {nome} (texto) ===\n{content.decode('utf-8', errors='replace')}"
        except Exception:
            return f"[Erro ao ler texto: {nome}]"

    if ext in ("jpg", "jpeg", "png", "gif", "webp") or "image" in mime:
        return f"=== {nome} (imagem — sem extração de texto) ==="

    # Genérico
    try:
        return f"=== {nome} ===\n{content.decode('utf-8', errors='replace')[:2000]}"
    except Exception:
        return f"=== {nome} (binário — {len(content)} bytes) ==="


def get_card_attachments_text(card_id: str) -> str:
    """
    Lê todos os anexos de um card do Pipefy e retorna o texto extraído.

    Args:
        card_id: ID real do card no Pipefy (campo id_do_card na tabela Nekt)

    Returns:
        Texto extraído de todos os anexos, concatenado.
        Retorna mensagem de erro/aviso se token ausente ou card sem anexos.
    """
    token = _load_token()
    if not token:
        return "⚠️ PIPEFY_TOKEN não configurado nos secrets."

    q = f"""{{
      card(id: {card_id}) {{
        id
        title
        fields {{
          name
          value
          field {{ type }}
        }}
      }}
    }}"""

    try:
        data = _query(q, token)
    except Exception as e:
        return f"⚠️ Erro ao consultar Pipefy: {e}"

    card = data.get("data", {}).get("card", {})
    if not card:
        return f"⚠️ Card {card_id} não encontrado no Pipefy."

    titulo = card.get("title", card_id)
    blocos = [f"📎 Documentos do card: **{titulo}** (ID: {card_id})\n"]
    total_anexos = 0

    for f in card.get("fields", []):
        if f.get("field", {}).get("type") != "attachment":
            continue
        val = f.get("value")
        if not val:
            continue

        nome_campo = f.get("name", "Anexo")

        try:
            urls = json.loads(val) if isinstance(val, str) else val
            if not isinstance(urls, list):
                urls = [urls]
        except Exception:
            urls = [val]

        for url in urls:
            if not url:
                continue
            total_anexos += 1
            # Tenta extrair nome do arquivo da URL
            nome_arquivo = url.split("/")[-1].split("?")[0] or f"{nome_campo}_{total_anexos}"
            blocos.append(f"\n📄 Campo: {nome_campo}")
            texto = _read_attachment(url, nome_arquivo, token)
            blocos.append(texto)

    if total_anexos == 0:
        return f"ℹ️ Card **{titulo}** não possui anexos."

    return "\n".join(blocos)


def get_docs_by_card_ids(card_ids: list) -> dict:
    """
    Dado uma lista de id_do_card (IDs reais do Pipefy),
    retorna dict {card_id: {poligono_ok, poligono_url, matricula_valor}}.
    """
    token = _load_token()
    if not token:
        return {}

    result = {}
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
