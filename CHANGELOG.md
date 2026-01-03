# Changelog

Todas as mudanças notáveis serão documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- Autenticação via Magic Links (ADR-007)
- Modelo de dados Multi-tenant (Organization, Team, Membership) (ADR-006)
- Pipeline RAG com Qdrant e OpenAI embeddings
- Busca semântica com filtro por tenant
- Estrutura inicial de documentação
- README modernizado com badges e quick start
- Catálogo de regras de negócio
- ADRs para decisões arquiteturais

### Changed
- (nenhuma mudança ainda)

### Fixed
- (nenhum fix ainda)

### Security
- Implementação de sessão com httpOnly cookies

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
