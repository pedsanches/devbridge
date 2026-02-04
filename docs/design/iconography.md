# Iconography & Icon Governance

> **Library Oficial**: [Lucide React](https://lucide.dev)
> **Versão**: Latest
> **Fonte da Verdade**: `docs/contracts/ui-contract.md` (para estados)

## 1. Especificações Técnicas (Strict)

Para garantir que a UI não pareça "improvisada", siga estas regras rígidas:

### Tamanhos Padrão (Tailwind Classes)
| Tamanho | Class | Uso Canônico | Exemplo |
|---------|-------|--------------|---------|
| **Tiny** | `w-3 h-3` | Badges, ReferenceChips, Metadata lines | inside `Badge`, `text-xs` |
| **Small** | `w-4 h-4` | Botões secundários, Links, Tabela Default | `Button size="sm"`, `Table` |
| **Base** | `w-5 h-5` | Botões primários, Nav Items, Headers H3/H4 | `Button size="default"` |
| **Large** | `w-6 h-6` | Modais, Page Headers, Empty States (Small) | Page Titles |
| **Hero** | `w-8 h-8`+ | Empty States (Large), Feature Highlights | Dashboard cards |

### Estilo e Alinhamento
- **Stroke Width**: `stroke-[1.5px]` é o padrão do DevBridge.
    - *Exceção*: Ícones Tiny (`w-3`) podem usar `stroke-[2px]` se perderem legibilidade.
- **Alinhamento com Texto**:
    - Flex container: `flex items-center gap-2`.
    - Nunca use `baseline` cegamente, pois ícones tendem a "flutuar". Centralize sempre verticalmente (`items-center`).
- **Estados**:
    - **Filled**: Evite `fill-current`. Use fill apenas para estados "toggled/active" (ex: Estrela de favorito, Like).

## 2. Mapeamento Semântico (Token -> Icon)

### Status & Feedback
| Token | Ícone (Lucide) | Semântica |
|-------|----------------|-----------|
| `Status.Success` | `CheckCircle2` | Completado com sucesso |
| `Status.Warning` | `AlertTriangle` | Atenção necessária |
| `Status.Error` | `AlertCircle` | Erro impeditivo (use XCircle para "Cancelado") |
| `Status.Info` | `Info` | Informação neutra |
| `Status.Loading` | `Loader2` | `animate-spin` obrigatório |

### Entidades de Negócio
| Token | Ícone (Lucide) | Contexto |
|-------|----------------|----------|
| `Entity.Repo` | `GitBranch` | Repositório de código |
| `Entity.PR` | `GitPullRequest` | Pull Request |
| `Entity.Commit` | `GitCommit` | Commit único |
| `Entity.Issue` | `CircleDot` | Issue aberta |
| `Entity.Team` | `Users` | Time |
| `Entity.Bot` | `Bot` | IA / Sistema |
| `Entity.User` | `User` | Humano |

### Ações Comuns
| Ação | Ícone | Nota |
|------|-------|------|
| Edit | `Pencil` | |
| Delete | `Trash2` | Ação destrutiva |
| Copy | `Copy` | |
| External Link | `ExternalLink` | Links que abrem nova aba |
| Search | `Search` | |
| Settings | `Settings` | |
| Menu | `Menu` | Hamburger |
| More | `MoreHorizontal` | Context menu (...) |

## 3. Anti-Patterns
- ❌ **Ícone Solitário sem Aria-Label**: Todo botão icon-only PRECISA de `aria-label="Descricao"`.
- ❌ **Tamanhos Arbitrários**: Não use `w-[17px]`. Use a escala `3, 4, 5, 6`.
- ❌ **Stroke Inconsistente**: Não misture ícones bold (2px+) com thin (1px) na mesma tela.
