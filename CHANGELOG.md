# Changelog

Todas as mudanças notáveis serão documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added

#### 📈 Developer Metrics & Tracking (ADR-009)
- **Code Metrics**: Rastreamento de linhas adicionadas/removidas, arquivos alterados e complexidade.
- **PR Lifecycle**: Métricas detalhadas de tempo (Pickup, Review, Merge, Cycle Time).
- **Quality**: Classificação de reviews (Superficial vs Profundo) e métricas de rejeição.
- **Issue Tracking**: Sincronização e métricas de Issues e vinculação com PRs.
- **DORA Metrics**: Cálculo automático de Deployment Frequency, Lead Time, Change Failure Rate e MTTR.
- **Developer Profiles**: Agregação de dados por desenvolvedor com análise de IA (pontos fortes, colaboração).
- **SPACE Framework**: Suporte a métricas holísticas de produtividade.

#### 📊 Sistema de Reports
- Sistema completo de geração de relatórios por persona (PM, CTO, CEO)
- Templates de report reutilizáveis com configuração dinâmica
- Export de reports em PDF
- UI de gerenciamento de templates (criar, editar, deletar)
- Histórico de reports gerados com re-download

#### 💬 Chat & RAG
- Interface de chat com IA integrada ao contexto de repositórios
- Seletor de repositórios múltiplos para contexto de conversas
- Context enrichment com sources transparency (mostra de onde vem a informação)
- Persistência de conversas e histórico de chat
- Suporte a markdown nas respostas

#### 🤖 AI-Powered Features
- Geração automática de Business Updates via IA durante sync
- Value Tagging: classificação automática de atividades (feature, refactor, bugfix, etc.)
- Endpoint manual para gerar Business Updates sob demanda

#### 🎨 UI/UX
- **Dark Mode** com theming semântico
- Dashboard redesenhado com cards e métricas visuais
- Badges de Value Tags nas atividades
- Página de login polida com visual moderno
- Home page com estética melhorada

#### 🔄 Sincronização
- Sincronização real de repositórios via GitHub API
- Extração de metadados enriquecidos (files, labels, issues)
- Campo `occurred_at` para datas reais de commit
- Tratamento de timeouts e diffs grandes

#### ⚙️ Infraestrutura
- Organization Settings com integração MCP
- Criptografia de tokens GitHub (Fernet)
- Campo `last_synced_at` exposto na API
- Autenticação via Magic Links (ADR-007)
- Modelo de dados Multi-tenant (Organization, Team, Membership) (ADR-006)
- Pipeline RAG com Qdrant e OpenAI embeddings
- Busca semântica com filtro por tenant
- ADRs para decisões arquiteturais

### Changed
- Dashboard melhorado com visualização de dados aprimorada
- Schemas de Activity e Chat padronizados
- Catálogo de regras de negócio atualizado

### Fixed
- Visibilidade de Business Updates no dashboard
- Persistência de mensagens de chat
- Propagação correta de Organization ID durante sync
- Validações de rotas de usuário no backend

### Security
- Implementação de sessão com httpOnly cookies
- Tokens GitHub criptografados antes de armazenar

---

## [0.1.0] - 2025-01-XX

### Added
- Setup inicial do projeto
- Integração com GitHub webhooks
- Pipeline de ingestão básico
- Sanitização de PII com Presidio
- Parsing AST com Tree-sitter
- Estrutura de documentação

[Unreleased]: https://github.com/seu-usuario/devbridge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/seu-usuario/devbridge/releases/tag/v0.1.0
