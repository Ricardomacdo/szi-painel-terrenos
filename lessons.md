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

## Erros comuns

| Erro | Causa | Solução |
|------|-------|---------|
| App mostra "You do not have access" | App deletado ou inativo no Streamlit Cloud | Reiniciar via share.streamlit.io → ⋮ → Reinício |
| Dados vazios / modo demo | JWT expirado ou tabela Nekt inacessível | Verificar JWT nos Secrets; testar query direto no Nekt |
| Botões de IA mostram erro | `ANTHROPIC_API_KEY` não configurado | Adicionar nos Secrets do Streamlit Cloud |
| Mojibake nos textos | requests decodificando como Latin-1 | Usar `r.content.decode("utf-8")` |
