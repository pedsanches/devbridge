# DevBridge Documentation

Bem-vindo à documentação do DevBridge! 🎉

## 🚀 Começando

| Documento | Descrição |
|-----------|-----------|
| [Quick Start](getting-started/quick-start.md) | Setup em 5 minutos |
| [Instalação](getting-started/installation.md) | Instalação detalhada |
| [Configuração](getting-started/configuration.md) | Variáveis de ambiente |

## 🏗️ Arquitetura

| Documento | Descrição |
|-----------|-----------|
| [Visão Geral](architecture/overview.md) | Arquitetura do sistema |
| [Fluxo de Dados](architecture/data-flow.md) | Como os dados fluem |
| [Decisões (ADRs)](architecture/decisions/) | Registro de decisões arquiteturais |

## 📋 Negócio

| Documento | Descrição |
|-----------|-----------|
| [Regras de Negócio](business/rules-catalog.md) | Catálogo completo de regras |
| [Glossário](business/glossary.md) | Definição de termos |
| [Personas](business/personas.md) | Perfis de usuário |
| [User Stories](business/user-stories.md) | Histórias de Usuário |

## 💻 Desenvolvimento

| Documento | Descrição |
|-----------|-----------|
| [Contribuição](development/contributing.md) | Como contribuir |
| [Padrões de Código](development/code-style.md) | Style guide |
| [Testes](development/testing.md) | Estratégia de testes |
| [API Reference](development/api-reference.md) | Documentação da API |
| [**Guia de Debug**](development/debug-guide.md) | **Fluxos de diagnóstico de erros** |
| [**Códigos de Erro**](development/error-codes.md) | **Catálogo completo de erros** |
| [**Logging Checklist**](development/logging-checklist.md) | **Padrões de logging estruturado** |

## 🔧 Operações

| Documento | Descrição |
|-----------|-----------|
| [Deploy](operations/deployment.md) | Guia de implantação |
| [Monitoring](operations/monitoring.md) | Observabilidade |
| [Runbook](operations/runbook.md) | Procedimentos operacionais |

## 🤖 Features Principais

### Chat com IA
O DevBridge oferece um **chat inteligente** que usa RAG (Retrieval-Augmented Generation) para responder perguntas sobre suas atividades de desenvolvimento:
- Contexto multi-repositório
- Histórico de conversas persistente
- Transparência de fontes (mostra de onde vem a informação)

### Reports Estruturados
Sistema de geração de **relatórios por persona** ([ADR-008](architecture/decisions/008-reports-system.md)):
- **Resumo Semanal** (PM): Entregas e progresso
- **Relatório Técnico** (CTO): Métricas e decisões arquiteturais
- **Resumo Executivo** (CEO): Máx 5 bullets, zero jargão
- Templates reutilizáveis
- Export em PDF

### Business Updates
Geração automática de **análises de impacto de negócio** para cada atividade técnica:
- Value Tagging (feature, refactor, bugfix, etc.)
- Tradução automática de commits para linguagem de negócio
- Integrado ao processo de sync

### Métricas de Time e Desenvolvedor
Rastreamento avançado de produtividade e qualidade ([ADR-009](architecture/decisions/009-developer-effort-tracking.md)):
- **DORA Metrics**: Deployment Frequency, Lead Time, Change Failure Rate, MTTR.
- **SPACE Framework**: Análise holística de produtividade.
- **Developer Profiles**: Insights individuais, tags de força técnica e colaboração.
- **Ciclo de Vida de PR**: Métricas detalhadas de review, merge e qualidade.

## 🔌 Integrações

| Integração | Descrição |
|------------|-----------|
| [MCP Toolbox](operations/mcp-integration.md) | Acesso DB para agentes IA |
| GitHub | Webhooks e sync de repositórios |
| Qdrant | Banco vetorial para RAG |
| OpenAI GPT-4o | LLM para processamento |
| Resend | Envio de emails (Magic Link) |

---

## Navegação Rápida por Perfil

### Sou um **novo desenvolvedor** 👨‍💻
1. [Quick Start](getting-started/quick-start.md)
2. [Padrões de Código](development/code-style.md)
3. [Contribuição](development/contributing.md)

### Sou um **arquiteto** 🏛️
1. [Visão Geral](architecture/overview.md)
2. [ADRs](architecture/decisions/)
3. [Regras de Negócio](business/rules-catalog.md)

### Sou de **operações** 🔧
1. [Deploy](operations/deployment.md)
2. [Monitoring](operations/monitoring.md)
3. [Runbook](operations/runbook.md)

### Sou um **stakeholder** 📊
1. [Glossário](business/glossary.md)
2. [Personas](business/personas.md)
3. [Regras de Negócio](business/rules-catalog.md)

### Sou um **agente de IA** 🤖
1. [AGENTS.md](../AGENTS.md) - **Sempre leia primeiro**
2. [Guia de Debug](development/debug-guide.md) - **Como resolver erros**
3. [Códigos de Erro](development/error-codes.md) - Catálogo de erros
4. [Logging Checklist](development/logging-checklist.md) - Padrões de logging
5. [Padrões de Código](development/code-style.md) - Style guide
