# Lições Aprendidas — SZI Painel Terrenos

Decisões técnicas tomadas durante o desenvolvimento e por que foram feitas assim.

---

## Autenticação Nekt MCP

### JWT vai no header Authorization, não no body
```python
headers = {"Authorization": f"Bearer {jwt}"}
```

### Session ID pode ser vazio — não é erro
O Nekt retorna `mcp-session-id` no header da resposta de `initialize`.
Se vier vazio, a sessão funciona normalmente em modo stateless.

### st.secrets pode lançar exceção em dev local
```python
try:
    return st.secrets["NEKT_JWT_TOKEN"]
except Exception:
    return ""
```
Sem `.streamlit/secrets.toml` local, `st.secrets` explode. Sempre usar try/except.

### Três formatos de secret aceitos (nekt_client.py)
- `NEKT_JWT_TOKEN = "..."` (flat)
- `[nekt] / jwt_token = "..."` (seção TOML)
- `jwt_token = "..."` (plano)

---

## Dados e SQL

### UTF-8 Mojibake — usar `.content.decode("utf-8")`
```python
raw_text = r.content.decode("utf-8", errors="replace")
```
`requests.text` usa Latin-1 por padrão para SSE. Forçar UTF-8 evita caracteres quebrados.

### pandas 2.x — `.replace("", Series)` não funciona mais
Usar `.loc[mask]` para substituição condicional em vez de `.replace`.

### Nomes de analistas no Pipefy nem sempre são pessoas
- Filtrar nomes com mais de 60 caracteres (são textos longos, não nomes)
- Rejeitar valores que começam com dígito (datas ou IDs caíram no campo)
- SQL filtra: `LENGTH(executivo_de_canais) < 60`

### Conversão de valores em Real brasileiro
```python
def _parse_br_money(s):
    return float(str(s).replace("R$","").replace(" ","")
                 .replace(".","").replace(",",".").strip())
```
Remove pontos de milhar antes de trocar vírgula decimal por ponto.

---

## Streamlit

### LinkColumn — parâmetro `url=` não existe na versão 1.57
O valor da célula deve ser a URL diretamente. `display_text` aceita string estática ou regex.

### Cache com ttl=0 para dados sempre frescos
```python
@st.cache_data(ttl=0, show_spinner="Buscando dados do Nekt…")
def fetch_nekt_data():
    ...
```
`ttl=0` desativa o cache — dados buscados a cada abertura do app.

### Fallback para modo demonstração
```python
try:
    df_raw = fetch_nekt_data()
    if df_raw.empty:
        df_raw = demo_data()
        DEMO = True
except Exception:
    df_raw = demo_data()
    DEMO = True
```
O app nunca quebra na tela do usuário — cai para dados sintéticos se o Nekt falhar.

---

## Deploy

### SSL verification desativado (verify=False)
O Nekt usa certificado auto-assinado. Necessário enquanto não for corrigido no servidor.

### .gitignore essencial
```
.nekt_secrets
nekt_token.json
__pycache__/
*.pyc
.streamlit/secrets.toml
lessons.md
memory.md
```

### Secrets no Streamlit Cloud (formato correto)
```toml
NEKT_JWT_TOKEN = "eyJ..."
ANTHROPIC_API_KEY = "sk-ant-..."
```

---

## IA (Claude API)

### Model ID correto
```python
model="claude-sonnet-4-5"
```

### Passar contexto real do funil no chat
Incluir resumo do estado atual (total, VGV, travados, fases) na mensagem enviada ao Claude
para que as respostas sejam sobre dados concretos, não genéricas.

### API key ausente deve mostrar mensagem clara
```python
except Exception as e:
    st.error(f"Configure ANTHROPIC_API_KEY nos secrets do Streamlit Cloud. Erro: {e}")
```

---

## Pipefy GraphQL

### Token via JWT Bearer
```python
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
```

### Campo Polígono é attachment — valor é JSON array de URLs
```python
urls = json.loads(val)  # ["https://app.pipefy.com/storage/..."]
poligono_ok = bool(urls)
```

