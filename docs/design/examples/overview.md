# Exemplo Canônico: Overview Dashboard

## 🎯 Objetivo
Esta é a "Home" do projeto/repositório. Deve dar ao CTO/Stakeholder a resposta imediata para: **"Como está a saúde do projeto hoje?"**

## ❓ Perguntas Respondidas
- O time está entregando? (Velocity/Cycle Time)
- O código está piorando? (Technical Debt/Complexity)
- Existe algum incêndio ativo? (Security/Bugs)

## 🏗️ Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  [Header: Repo Name + Branch + Date Picker ]     [Settings] │
├──────┬──────────────────────────────────────────────────────┤
│ SIDE │  [ Hero Metrics Row: 4 Cards ]                       │
│ BAR  │  1. Cycle Time (3d) 2. Deploy Freq (2/d) ...         │
│      ├───────────────────────────┬──────────────────────────┤
│      │  [ Activity Feed ]        │  [ AI Insights ]         │
│      │  Title: Recent Activity   │  Title: Weekly Digest    │
│      │                           │                          │
│      │  - [User] pushed 3 commits│  [InsightCard]           │
│      │  - [Bot] merged PR #123   │  "Refactor Opportunity"  │
│      │  - [User] opened Issue    │  High Confidence         │
│      │                           │  [Actions]               │
│      │                           │                          │
│      └───────────────────────────┴──────────────────────────┘
```

## ✅ Seções Obrigatórias
1.  **KPIs de Topo**: Máximo 4 métricas críticas (DORA metrics).
2.  **AI Highlights**: O que a IA descobriu que requer atenção humana (não apenas logs).
3.  **Recent Activity**: Para dar sensação de pulso/vivo.

## 🚦 Estados
- **Empty (Day 0)**: "Conecte o repositório para começar a ver métricas. [Setup Guide]"
- **Loading**: Skeletons nos cards de métricas. Activity feed com shimmer.
- **Error**: "Falha ao sincronizar GitHub. [Retry]" nos cards afetados.

## 🚫 Don't Do This
- Não mostre gráficos vazios "Flatline" se não houver dados. Mostre Empty State.
- Não misture alertas críticos com "bom dia" ou mensagens irrelevantes no feed da IA.
