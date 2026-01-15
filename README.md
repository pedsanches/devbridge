# DevBridge

> **Making Technical Work Visible to Non-Technical Stakeholders via AI Translation**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude%203.5-blueviolet.svg)](https://www.anthropic.com)
[![Docs](https://img.shields.io/badge/docs-available-brightgreen.svg)](docs/index.md)

---

## 🎯 O Problema

Times de desenvolvimento fazem trabalho invisível (refactoring, arquitetura, dívida técnica) que stakeholders não conseguem entender ou valorizar.

**DevBridge traduz atividade técnica em valor de negócio** usando AI generativa com guardrails estritos. Agora com suporte nativo a métricas **DORA** e **SPACE**.

## ⚡ Quick Start

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/devbridge.git
cd devbridge

# Copie as variáveis de ambiente
cp .env.example .env

# Inicie a infraestrutura (inclui AI stack)
 docker-compose --profile ai up -d


# Configure o repositório a monitorar
curl -X POST http://localhost:8001/api/v1/repos \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/seu-usuario/seu-repo"}'
```

📚 **[Documentação Completa →](docs/index.md)**

## 🏗️ Arquitetura

```
GitHub Webhook → FastAPI → Redis Queue → Celery Worker
                                              ↓
                                    Tree-sitter (AST)
                                              ↓
                                    Presidio (Privacidade)
                                              ↓
                                    LangGraph Agent → Claude 3.5
                                              ↓
                              PostgreSQL + Qdrant → Chat/Slack
```

## 📊 Princípios

| Princípio | Implementação |
|-----------|---------------|
| **Zero Alucinação Financeira** | IA nunca inventa valores sem `.devbridge.yaml` |
| **Privacidade por Design** | Presidio sanitiza PII antes da LLM |
| **Saída Estruturada** | Pydantic valida todas as respostas |
| **Push over Pull** | Notificações proativas via Slack |

## 📖 Documentação

| Seção | Descrição |
|-------|-----------|
| [Quick Start](docs/getting-started/quick-start.md) | Setup em 5 minutos |
| [Arquitetura](docs/architecture/overview.md) | Visão técnica do sistema |
| [Regras de Negócio](docs/business/rules-catalog.md) | Catálogo de regras |
| [Contribuição](docs/development/contributing.md) | Como contribuir |
| [ADRs](docs/architecture/decisions/) | Decisões arquiteturais |
| [Contexto do Sistema](docs/system-context.md) | **Mapa mental para IA** |
| [Guia do Agente](docs/agent-guide.md) | Instruções para Agentes |

## 🛠️ Stack

- **Backend**: Python 3.11+, FastAPI, Celery
- **AI**: LangGraph, Claude 3.5 Sonnet, Instructor
- **Dados**: PostgreSQL, Qdrant, Redis
- **Privacidade**: Microsoft Presidio
- **Frontend**: Next.js 15, Vercel AI SDK

## 🤝 Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para começar.

## 📄 Licença

MIT - veja [LICENSE](LICENSE) para detalhes.
