# Exemplo Canônico: Insight Detail

## 🎯 Objetivo
Aprofundar em um insight específico gerado pela IA (ex: "Detector de Risco em PR"). Deve dar confiança total ao usuário para tomar uma ação.

## ❓ Perguntas Respondidas
- Por que a IA acha isso? (Reasoning)
- Quais arquivos provam isso? (Evidence)
- Qual o impacto se eu ignorar? (Implication)

## 🏗️ Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  < Back to Dashboard                                        │
├─────────────────────────────────────────────────────────────┤
│  [ Badge: High Severity ] [ Badge: Performance ]            │
│  # N+1 Query detected in UserServices (H1)                  │
│                                                             │
│  [ Context Description: 2-3 lines of summary ]              │
│                                                             │
│  [ Action Bar ] ──────────────────────────────────────────  │
│  [ Button: Create Issue ] [ Button: Generate Fix ]          │
├─────────────────────────────────────────────────────────────┤
│  ## Evidências (H2)                                         │
│                                                             │
│  [EvidenceTable]                                            │
│  | File impl.py    | L45  | for user in users: db.get() |   │
│  | File query.sql  | L12  | SELECT * FROM address...    |   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ## Impacto Estimado (H2)                                   │
│  - Latency: +400ms (p99)                                    │
│  - Database Load: Linear increase with user count           │
└─────────────────────────────────────────────────────────────┘
```

## ✅ Seções Obrigatórias
1.  **Header Claro**: Título descritivo, não "Erro #342".
2.  **Contexto**: Texto humano explicando o problema.
3.  **Evidências**: Links diretos para os arquivos (`ReferenceChip`).
4.  **Ações**: O que o usuário pode fazer agora?

## 🚦 Estados
- **Loading**: Spinner enquanto a IA busca detalhes extras do commit.
- **Partial**: Se a IA não conseguir estimar impacto, omita a seção, não mostre "Impacto: Desconhecido".

## 🚫 Don't Do This
- Nunca mostre um diff de código proposto sem que o usuário peça ("Generate Fix").
- Nunca esconda o caminho do arquivo (path) para "simplificar". O usuário técnico precisa saber onde é.
