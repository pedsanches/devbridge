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
- Execute `pytest` para garantir que nada quebrou.
- Execute `ruff check .` se alterou arquivos Python.
- Se criar novos arquivos, atualize o `docs/system-context.md` se relevante.

## 📝 Documentação é Código

- **Nunca** altere lógica de negócio sem atualizar a documentação correspondente em `docs/business`.
- Se você tomou uma decisão arquitetural significativa, sugira criar um ADR em `docs/architecture/decisions`.

## 🎨 Diretrizes de UI/Design

Ao criar ou modificar interfaces visuais:

1.  **Use os Tokens**: Consulte `docs/design/foundations.md` para cores, tipografia e espaçamento.
    - *Nunca* use valores hardcoded (ex: `#0071E3`). Use variáveis (ex: `var(--color-primary)`).
2.  **Siga os Componentes**: Veja `docs/design/components.md` para padrões de botões, inputs, cards.
3.  **Respeite a Marca**: Consulte `docs/design/brand.md` para logo, voz e ícones (Lucide).
4.  **Garanta Acessibilidade**: Contraste mínimo 4.5:1, touch targets 44x44px.
