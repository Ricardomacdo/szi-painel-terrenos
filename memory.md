# Memory — SZI Painel Terrenos

Registro de decisões, estado atual e histórico do projeto.

---

## Estado atual (10/06/2026)

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
- `ANTHROPIC_API_KEY` — necessário para funcionalidades de IA ⚠️ (ainda não configurado)

---

## Funcionalidades implementadas

### Painel (4 abas)
1. **Dashboard** — KPIs, funil 22 etapas, score, mapa cidade/microrregião, tabela filtrada com link Pipefy
2. **Executivo de Canais** — breakdown Farmer (Ricardo) / Key Account (Gabriel)
3. **Ficha do Terreno** — busca por ID ou nome, card completo com AP/EM/Private/EP
4. **Alertas** — travados ≥15d, falta info, sem matrícula, score baixo, cota acima do cap

### IA (requer ANTHROPIC_API_KEY)
- **Análise IA do Funil** — botão no Dashboard que envia estado real do funil ao Claude e retorna pontos de atenção urgentes
- **Análise IA do Terreno** — botão na Ficha que avalia um terreno específico (vale prosseguir? riscos? próximos passos?)
- **Chat com contexto** — chat assistente que inclui resumo do funil atual em cada mensagem

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
