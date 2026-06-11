# SZI Painel Terrenos
> Atualizado em 10/06/2026

Dashboard Streamlit para monitoramento do funil de terrenos da Seazone Investimentos — uso exclusivo do Farmer (Ricardo Macedo).

---

## Arquitetura

```
szi-painel-terrenos/
├── app.py              # Streamlit app (4 abas + IA)
├── nekt_client.py      # Cliente MCP para Nekt (data lake)
├── ai_client.py        # Cliente IA — gateway hub.seazone.dev (minimax-m2.7)
├── pipefy_client.py    # Cliente Pipefy GraphQL — documentos e leitura de anexos
├── nekt_auth.py        # OAuth PKCE para autenticar no Nekt
├── requirements.txt    # Dependências Python
├── .nekt_secrets       # Tokens locais (não commitear)
└── .streamlit/
    └── secrets.toml    # Configurações Streamlit Cloud
```

---

## Fontes de Dados

| Fonte | O que fornece | Endpoint |
|-------|---------------|----------|
| **Nekt MCP** | Dados reais dos cards Pipefy | `https://nekt-app-mcp.seazone.com.br/mcp` |
| **Pipefy GraphQL** | Documentos e anexos dos cards | `https://app.pipefy.com/queries` |
| **IA (minimax-m2.7)** | Análise de funil, terrenos e documentos | `https://hub.seazone.dev` |

### Tabela canônica Nekt
```sql
nekt_operacional_silver.pipefy_szi_all_cards_transformada_bd_terreno
```

---

## Deploy

- **URL pública:** `https://szi-painel-terrenos-azp998z4x25rv9hcmoqm89.streamlit.app`
- **Repositório:** `https://github.com/Ricardomacdo/szi-painel-terrenos` — branch `master`
- **Conta:** `ricardo.macedo@seazone.com.br` / GitHub: `Ricardomacdo`
- **Deploy:** automático a cada push para `master`

### Secrets necessários no Streamlit Cloud

```toml
NEKT_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."   # JWT Nekt — válido até ~maio 2027
ANTHROPIC_API_KEY = "sk-WFLxVCpL5vJZCbQgHKeB7Q"              # Gateway Seazone
ANTHROPIC_BASE_URL = "https://hub.seazone.dev"                # Gateway IA interno Seazone
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9..."                     # API Pipefy — tool@seazone.com.br
```

> Tokens completos salvos em `.nekt_secrets` na máquina local.

---

## Execução local

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Abas do Dashboard

### 1. Dashboard (`tab_dash`)
- KPIs: total no funil, VGV, qualificados, falta informação, backup, sem matrícula, travados
- Gráficos: funil 22 etapas, score, cidade/microrregião, executivo de canais
- Tabela com filtros e link para o Pipefy
- **🤖 Plano do Dia IA** — ao clicar "Gerar análise":
  - Ações urgentes (travados + falta info)
  - Mensagens WhatsApp prontas por corretor (campos faltantes: Valor, Área, Dimensões, Pasta docs, Triagem)
  - Oportunidades do dia (score ≥320 parados na triagem)
  - Saúde do funil + recomendação estratégica

### 2. Executivo de Canais (`tab_analistas`)
- Visão Farmer (Ricardo Macedo) com distribuição por fase + tabela
- Botão de análise IA por analista

### 3. Ficha do Terreno (`tab_ficha`)
- Busca por ID ou nome
- Card completo com localização, scores, financeiro, AP/EM/Private/EP
- **Analisar com IA** — avalia o terreno com dados cadastrados
- **📎 Ler documentos do Pipefy** — baixa todos os anexos do card, extrai texto de PDFs via pdfplumber, IA analisa inconsistências

### 4. Alertas (`tab_alertas`)
- Travados ≥15 dias
- Falta Informação com campos específicos faltantes por card + Polígono ✅/❌
- Sem matrícula, score abaixo da régua (320), cota acima do cap

---

## Filtro global — apenas Farmer

Logo após carregar os dados do Nekt, o app filtra automaticamente:
```python
df_raw = df_raw[df_raw["analista"] == "Farmer"].copy()
```
Todos os KPIs, gráficos, alertas e análises de IA refletem apenas a carteira do Ricardo.

---

## Campos verificados na mensagem ao corretor

Apenas: **Valor/Preço · Área (m²) · Dimensões · Pasta de documentos · Triagem inicial**
Removidos: Zoneamento e Contato do proprietário.

---

## Stack

| Pacote | Versão |
|--------|--------|
| streamlit | 1.57.0 |
| pandas | 2.3.3 |
| plotly | 6.7.0 |
| requests | 2.34.2 |
| anthropic | ≥ 0.20.0 |
| httpx | ≥ 0.24.0 |
| pdfplumber | ≥ 0.10.0 |

---

## Funil (22 etapas)

```
Entrada:  Não Iniciado → Falta Informação → Sem Zoneamento → Triagem de terrenos → Análise Preliminar
EM:       Fila de EM → EM Iniciado → EM Análise de ROI → EM Relatório de Proposta → Pré Proposta → EM Finalizado
Private:  Fila de Análise Private → Análise Private Finalizada
EP:       Fila de EP → EP Iniciado → EP Orçamento Prévio → EP Revisão de ROI → Revisão Análise Private → EP Finalizado
Saída:    Perdido | Ganho | Excluídos
```

---

## Conceitos importantes

| Termo | Definição |
|-------|-----------|
| **Score ≥ 320** | Terreno qualificado (régua canônica) |
| **Gate AP** | Regras passa/não-passa por interesse (1-5) e micro-score |
| **Backup** | Terreno abaixo da régua, mantido para reabertura |
| **EM** | Estudo de Massa (~1 dia em Revit) |
| **EP** | Estudo Preliminar (~2 dias) |
| **Private** | Validação pelos investidores garantidores |

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| "JWT token não configurado" | Verificar `.nekt_secrets` ou `NEKT_JWT_TOKEN` nos Secrets |
| Dados vazios / modo demo | JWT expirado — renovar via `python nekt_auth.py` |
| IA retorna erro 401 | Usar modelo `minimax-m2.7` e chave `sk-WFLxVCpL5vJZCbQgHKeB7Q` |
| "Invalid format: valid TOML" | Apagar tudo nos Secrets e colar os 4 de uma vez |
| Polígono não verificado | Adicionar `PIPEFY_TOKEN` nos Secrets do Streamlit Cloud |
| Documentos não carregam | `PIPEFY_TOKEN` ausente ou URL S3 expirada |
