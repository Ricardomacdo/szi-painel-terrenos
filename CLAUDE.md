# SZI Painel Terrenos

Dashboard Streamlit para monitoramento do funil de terrenos da Seazone Investimentos.

## O que é

Painel de BI que exibe todos os cards do Pipefy (funil SZI Terrenos, 22 etapas) com:
- Dashboard com métricas, gráficos e tabela filtrada
- Visão por Executivo de Canais
- Ficha individual de terreno
- Alertas automáticos (travados, falta info, score baixo, docs faltando)

## Arquitetura

```
szi-painel-terrenos/
├── app.py              # Streamlit app (4 abas)
├── nekt_client.py      # Cliente MCP para Nekt (data lake)
├── nekt_auth.py        # OAuth PKCE para autenticar no Nekt
├── requirements.txt    # Dependências Python
├── .nekt_secrets       # JWT token (não commitear)
└── .streamlit/
    └── secrets.toml   # Configurações Streamlit Cloud
```

## Fontes de Dados

| Fonte | O que fornece | API/Endpoint |
|-------|---------------|--------------|
| **Nekt MCP** | Dados reais dos cards Pipefy | `https://nekt-app-mcp.seazone.com.br/mcp` |
| **Pipefy** | Cards do funil (backup direto) | `https://app.pipefy.com/queries` |
| **Pipedrive** | Corretores e deals | `https://seazone-fd92b9.pipedrive.com/api/v1/` |

### Nekt MCP Protocol

O Nekt usa MCP (Model Context Protocol) com:
- `initialize` → retorna `mcp-session-id` no header
- `tools/call` com `execute_sql` → executa SQL no Athena/BigQuery

O JWT é carregado de (ordem de prioridade):
1. Variável de ambiente `NEKT_JWT_TOKEN`
2. Arquivo `.nekt_secrets` (formato JSON com `jwt_token`)
3. Streamlit secrets (`st.secrets`)

### Tabela canônica

```sql
nekt_operacional_silver.pipefy_szi_all_cards_transformada_bd_terreno
```

Contém todos os campos do funil: etapa, scores, VGV, ROI, datas, etc.

## Configuração

### 1. Autenticação Nekt

```bash
python nekt_auth.py
```

Isso abre o browser para OAuth, salva o token em `nekt_token.json`, e você copia o JWT para `.nekt_secrets`:

```json
{"jwt_token": "eyJ..."}
```

### 2. Variáveis de ambiente (opcional)

```bash
export NEKT_JWT_TOKEN="eyJ..."
```

### 3. Streamlit Cloud

Adicionar no Secrets do Streamlit Cloud:
```toml
NEKT_JWT_TOKEN = "eyJ..."
```

## Execução local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Ou usar o script `rodar.bat` no Windows.

## Abas do Dashboard

### 1. Dashboard (`tab_dash`)
- Métricas: total no funil, VGV, qualificados, falta informação, backup, sem matrícula, travados
- Gráficos: funil, score, cidade/microrregião, executivo de canais
- Tabela com filtros e link para o Pipefy

### 2. Executivo de Canais (`tab_analistas`)
- Visão individual por analista (Ricardo, Gabriel)
- Distribuição por fase + tabela de terrenos

### 3. Ficha do Terreno (`tab_ficha`)
- Busca por ID ou nome
- Card detalhado com localização, scores, financeiro, documentos, AP, EM, Private, EP

### 4. Alertas (`tab_alertas`)
- Terrenos travados ≥15 dias
- Falta Informação
- Sem matrícula
- Score abaixo da régua (320)
- Cota acima do cap
- Documentos faltando/divergentes

## Conceitos importantes

| Termo | Definição |
|-------|-----------|
| **Score ≥ 320** | Terreno qualificado (régua canônica) |
| **Gate AP** | Regras de passam/não passam por interesse (1-5) e micro-score |
| **Backup** | Terreno abaixo da régua, mantido para reabertura |
| **EM** | Estudo de Massa (~1 dia em Revit) |
| **EP** | Estudo Preliminar (~2 dias) |
| **Private** | Validação pelos investidores garantidores |

## Funil (22 etapas)

```
Entrada: Não Iniciado → Falta Informação → Sem Zoneamento
Triagem: Triagem de terrenos → Análise Preliminar
EM: Fila de EM → EM Iniciado → EM Análise de ROI → EM Relatório de Proposta → Pré Proposta → EM Finalizado
Private: Fila de Análise Private → Análise Private Finalizada
EP: Fila de EP → EP Iniciado → EP Orçamento Prévio → EP Revisão de ROI → Revisão Análise Private → EP Finalizado
Saída: Perdido / Ganho / Excluídos
```

## Desenvolvimento

### Estrutura de dados (Nekt → DataFrame)

O `fetch_nekt_data()` normaliza os dados do Nekt para colunas do painel:
- `id`, `terreno`, `cidade`, `microrregiao`
- `score`, `score_micro`, `interesse`
- `vgv`, `preco`, `area_m2`, `roi_est`
- `analista`, `corretor`
- `fase_atual`, `status`, `dias_na_fase`
- `_ap`, `_em`, `_private`, `_ep`, `_docs` (dicts aninhados)

### Dados demo

`demo_data()` gera ~200 terrenos sintéticos para teste quando o Nekt não está disponível.

## Deploy

### Streamlit Cloud

1. Push para GitHub (repo `szi-painel-terrenos`)
2. Conectar no [Streamlit Cloud](https://streamlit.io/cloud)
3. Adicionar secrets: `NEKT_JWT_TOKEN`
4. Deploy automático em push para main

### URL pública (produção)

`https://szi-painel-terrenos-azp998z4x25rv9hcmoqm89.streamlit.app`

### Repositório GitHub

`https://github.com/Ricardomacdo/szi-painel-terrenos` — branch `master`, arquivo `app.py`

### Secrets necessários no Streamlit Cloud

```toml
NEKT_JWT_TOKEN = "eyJ..."       # JWT Nekt — válido até ~maio 2027
ANTHROPIC_API_KEY = "sk-ant-..." # Necessário para as funcionalidades de IA
```

## Troubleshooting

### "JWT token não configurado"
- Verificar `.nekt_secrets` existe e tem `jwt_token`
- Ou configurar `NEKT_JWT_TOKEN` como variável de ambiente
- Ou adicionar no Streamlit secrets

### "Conectado (session: None...)"
- O Nekt MCP retorna session ID no header `mcp-session-id`
- Se vazio, a sessão ainda funciona (stateless)
- Verificar se o JWT está válido

### Dados vazios do Nekt
- O app cai para modo demonstração automaticamente
- Verificar se a tabela `pipefy_szi_all_cards_transformada_bd_terreno` existe
- Testar query diretamente no Nekt

### Erro de CORS ou SSL
- `verify=False` está configurado nos requests (necessário para o Nekt)
- Se o Nekt deployar com SSL válido, remover essa flag
