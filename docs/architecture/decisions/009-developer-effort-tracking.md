# ADR-009: Estratégia de Rastreamento de Esforço do Desenvolvedor

**Status:** Aceito
**Data:** 2026-01-09
**Deciders:** Product & Engineering Team

## Contexto

O DevBridge precisa evoluir sua capacidade de analisar a produtividade e a qualidade do desenvolvimento. Anteriormente, o sistema rastreava apenas atividades básicas como Commits e Pull Requests de forma isolada. Para fornecer insights valiosos para gestores e times técnicos, é necessário adotar frameworks de métricas validados pela indústria.

Os frameworks escolhidos foram:
1.  **DORA (DevOps Research and Assessment)**: Focado em velocidade e estabilidade de entrega (nível de time).
2.  **SPACE (Satisfaction, Performance, Activity, Communication, Efficiency)**: Uma visão holística da produtividade do desenvolvedor (nível individual e time).

## Decisão

Implementar um sistema abrangente de coleta e processamento de métricas, dividido em 5 fases, integrando dados do GitHub com análise de IA.

### 1. Métricas Coletadas

#### Métricas de Código (Activity)
Expandimos a coleta de dados de atividades para incluir:
- **Volume**: Linhas adicionadas `lines_added`, removidas `lines_deleted` e arquivos alterados.
- **Ciclo de Vida de PR**: `first_review_at`, `approved_at`, `merged_at`.
- **Tempos Calculados**:
    - *Pickup Time*: Tempo até o primeiro review.
    - *Review Time*: Tempo do primeiro review até a aprovação.
    - *Merge Time*: Tempo da aprovação até o merge.
    - *Cycle Time*: Tempo total (criação até merge).

#### Métricas de Issues
Integração completa com Github Issues para rastrear:
- Status e ciclo de vida (`opened_at` a `closed_at`).
- `time_to_close_hours`.
- Vinculação automática com PRs.

#### Métricas de Code Review
Rastreamento detalhado da qualidade do code review:
- Engajamento do revisor (comentários, aprovações).
- Tempo de resposta.
- Identificação de reviews superficiais vs. profundos.

#### Métricas de Time (DORA)
Cálculo automático das 4 métricas chave do DORA:
1.  **Deployment Frequency**: Frequência de merges na branch principal.
2.  **Lead Time for Changes**: Tempo médio do commit até o deploy (merge).
3.  **Change Failure Rate**: Taxa de PRs/deploys revertidos ou com falha.
4.  **Mean Time to Recovery (MTTR)**: Tempo médio para correção de falhas.

#### Perfil do Desenvolvedor (SPACE)
Agregação de dados por desenvolvedor (`DeveloperProfile`):
- **Activity**: Commits, PRs, Reviews.
- **Efficiency**: Tempos médios de merge e review.
- **Communication**: Colaboração em reviews.
- **Insights de IA**: Tags de força técnica (ex: "frontend", "security") e score de colaboração.

### 2. Mudanças na Arquitetura

#### Novos Modelos de Dados
- `Issue`: Rastreamento de tarefas e bugs.
- `CodeReview`: Rastreamento de revisões de código.
- `DeveloperProfile`: Métricas agregadas por dev.
- `ContributorStats`: Snapshots semanais de atividade.
- `TeamMetrics`: Métricas DORA agregadas por período.

#### Novos Serviços
- **MetricsService**: Responsável pela lógica de cálculo das métricas DORA e agregações de perfil.
- **AIService (Extensão)**: Novos métodos para análise de _expertise_ técnica (`analyze_developer_strengths`) e pontuação de colaboração.
- **SyncService (Extensão)**: Suporte para sincronização de Issues, Reviews de PR e estatísticas de contribuidores.

## Consequências

### Positivas
- **Visibilidade**: Gestores têm visão clara da velocidade e qualidade do time.
- **Insights Acionáveis**: Identificação de gargalos no processo de review e merge.
- **Reconhecimento**: Perfis de desenvolvedor destacam áreas de especialidade e esforço não visível (ex: reviews).
- **Alinhamento com Mercado**: Uso de métricas padrão (DORA/SPACE) facilita benchmarking.

### Negativas / Riscos
- **Privacidade**: As métricas individuais devem ser usadas com cuidado para evitar microgerenciamento. O foco deve ser no autodesenvolvimento e saúde do time.
- **Complexidade de Sync**: A sincronização de dados adicionais (reviews, issues) aumenta o consumo da API do GitHub e o tempo de processamento.
- **Volume de Dados**: As tabelas de métricas podem crescer rapidamente em organizações grandes.

## Status da Implementação

Todas as fases propostas foram implementadas:
- [x] Fase 1: Code Metrics & PR Lifecycle
- [x] Fase 2: Issue Tracking
- [x] Fase 3: Code Reviews
- [x] Fase 4: Developer Profiles & Aggregations
- [x] Fase 5: Team Metrics (DORA) & AI Analysis
