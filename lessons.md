# Lições Aprendidas — SZI Painel Terrenos
> Atualizado em 10/06/2026

---

## Autenticação Nekt MCP

### JWT vai no header Authorization
```python
headers = {"Authorization": f"Bearer {jwt}"}
```

### Session ID pode ser vazio — não é erro
O Nekt retorna `mcp-session-id` no header de `initialize`. Se vazio, funciona em modo stateless.

### st.secrets — sempre usar try/except
```python
try:
    return st.secrets["NEKT_JWT_TOKEN"]
except Exception:
    return ""
```

### Três formatos de secret aceitos
- `NEKT_JWT_TOKEN = "..."` (flat)
- `[nekt] / jwt_token = "..."` (seção TOML)
- `jwt_token = "..."` (plano)

---

## Dados e SQL

### UTF-8 Mojibake
```python
raw_text = r.content.decode("utf-8", errors="replace")
```
`requests.text` usa Latin-1 por padrão para SSE.

### pandas 2.x — `.replace("", Series)` não funciona
Usar `.loc[mask]` para substituição condicional.

### Nomes de analistas — filtrar inválidos
- Rejeitar nomes > 60 chars e nomes que começam com dígito
- SQL: `LENGTH(executivo_de_canais) < 60`

### Conversão de valores em Real
```python
float(str(s).replace("R$","").replace(" ","").replace(".","").replace(",",".").strip())
```

---

## Streamlit

### Cache ttl=0 para dados sempre frescos
```python
@st.cache_data(ttl=0, show_spinner="Buscando dados do Nekt…")
def fetch_nekt_data(): ...
```

### Fallback para modo demonstração
```python
try:
    df_raw = fetch_nekt_data()
    if df_raw.empty:
        df_raw = demo_data(); DEMO = True
except Exception:
    df_raw = demo_data(); DEMO = True
```

### Filtro global de analista — aplicar logo após carregar df_raw
```python
df_raw = df_raw[df_raw["analista"] == "Farmer"].copy()
```
Garante que TODO o app mostra apenas terrenos do Farmer (Ricardo Macedo).

### LinkColumn — versão 1.57
O valor da célula deve ser a URL diretamente. `display_text` aceita string estática ou regex.

---

## Deploy

### SSL verification desativado (verify=False)
Nekt, Pipefy e gateway IA usam certificados auto-assinados.

### Secrets no Streamlit Cloud — colar todos de uma vez
```toml
NEKT_JWT_TOKEN = "eyJ..."
ANTHROPIC_API_KEY = "sk-WFLxVCpL5vJZCbQgHKeB7Q"
ANTHROPIC_BASE_URL = "https://hub.seazone.dev"
PIPEFY_TOKEN = "eyJ..."
```
Colar com quebra de linha dentro do valor ou duplicado → erro "Invalid format: please enter valid TOML".

### .gitignore essencial
```
.nekt_secrets
nekt_token.json
__pycache__/
*.pyc
.streamlit/secrets.toml
```
`lessons.md` e `memory.md` NÃO entram no .gitignore — são documentação do projeto.

---

## IA — Gateway Seazone (hub.seazone.dev)

### Configuração correta
```python
client = anthropic.Anthropic(
    api_key="sk-WFLxVCpL5vJZCbQgHKeB7Q",
    base_url="https://hub.seazone.dev",
    http_client=httpx.Client(verify=False)
)
```

### Modelo: minimax-m2.7
Não usar `claude-sonnet-*` → retorna 401.

### httpx obrigatório no requirements.txt
O SDK anthropic usa httpx internamente. Adicionar `httpx>=0.24.0`.

### max_tokens mínimo: 100
Com `max_tokens < 30` o modelo pode retornar `content: []`.

### Plano do Dia IA — contexto enviado
Envia: travados ≥15d (com dias), falta info (campos específicos), oportunidades (score ≥320 na triagem), top 5 VGV.
Retorna: ações urgentes, mensagens WhatsApp para corretor, oportunidades, saúde do funil.

### Campos na mensagem ao corretor
Apenas: Valor/Preço, Área (m²), Dimensões, Pasta de documentos, Triagem inicial.
**Removidos:** Zoneamento e Contato do proprietário.

---

## Pipefy GraphQL

### Token via JWT Bearer
```python
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
```

### Campo Polígono é attachment — valor é JSON array de URLs
```python
urls = json.loads(val)
poligono_ok = bool(urls)
```

### Campo Matrícula é select (Sim/Não/Não sabemos) — não é anexo
Desconsiderado. Não armazena metragem.

### Consulta por card individual
```python
query = f'{{ card(id: {card_id}) {{ fields {{ name value field {{ type }} }} }} }}'
```

### Leitura de anexos — download + extração de texto
```python
import pdfplumber, io
with pdfplumber.open(io.BytesIO(content)) as pdf:
    texto = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
```
- URLs de attachment são pre-signed S3 — tentar sem auth primeiro, usar Bearer como fallback
- Imagens não têm extração de texto (precisaria de OCR/Google Vision)
- Adicionar `pdfplumber>=0.10.0` no requirements.txt

---

## Erros comuns

| Erro | Causa | Solução |
|------|-------|---------|
| "You do not have access" | App inativo no Streamlit Cloud | share.streamlit.io → ⋮ → Reinício |
| Dados vazios / modo demo | JWT expirado | Renovar JWT nos Secrets |
| IA retorna 401 | Modelo errado ou chave inválida | Usar `minimax-m2.7` + chave `sk-WFLxVCpL5vJZCbQgHKeB7Q` |
| "Invalid format: valid TOML" | Token duplicado ou com quebra de linha | Apagar tudo e colar os 4 secrets de uma vez |
| Polígono não verificado | `PIPEFY_TOKEN` ausente | Adicionar nos Secrets do Streamlit Cloud |
| Documentos não carregam | `PIPEFY_TOKEN` ausente ou URL S3 expirada | Verificar token |
| httpx not found | Não estava em requirements.txt | Adicionar `httpx>=0.24.0` |
| Mojibake nos textos | requests decodificando como Latin-1 | `r.content.decode("utf-8")` |
