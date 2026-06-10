# Contexto do Projeto — SZI Painel Terrenos

Você está trabalhando no projeto **SZI Painel Terrenos**, um dashboard Streamlit de monitoramento do funil de prospecção de terrenos da Seazone Investimentos (SZI).

---

## Onde está o projeto

- **URL pública:** https://szi-painel-terrenos-azp998z4x25rv9hcmoqm89.streamlit.app
- **Repositório GitHub:** https://github.com/Ricardomacdo/szi-painel-terrenos (branch `master`)
- **Diretório local:** `C:\Users\compu\Desktop\szi-painel-terrenos\`
- **Arquivo principal:** `app.py`

---

## O que o painel faz

Dashboard com 4 abas:
1. **Dashboard** — KPIs (56 terrenos, R$993,7M VGV), funil 22 etapas, score, tabela com link direto para o Pipefy
2. **Executivo de Canais** — breakdown por Farmer (Ricardo Macedo) e Key Account (Gabriel)
3. **Ficha do Terreno** — busca por ID ou nome, card completo com AP/EM/Private/EP + botão "Analisar com IA"
4. **Alertas** — travados ≥15d, falta info, sem matrícula, score baixo

Funcionalidades de IA (requerem `ANTHROPIC_API_KEY`):
- Análise automática do funil no Dashboard
- Análise individual de terreno na Ficha
- Chat assistente com contexto real do funil

---

## Fontes de dados

| Fonte | Endpoint | Auth |
|-------|----------|------|
| **Nekt MCP** (principal) | `https://nekt-app-mcp.seazone.com.br/mcp` | JWT Bearer |
| **Pipefy** | `https://app.pipefy.com/queries` | GraphQL |
| **Pipedrive** | `https://seazone-fd92b9.pipedrive.com/api/v1/` | API key |

Tabela canônica no Nekt:
```
nekt_operacional_silver.pipefy_szi_all_cards_transformada_bd_terreno
```

---

## Arquivos do projeto

```
app.py              # App Streamlit completo (4 abas + IA)
ai_client.py        # Cliente Claude API (análise de terrenos + chat)
nekt_client.py      # Cliente MCP Nekt (SQL via JWT)
nekt_auth.py        # OAuth PKCE para obter JWT
requirements.txt    # streamlit 1.57, pandas 2.3.3, plotly 6.7, anthropic
CLAUDE.md           # Documentação técnica completa
lessons.md          # Lições aprendidas e decisões técnicas
memory.md           # Estado atual, histórico e mapeamento de dados
.nekt_secrets       # JWT token local (não está no git)
```

---

## Secrets no Streamlit Cloud

```toml
NEKT_JWT_TOKEN = "eyJ..."       # JWT Nekt — válido até ~maio 2027
ANTHROPIC_API_KEY = "sk-ant-..." # Para as funcionalidades de IA
```

---

## Regras de negócio importantes

- **Score ≥ 320** = terreno qualificado (régua canônica)
- **Travado** = ≥ 15 dias na mesma fase → alerta vermelho
- **Gate AP** = interesse (1-5) + micro-score (1-10) define se terreno passa para Análise Preliminar
- **Backup** = terreno abaixo da régua, mantido para reabertura futura
- Link Pipefy: `https://app.pipefy.com/pipes/304543320#cards/{id_do_card}`

---

## Funil — 22 etapas

```
Não Iniciado → Falta Informação → Sem Zoneamento → Triagem → Análise Preliminar
→ Fila de EM → EM Iniciado → EM Análise de ROI → EM Relatório de Proposta → Pré Proposta → EM Finalizado
→ Fila de Análise Private → Análise Private Finalizada
→ Fila de EP → EP Iniciado → EP Orçamento Prévio → EP Revisão de ROI → Revisão Análise Private → EP Finalizado
→ [Perdido | Ganho | Excluídos]
```

---

## Armadilhas conhecidas

- `requests.text` usa Latin-1 → usar `r.content.decode("utf-8")` para evitar mojibake
- `pandas 2.x`: `.replace("", Series)` não funciona → usar `.loc[mask]`
- `LinkColumn` no Streamlit 1.57 não tem parâmetro `url=` → célula deve conter a URL diretamente
- `st.secrets` lança exceção em dev local → sempre usar try/except
- Nekt usa certificado auto-assinado → `verify=False` nos requests
- Nomes no campo `executivo_de_canais` do Pipefy nem sempre são pessoas → filtrar `LENGTH < 60` e rejeitar valores que começam com dígito

---

## Como rodar localmente

```bash
cd C:\Users\compu\Desktop\szi-painel-terrenos
pip install -r requirements.txt
streamlit run app.py
```

---

## Estado atual (10/06/2026)

- App deployado e funcionando com dados reais
- 56 terrenos no funil | VGV R$993,7M | 30 qualificados | 0 travados
- `NEKT_JWT_TOKEN` configurado no Streamlit Cloud ✅
- `ANTHROPIC_API_KEY` ainda não configurado — IA não funciona até ser adicionado ⚠️
