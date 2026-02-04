# Guia para Agentes de IA

Este documento define como Agentes de IA devem operar dentro do repositório DevBridge.

## 🚦 Protocolo de Desenvolvimento

Antes de realizar qualquer alteração, o Agente deve:

1.  **Carregar o Contexto**: Leia `docs/system-context.md` para entender onde você está.
2.  **Verificar Estilo**: Consulte `docs/development/code-style.md` para padrões Python/TS.
    - *Exemplo*: Use type hints sempre (`def func(a: int) -> str:`).
    - *Exemplo*: Use `snake_case` para variáveis Python e `camelCase` para TS.
3.  **Respeitar a Arquitetura**:
    - Mudanças de banco de dados exigem updates em `docs/architecture/data-flow.md`.
    - Novas dependências exigem justificativa.
4.  **Seguir a Estrutura**: Ao criar novos arquivos, siga `docs/architecture/project-structure.md`.

## 🧪 Verificação

Ao concluir uma tarefa:
- Execute `make precommit` para rodar todas as verificações (Lint, Types, Security).
- Execute `make complexity` para garantir que o código não ficou complexo demais (Grade A ou B).
- Execute `make test-backend` para garantir que nada quebrou.
- Se criar novos arquivos, atualize o `docs/system-context.md`.

## 📝 Documentação é Código

- **Nunca** altere lógica de negócio sem atualizar a documentação correspondente em `docs/business`.
- Se você tomou uma decisão arquitetural significativa, sugira criar um ADR em `docs/architecture/decisions`.

## 🎨 Diretrizes de UI/Design (Governança)

Antes de criar qualquer interface, **leia o Contrato de UI**: `docs/design/ui-charter.md`.

### 📚 Referência Obrigatória
- **Regras Visuais**: `docs/design/ui-constraints.md` (Layout, Cores, Tabelas)
- **Tokens**: `docs/design/foundations.md` (Use variáveis, nunca hardcode!)
- **Componentes**: `docs/design/components.md` (InsightCard, EvidenceTable, etc)
- **Interações IA**: `docs/design/patterns/ai-interactions.md` (Patterns de resposta)

### ✅ Checklist "Antes de Criar UI"
1.  **Validar Tokens**: Estou usando `--color-primary` e `--space-4`? (Proibido hex/px)
2.  **Verificar Anti-Patterns**: Minha UI parece um "Dribbble shot"? Se sim, simplifique.
3.  **Rastreabilidade**: Adicionei `ReferenceChip` ou link de evidência para toda afirmação?
4.  **Estados**: Defini como fica esta tela vazia (`EmptyState`) ou carregando (`Skeleton`)?
5.  **Confirmação**: Ações de escrita exigem fluxo `Proposta -> Preview -> Confirmar`.

> [!WARNING]
> Agentes flagrados inventando estilos ou ignorando tokens receberão feedback negativo severo no Code Review.

