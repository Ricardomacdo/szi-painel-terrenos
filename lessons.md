# Lições Aprendidas — SZI Painel Terrenos

## Autenticação Nekt MCP

### OAuth PKCE é necessário
O Nekt usa OAuth 2.0 com PKCE. Não funciona com token fixo.
- `code_verifier` = 64 bytes random, codificado em base64url
- `code_challenge` = SHA256 do verifier, também base64url
- Exchange exige o verifier original (não o hash)

### Client registration dinâmico
O endpoint `/register` cria um client_id único por sessão.
- Fallback: `client_id = "claude-code"` se o registro falhar
- `client_secret` pode ser vazio com `token_endpoint_auth_method: client_secret_post`

### JWT no header, não no body
```python
headers = {"Authorization": f"Bearer {jwt}"}
```
O JWT vai no Authorization header, não no body do request.

### Session ID no header de resposta
```python
session_id = r.headers.get("mcp-session-id", "")
```
O MCP retorna `mcp-session-id` no header da resposta de `initialize`, não no body JSON.

## Streamlit + Nekt

### st.secrets pode não existir
```python
try:
    return st.secrets["NEKT_JWT_TOKEN"]
except Exception:
    return ""
```
Em desenvolvimento local sem `.streamlit/config.toml`, `st.secrets` levanta exceção.

### Cache com TTL
```python
@st.cache_data(ttl=300, show_spinner="...")
def fetch_nekt_data():
    ...
```
- TTL de 300s (5 min) evita chamadas excessivas
- `show_spinner` melhora UX durante carregamento

### Fallback para demo
O app detecta erro e cai para dados demo automaticamente:
```python
try:
    df_raw = fetch_nekt_data()
    if df_raw.empty:
        df_raw = demo_data()
        DEMO = True
except Exception as e:
    df_raw = demo_data()
    DEMO = True
```

## Dados e SQL

### Conversão de dinheiro brasileiro
```python
def _parse_br_money(s):
    return float(str(s).replace("R$","").replace(" ","")
 .replace(".","").replace(",",".").strip())
```
- Remove pontos de milhar primeiro
- Troca vírgula decimal por ponto

### Datas em múltiplos formatos
```python
for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
    try:
        return datetime.strptime(str(s)[:len(fmt)], fmt)
    except Exception:
        continue
```
O Nekt retorna datas em formatos variados.

### Nomes de analistas
Nem todos os nomes no Pipefy são pessoas reais.
- Filtrar nomes > 60 chars (são textos longos, não nomes)
- Rejeitar nomes que começam com dígito (datas ou IDs)
- Mapear nomes canônicos: "Ricardo Macedo" → "Farmer"

### Etapas válidas
O Pipefy tem 22 etapas, mas nem todas são "ativas".
- Filtrar só as etapas do funil principal (não "Perdido", "Ganho", "Excluídos" para contagem)
- `ETAPAS_VALIDAS` no SQL garante só cards ativos

## UI/UX

### Semáforo de tempo
```python
def semaforo_dias(d):
    if d < 7:   return f"🟢 {d}d"
    elif d < 15: return f"🟡 {d}d"
    else:        return f"🔴 {d}d"
```
- 🟢 Verde: em dia (<7 dias)
- 🟡 Amarelo: atenção (7-14 dias)
- 🔴 Vermelho: travado (≥15 dias)

### Gate AP
Regras de passam/não passam baseadas em interesse (1-5) e micro-score:
- Interesse 5 → qualquer micro passa
- Interesse 4 → micro ≥ 7 passa
- Interesse 3 → micro ≥ 8 passa
- Interesse 1-2 → micro 10 auto-passa, micro ≥8 condicional

### Link para o Pipefy
O card ID do Nekt é o ID numérico do Pipefy:
```python
pipefy_url = f"https://app.pipefy.com/pipes/{PIPEFY_PIPE_ID}#cards/{id_do_card}"
```

## Deploy

### SSL verification
```python
verify=False
```
Necessário porque o Nekt usa certificado auto-assinado ou não configura SSL corretamente. Quando o Nekt corrigir, remover.

### .gitignore essencial
```
.nekt_secrets
nekt_token.json
__pycache__/
*.pyc
.streamlit/config.toml
streamlit_real*.log
```

### Secrets no Streamlit Cloud
Formato `secrets.toml`:
```toml
NEKT_JWT_TOKEN = "eyJ..."
```

## Erros comuns

### "mcp-session-id" vazio
- Não é erro — o MCP funciona stateless
- Só indica que o servidor não mantém sessão

### Dados vazios no Nekt
- Verificar se a tabela existe: `nekt_operacional_silver.pipefy_szi_all_cards_transformada_bd_terreno`
- Verificar se o JWT tem permissão para a tabela
- Testar query no Nekt UI primeiro

### Unicode/Mojibake
```python
raw_text = r.content.decode("utf-8", errors="replace")
```
O Nekt pode retornar latin-1; forçar UTF-8 com fallback.

### Pipefy API rate limit
- 50 cards por página (param `first: 50`)
- Loop com cursor para paginar
- TTL de 5 min no cache ajuda
