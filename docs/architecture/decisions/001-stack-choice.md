# ADR-001: Escolha de Stack Tecnológica

**Data:** 2025-01-01

**Status:** Accepted

**Deciders:** Pedro (Tech Lead)

## Contexto

O DevBridge precisa de uma stack que suporte:
- Processamento assíncrono de webhooks em escala
- Integração profunda com LLMs e ferramentas de AI
- Parsing de código fonte (AST)
- Busca semântica vetorial
- Interface de chat em tempo real

O time tem experiência predominante em Python e TypeScript.

## Decisão

> Usaremos **Python 3.11+ com FastAPI** para o backend e **Next.js 15** para o frontend.

### Stack Completa

| Camada | Tecnologia |
|--------|------------|
| API | FastAPI |
| Task Queue | Celery + Redis |
| AI Orchestration | LangGraph |
| LLM | Claude 3.5 Sonnet (Anthropic) |
| Schema Validation | Instructor + Pydantic |
| Parsing | Tree-sitter |
| Privacy | Microsoft Presidio |
| Vector DB | Qdrant |
| Relational DB | PostgreSQL |
| Frontend | Next.js 15 |

## Alternativas Consideradas

### Alternativa A: Node.js/TypeScript Full-Stack

- **Prós:** Única linguagem, ecossistema npm
- **Contras:** 
  - Menos bibliotecas maduras para AI/ML
  - Tree-sitter bindings menos estáveis
  - LangGraph não tem port oficial
- **Por que descartada:** Ecossistema Python é significativamente mais maduro para AI

### Alternativa B: Go Backend

- **Prós:** Performance superior, binários simples
- **Contras:**
  - Sem LangGraph
  - Menos bibliotecas de AI
  - Curva de aprendizado para o time
- **Por que descartada:** Produtividade menor e menos tooling de AI

## Consequências

### Positivas
- Acesso a todo ecossistema Python de AI (LangChain, LangGraph, Instructor)
- FastAPI oferece async nativo e documentação automática
- Pydantic integra perfeitamente com Instructor
- Time já conhece Python

### Negativas
- Duas linguagens no projeto (Python + TypeScript)
- Python mais lento que Go/Rust para CPU-bound tasks
- Deploy de Python requer mais cuidado (virtualenvs, dependências)

### Neutras
- Necessidade de manter dois package managers (Poetry + pnpm)

## Notas de Implementação

- Usar **Poetry** para gerenciar dependências Python
- Usar **Ruff** para linting (substituindo black, isort, flake8)
- Manter Python 3.11+ para melhor performance de async
- Usar **pnpm** para frontend (mais rápido que npm)

## Links Relacionados

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Instructor](https://instructor-ai.github.io/instructor/)
