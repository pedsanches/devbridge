# ADR-010: Data Sources Organization with Teams

## Status

**Accepted** - 2026-01-11

## Context

O DevBridge conecta repositórios GitHub dos usuários, mas não tinha um conceito de agrupamento lógico. Isso causava problemas:

1. **Relatórios desorganizados**: Por padrão, relatórios puxavam TODOS os repositórios acessíveis pelo usuário
2. **Chat sem contexto**: Não havia forma fácil de filtrar por "projeto" ou "produto"
3. **Ruído excessivo**: Desenvolvedores com 50+ repos tinham dificuldade em focar no que importa

### Análise Competitiva

Pesquisamos 6 ferramentas de developer analytics:

| Ferramenta | Conceito Principal | Insight |
|------------|-------------------|---------|
| **LinearB** | Service (múltiplos repos) | Bom para monorepos |
| **Jellyfish** | Team hierárquico | Org → Division → Team |
| **Swarmia** | Team (sync GitHub) | Auto-import de GitHub Teams |
| **Sleuth** | Project (deploy-based) | Foco em DORA |
| **Waydev** | Group (repo+team+board) | Mais parecido com nossa necessidade |
| **Pluralsight Flow** | Team Health | Foco em produtividade |

## Decision

Implementar o conceito de **Team** como unidade de organização de fontes de dados.

### Modelo de Dados

```
Organization
└── Team "Squad Pagamentos"
    ├── Repositories: [payments-api, checkout-web]
    └── Membros: auto-detectados via commits

└── Team "Infra"
    ├── Repositories: [terraform-prod, k8s-configs]
    └── Membros: auto-detectados
```

### Características

1. **Many-to-many**: Um repositório pode pertencer a múltiplos teams
2. **Team default**: Criado automaticamente no onboarding ("Meus Repositórios")
3. **GitHub Teams sync**: Suporte futuro para importar estrutura do GitHub
4. **Cores personalizáveis**: Para diferenciação visual na UI

### API Endpoints

```
GET    /api/v1/teams              # Listar times
POST   /api/v1/teams              # Criar time
GET    /api/v1/teams/{id}         # Detalhes do time
PATCH  /api/v1/teams/{id}         # Atualizar time
DELETE /api/v1/teams/{id}         # Deletar time
POST   /api/v1/teams/{id}/repositories     # Adicionar repos
DELETE /api/v1/teams/{id}/repositories     # Remover repos
GET    /api/v1/teams/default      # Time padrão
POST   /api/v1/teams/default      # Criar/obter time padrão
```

## Consequences

### Positivas

1. **Chat contextualizado**: Usuário seleciona team para filtrar respostas
2. **Relatórios focados**: Obrigatório selecionar ≥1 team para gerar relatório
3. **Métricas por team**: DORA/SPACE calculadas por agrupamento lógico
4. **Onboarding simplificado**: Time default criado automaticamente

### Negativas

1. **Complexidade**: Mais uma entidade para gerenciar
2. **Migration**: Dados existentes precisam de backfill

### Trabalho Futuro

1. [ ] Atualizar Chat para usar team como filtro default
2. [ ] Atualizar Reports para exigir seleção de team
3. [ ] Implementar GitHub Teams sync
4. [ ] UI para gerenciar teams no frontend

## Related

- [ADR-006: SaaS Data Model](006-saas-data-model.md)
- [ADR-008: Reports System](008-reports-system.md)