### Campo Matrícula é select (Sim / Não / Não sabemos) — não é anexo
Não armazena metragem. Para comparar área da matrícula com área cadastrada
seria necessário Google Drive API ou campo manual no Pipefy.

### Consulta por card individual (não há batch por IDs)
```python
query = f'{{ card(id: {card_id}) {{ fields {{ name value field {{ type }} }} }} }}'
```

### SSL desativado também no Pipefy (mesmo problema do Nekt)
```python
requests.post(..., verify=False)
```

## IA — Gateway Seazone

### Endpoint correto: hub.seazone.dev (não api.anthropic.com)
```python
client = anthropic.Anthropic(
    api_key="sk-...",
    base_url="https://hub.seazone.dev",
    http_client=httpx.Client(verify=False)  # SSL auto-assinado
)
```

### Modelo disponível: minimax-m2.7
Chave `sk-WFLxVCpL5vJZCbQgHKeB7Q` só acessa `minimax-m2.7`.
Não usar `claude-sonnet-*` — retorna 401.

### Conteúdo vazio com max_tokens muito baixo
Se `max_tokens < 30`, o modelo pode retornar `content: []`.
Usar mínimo `max_tokens=100` para garantir resposta.

## Leitura de Anexos Pipefy

### pdfplumber para extração de texto de PDFs
```python
import pdfplumber, io
with pdfplumber.open(io.BytesIO(content)) as pdf:
    texto = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
```
Adicionado `pdfplumber>=0.10.0` no requirements.txt.

### Download de attachment — tentar sem auth primeiro (S3 pre-signed URL)
URLs de attachment do Pipefy são geralmente pre-signed do S3 — acessíveis sem Bearer token.
Só usar auth como fallback se o primeiro download falhar.

### Imagens não têm extração de texto
JPG/PNG/WEBP → apenas exibe o nome do arquivo. OCR exigiria Google Vision API.

### Filtro de analista aplicado globalmente após carregar df_raw
```python
df_raw = df_raw[df_raw["analista"] == "Farmer"].copy()
```
Garante que TODO o app (dashboard, alertas, ficha, IA) mostra apenas terrenos do Farmer (Ricardo).

### Campos verificados na mensagem ao corretor (Falta Informação)
Somente: Valor/Preço, Área (m²), Dimensões, Pasta de documentos, Triagem inicial.
Zoneamento e Contato do proprietário foram removidos a pedido do usuário (10/06/2026).

### Plano do Dia IA — contexto enviado
O botão "Gerar análise" envia para a IA:
- Travados ≥15 dias com dias_na_fase
- Falta Informação com campos específicos faltantes por terreno
- Oportunidades (score ≥320 parados na triagem)
- Top 5 por VGV
A IA retorna: ações urgentes, mensagens WhatsApp prontas, oportunidades e saúde do funil.

## Erros comuns

| Erro | Causa | Solução |
|------|-------|---------|
| App mostra "You do not have access" | App deletado ou inativo no Streamlit Cloud | Reiniciar via share.streamlit.io → ⋮ → Reinício |
| Dados vazios / modo demo | JWT expirado ou tabela Nekt inacessível | Verificar JWT nos Secrets; testar query direto no Nekt |
| Botões de IA mostram erro | `ANTHROPIC_API_KEY` não configurado | Adicionar nos Secrets do Streamlit Cloud |
| Mojibake nos textos | requests decodificando como Latin-1 | Usar `r.content.decode("utf-8")` |
| Polígono "não verificado" | `PIPEFY_TOKEN` ausente nos Secrets | Adicionar `PIPEFY_TOKEN` no Streamlit Cloud |
| IA retorna 401 | Modelo errado ou chave inválida | Usar `minimax-m2.7` e chave `sk-WFLxVCpL5vJZCbQgHKeB7Q` |
| "Invalid format: please enter valid TOML" | Token colado com quebra de linha ou duplicado | Apagar tudo e colar os 4 secrets de uma vez em formato flat |
| Documentos não carregam (Ler docs) | `PIPEFY_TOKEN` ausente ou URL expirada | Verificar token; URLs S3 têm validade |
