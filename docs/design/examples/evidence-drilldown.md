# Exemplo Canônico: Evidence Drill-down

## 🎯 Objetivo
A interface de "Prova Real". O usuário duvidou da IA ou precisa de contexto técnico bruto. É fundamentalmente uma view de dados/code.

## ❓ Perguntas Respondidas
- Onde exatamente isso aconteceu?
- Quem fez essa alteração?
- Qual era o código antes e depois?

## 🏗️ Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  [Breadcrumb: Insight > Evidence #12 ]                      │
├──────┬──────────────────────────────────────────────────────┤
│ FILE │  src/backend/app/main.py  (Copy Path)                │
│ TREE │                                                      │
│      │  [Code View Block - Read Only]                       │
│      │  39 | def get_users():                               │
│      │  40 |    # Old implementation                        │
│      │  41 |    return db.query(User).all()                 │
│      │  42 |                                                │
│      │                                                      │
│      │  [Annotated Line Highlight - Background Yellow]      │
│      │  ⚠️ IA Suggestion: Missing pagination here           │
│      │                                                      │
│      └──────────────────────────────────────────────────────┘
├─────────────────────────────────────────────────────────────┤
│  [Metadata Panel - Bottom or Right]                         │
│  Commit: a1b2c (Pedro) | Date: 2023-10-15 | PR: #405        │
└─────────────────────────────────────────────────────────────┘
```

## ✅ Seções Obrigatórias
1.  **Code Viewer**: Com syntax highlighting e números de linha.
2.  **Annotations**: A IA deve ser capaz de "desenhar" sobre o código (highlights, comments inline).
3.  **Source Link**: Botão para abrir no GitHub/GitLab.

## 🚦 Estados
- **File Not Found**: O arquivo mudou ou foi deletado desde a análise. Mostrar aviso claro e, se possível, o conteúdo "cached" da época da análise.
- **Binary File**: Se for imagem/binário, mostrar placeholder ou preview, não garbage text.

## 🚫 Don't Do This
- Não permita edição direta aqui. É um view de auditoria.
- Não mostre o arquivo inteiro se tiver 10k linhas. Mostre `[Expanded Context]` button acima/abaixo do trecho relevante.
