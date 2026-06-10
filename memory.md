---
name: szi-painel-terrenos
description: Dashboard Streamlit para monitoramento do funil SZI Terrenos — lê do Nekt MCP, exibe dashboards, fichas e alertas
metadata:
  type: project
---

# SZI Painel Terrenos

## Status
- **Criado**:2026-05-27
- **Deploy**: Pendente (precisa push para GitHub e configurar no Streamlit Cloud)
- **URL esperada**: `https://szi-painel-terrenos.streamlit.app`

## Origem
- Subtarefa do projeto maior de "Motor de Análise Automática" (discovery02/04/2026)
- Objetivo: criar painel de BI para visualizar dados do funil sem depender de exportação manual

## Funcionalidades implementadas
1. Dashboard com métricas e gráficos (funil, score, cidade, analista)
2. Visão por Executivo de Canais (Ricardo, Gabriel)
3. Ficha individual de terreno com todos os detalhes
4. Alertas automáticos (travados, falta info, docs)

## Dados
- **Fonte primária**: Nekt MCP (`nekt-app-mcp.seazone.com.br/mcp`)
- **Tabela**: `nekt_operacional_silver.pipefy_szi_all_cards_transformada_bd_terreno`
- **Fallback**: Pipefy API direto + modo demonstração

## Pendências
- [ ] Testar URL do Nekt MCP em produção
- [ ] Deploy no Streamlit Cloud
- [ ] Configurar secrets no Streamlit Cloud
- [ ] Testar autenticação OAuth com JWT válido
- [ ] Validar dados reais vs demo

## Autores
- Desenvolvimento: Claude Code (agente)
- Dono do projeto: Ricardo (Analista de Prospecção)

## Relacionado
- [[seazone-terrenos-contexto]] — contexto de negócio completo do setor
- [[szi-painel-terrenos-deploy]] — quando criar, trackar status do deploy
