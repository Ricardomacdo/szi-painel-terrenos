# Memory — SZI Painel Terrenos

Registro de decisões, estado atual e histórico do projeto.

---

## Estado atual (10/06/2026 — atualizado em 10/06/2026)

### Deploy
- **URL pública:** https://szi-painel-terrenos-azp998z4x25rv9hcmoqm89.streamlit.app
- **Repositório:** https://github.com/Ricardomacdo/szi-painel-terrenos
- **Branch:** `master` · arquivo principal: `app.py`
- **Plataforma:** Streamlit Community Cloud
- **Conta:** ricardo.macedo@seazone.com.br / GitHub: ricardomacdo
- **Status:** Online e funcionando com dados reais do Nekt

### Dados reais confirmados (10/06/2026)
- 56 terrenos no funil
- VGV potencial: R$ 993,7M
- 30 qualificados (score ≥ 320)
- 3 com Falta de Informação
- 25 em Backup
- 0 travados (≥15 dias)

### Secrets configurados no Streamlit Cloud
- `NEKT_JWT_TOKEN` — JWT Nekt, válido até ~maio 2027 ✅
- `ANTHROPIC_API_KEY = sk-WFLxVCpL5vJZCbQgHKeB7Q` — gateway hub.seazone.dev ✅
- `ANTHROPIC_BASE_URL = https://hub.seazone.dev` — gateway IA interno Seazone ✅
- `PIPEFY_TOKEN` — API Pipefy (tool@seazone.com.br) ✅ (adicionar nos Secrets)

---

## Funcionalidades implementadas

### Painel (4 abas) — apenas terrenos Farmer (Ricardo Macedo)
1. **Dashboard** — KPIs, funil 22 etapas, score, mapa cidade/microrregião, tabela filtrada com link Pipefy
2. **Executivo de Canais** — visão Farmer com análise IA por analista
3. **Ficha do Terreno** — busca por ID ou nome, card completo + leitura de anexos Pipefy + análise IA
4. **Alertas** — travados ≥15d, falta info (campos específicos), sem matrícula, score baixo, cota acima do cap

### IA — gateway hub.seazone.dev
- Modelo: `minimax-m2.7` | Chave: `sk-WFLxVCpL5vJZCbQgHKeB7Q`
- SSL desativado (`httpx.Client(verify=False)`)
- **Plano do Dia** — ações urgentes + mensagens WhatsApp para corretor + oportunidades + saúde do funil
- **Análise IA por Executivo** — botão na aba Executivo de Canais para cada analista
- **Análise IA do Terreno** — botão na Ficha com dados reais do card
- **📎 Ler documentos do Pipefy** — baixa e extrai texto de PDFs/anexos; IA analisa inconsistências
- **Chat com contexto** — inclui resumo do funil atual em cada mensagem

### Verificação de Polígono (Pipefy)
- `pipefy_client.py` busca o campo `Poligono` (attachment) via GraphQL
- Mostra ✅/❌ com link direto para o arquivo no alerta de Falta Informação
- Campo `Matrícula` é select (Sim/Não/Não sabemos) — desconsiderado (não armazena metragem)

### Campos verificados na mensagem ao corretor (Falta Informação)
- Valor/Preço, Área (m²), Dimensões, Pasta de documentos, Triagem inicial
- **Removidos:** Zoneamento e Contato do proprietário (10/06/2026)

---

## Histórico de decisões

| Data | Decisão | Motivo |
|------|---------|--------|
| 27/05/2026 | Usar Nekt MCP como fonte de dados | Dados do Pipefy já estão na tabela `pipefy_szi_all_cards_transformada_bd_terreno` |
| 27/05/2026 | JWT Bearer token, não OAuth PKCE | PKCE é necessário para obter o JWT; após obtido, o JWT é suficiente para chamadas SQL |
| 28/05/2026 | Fallback para modo demo | App não pode quebrar — se Nekt falhar, exibe dados sintéticos |
| 28/05/2026 | verify=False nos requests | Nekt usa certificado auto-assinado |
| 10/06/2026 | ttl=0 no cache | Usuário quer dados atualizados a cada abertura |
| 10/06/2026 | Remover lessons.md e memory.md do .gitignore | Esses arquivos são documentação do projeto, não devem ir para o repo como arquivos internos ocultos |
| 10/06/2026 | Adicionar funcionalidades de IA | Feedback: painel precisava de IA fazendo algo além de listar cards |
| 10/06/2026 | Gateway hub.seazone.dev + minimax-m2.7 | Seazone tem proxy interno para LLMs; chave Anthropic direta não funciona |
| 10/06/2026 | Verificação de polígono via Pipefy API | Campo Polígono é attachment no Pipefy (não está no Nekt); busca direta via GraphQL |
| 10/06/2026 | Matrícula desconsiderada na análise | Campo é select (Sim/Não), não armazena metragem; documento fica no Google Drive |
| 10/06/2026 | Filtrar apenas terrenos Farmer | App é uso exclusivo do Ricardo (Farmer); Key Account removido da visão |
| 10/06/2026 | Plano do Dia IA substituiu análise genérica | IA agora retorna ações urgentes, mensagens prontas para corretor e oportunidades do dia |
| 10/06/2026 | Leitura de anexos Pipefy via pdfplumber | Botão "Ler documentos" baixa PDFs/anexos do card e extrai texto para análise IA |
| 10/06/2026 | Remover Zoneamento e Contato do proprietário da mensagem ao corretor | Esses campos não são responsabilidade do corretor informar |

---

## Equipe e mapeamento de analistas

| Nome no Nekt | Exibido no painel |
|---|---|
| Ricardo Macedo | Farmer |
| Gabriel Carlos Gouvea de Souza | Key Account |
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

Formato: `https://app.pipefy.com/pipes/304543320#cards/{id_do_card}`
- `id` exibido no painel = campo `ids` da tabela Nekt (sequencial)
- `id_do_card` = campo `id_do_card` da tabela Nekt (ID real do card no Pipefy)

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
