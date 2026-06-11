# Memory — SZI Painel Terrenos
> Atualizado em 10/06/2026

---

## Estado atual (10/06/2026)

### Deploy
- **URL pública:** https://szi-painel-terrenos-azp998z4x25rv9hcmoqm89.streamlit.app
- **Repositório:** https://github.com/Ricardomacdo/szi-painel-terrenos
- **Branch:** `master` · arquivo principal: `app.py`
- **Plataforma:** Streamlit Community Cloud
- **Conta:** ricardo.macedo@seazone.com.br / GitHub: Ricardomacdo
- **Status:** Online, dados reais do Nekt, IA funcionando

### Secrets configurados no Streamlit Cloud
- `NEKT_JWT_TOKEN` — JWT Nekt, válido até ~maio 2027 ✅
- `ANTHROPIC_API_KEY = sk-WFLxVCpL5vJZCbQgHKeB7Q` ✅
- `ANTHROPIC_BASE_URL = https://hub.seazone.dev` ✅
- `PIPEFY_TOKEN` — API Pipefy (tool@seazone.com.br) ✅

---

## Funcionalidades implementadas (10/06/2026)

### Painel — apenas terrenos Farmer (Ricardo Macedo)
Filtro global aplicado logo após carregar df_raw:
```python
df_raw = df_raw[df_raw["analista"] == "Farmer"].copy()
```

### 4 abas
1. **Dashboard** — KPIs, funil, score, tabela + **🤖 Plano do Dia IA**
2. **Executivo de Canais** — visão Farmer + análise IA por analista
3. **Ficha do Terreno** — card completo + Analisar com IA + 📎 Ler documentos Pipefy
4. **Alertas** — travados, falta info (campos específicos), score baixo, cota, polígono ✅/❌

### 🤖 Plano do Dia IA (Dashboard)
Botão "Gerar análise" envia contexto real e retorna:
- **Ações urgentes** — travados + falta info
- **Mensagens WhatsApp prontas** — por corretor, campos específicos faltantes
- **Oportunidades do dia** — score ≥320 parados na triagem
- **Saúde do funil** — avaliação + recomendação estratégica

### 📎 Ler documentos do Pipefy (Ficha do Terreno)
- Busca todos os campos tipo `attachment` do card via GraphQL
- Baixa arquivos (PDFs via pdfplumber, texto, imagens)
- Extrai texto e passa para IA analisar inconsistências

### Campos verificados na mensagem ao corretor
✅ Valor/Preço · Área (m²) · Dimensões · Pasta de documentos · Triagem inicial
❌ Removidos: Zoneamento · Contato do proprietário

---

## Histórico de decisões — 10/06/2026

| Decisão | Motivo |
|---------|--------|
| ttl=0 no cache | Dados frescos a cada abertura do app |
| Gateway hub.seazone.dev + minimax-m2.7 | Chave Anthropic direta não funciona; Seazone tem proxy interno |
| httpx no requirements.txt | SDK anthropic usa httpx — faltava como dependência |
| pdfplumber no requirements.txt | Leitura de PDFs nos anexos do Pipefy |
| Filtrar apenas terrenos Farmer | App é uso exclusivo do Ricardo; Key Account removido |
| Plano do Dia IA substituiu análise genérica | IA agora retorna ações práticas e mensagens prontas |
| Leitura de anexos Pipefy | Botão baixa e extrai texto de PDFs/docs do card |
| Remover Zoneamento e Contato do proprietário | Não são campos de responsabilidade do corretor |
| Matrícula desconsiderada | Campo é select (Sim/Não), não armazena metragem |
| Verificação de polígono via Pipefy API | Campo Polígono é attachment no Pipefy, não está no Nekt |

---

## Equipe e mapeamento de analistas

| Nome no Nekt | Exibido no painel |
|---|---|
| Ricardo Macedo | Farmer (único exibido) |
| Gabriel Carlos Gouvea de Souza | Key Account (removido da visão) |
| Davi Millan | excluído |
| Eduardo Farias | excluído |

---

## Funil — 22 etapas

```
Entrada:  Não Iniciado → Falta Informação → Sem Zoneamento → Triagem de terrenos → Análise Preliminar
EM:       Fila de EM → EM Iniciado → EM Análise de ROI → EM Relatório de Proposta → Pré Proposta → EM Finalizado
Private:  Fila de Análise Private → Análise Private Finalizada
EP:       Fila de EP → EP Iniciado → EP Orçamento Prévio → EP Revisão de ROI → Revisão Análise Private → EP Finalizado
Saída:    Perdido | Ganho | Excluídos
```

---

## Link para o Pipefy

`https://app.pipefy.com/pipes/304543320#cards/{id_do_card}`
- `id` exibido no painel = campo `ids` (sequencial)
- `id_do_card` = campo `id_do_card` da tabela Nekt (ID real no Pipefy)

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
