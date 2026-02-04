# AI Interaction Patterns

Este documento define como a Inteligência Artificial interage com o usuário na interface do DevBridge. O modelo mental central é: **IA Propõe, Humano Confirma.**

## 🧠 Modelo Mental: Co-Pilot, não Auto-Pilot

1.  **Intent**: O usuário expressa uma intenção (vaga ou específica).
2.  **Reasoning**: A IA analisa o contexto, busca dados (R#) e formula uma estratégia.
3.  **Proposal**: A IA apresenta uma proposta estruturada (Resumo + Evidência + Ação).
4.  **Verification**: O usuário revisa (Preview/Diff).
5.  **Execution**: O usuário aprova e o sistema executa.

## 💬 Padrão de Resposta (The "Insight Block")

Toda resposta da IA que traz um insight técnico deve seguir esta anatomia:

```
┌───────────────────────────────────────────────┐
│  🧩 [Título do Insight / Conclusão Principal] │
│  [Badge: Confidence Level]                    │
├───────────────────────────────────────────────┤
│  Resumo executivo do problema ou descoberta.  │
│  Texto curto, direto, focado em impacto.      │
├───────────────────────────────────────────────┤
│  🔍 Evidências (Drill-down):                  │
│  - [RefChip] app/main.py (L45-90)             │
│  - [RefChip] Commit a1b2c3d                   │
│  - [Metrica] Complexidade aumentou +15%       │
├───────────────────────────────────────────────┤
│  ⚡ Ações Sugeridas:                          │
│  [ Button: Gerar Refactor ]  [ Button: Ignorar ]
└───────────────────────────────────────────────┘
```

## 🛡️ Segurança contra Alucinação

### Indicadores de Confiança
Sempre que a IA fizer uma afirmação inferida (não um fato determinístico), mostre o nível de confiança:
- 🟢 **Alta (High Confidence)**: Baseado em dados explícitos e padrões claros.
- 🟡 **Média (Needs Review)**: Padrão detectado, mas com ambiguidades.
- 🔴 **Baixa (Experimental)**: Sugestão criativa ou baseada em dados escassos.

### Citação Obrigatória
- Se a IA diz "O código está lento", ela DEVE mostrar o link para o benchmark ou trecho de código O(n^2).
- Se a IA diz "Isso quebra a regra de negócio", ela DEVE linkar a regra no `rules-catalog.md`.

## 🔄 Fluxo de Mutação (Apply / Preview)

Para ações que alteram código ou documentos:

### 1. Staging (Proposta)
A IA gera o artefato em memória ou em um branch temporário/shadow.
O usuário vê um card: *"Pronto para criar arquivo `service.py`"*.

### 2. Preview (Diff)
Ao clicar, abre-se um modal ou painel split-view:
- **Esquerda**: Atual (Empty ou Old Version)
- **Direita**: Proposto (New Version)
- **Visual**: Highlight de sintaxe e diff colorido (Verde/Vermelho).

### 3. Confirmation
Botão de ação claro: "Confirmar Alterações" ou "Aplicar Commit".
Opção de edição manual antes de aplicar ("Refine").

## 👍 Feedback Loops
Todo bloco de resposta da IA deve ter micro-ações de feedback discretas:
- 👍 (Útil / Correto)
- 👎 (Incorreto / Alucinação) -> Abre diálogo: "O que estava errado?"
- 🚩 (Report Issue) -> Cria ticket para engenharia do DevBridge.
