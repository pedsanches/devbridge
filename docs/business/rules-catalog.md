# Catálogo de Regras de Negócio

Este documento é a **fonte única de verdade** para todas as regras de negócio do DevBridge.

## Formato

Cada regra segue o padrão:

| Campo | Descrição |
|-------|-----------|
| **ID** | Identificador único (BR-XXX) |
| **Título** | Nome descritivo |
| **Regra** | Declaração em linguagem natural |
| **Justificativa** | Por que esta regra existe |
| **Módulo** | Componente afetado |
| **Prioridade** | Critical / High / Medium / Low |

---

## Regras de Privacidade e Segurança

### BR-001: Sanitização Obrigatória de PII

| Campo | Valor |
|-------|-------|
| **Regra** | Todo conteúdo de código deve passar por sanitização de PII antes de ser enviado para qualquer LLM externa. |
| **Justificativa** | Compliance com LGPD/GDPR e proteção de dados dos clientes |
| **Módulo** | `engine/scrubbing` |
| **Prioridade** | Critical |

### BR-002: Validação de Webhook Signature

| Campo | Valor |
|-------|-------|
| **Regra** | Webhooks do GitHub devem ter assinatura HMAC validada antes de processamento. |
| **Justificativa** | Prevenir processamento de payloads forjados |
| **Módulo** | `api/webhooks` |
| **Prioridade** | Critical |

### BR-003: Secrets Nunca em Logs

| Campo | Valor |
|-------|-------|
| **Regra** | Tokens, API Keys e senhas nunca podem aparecer em logs de aplicação. |
| **Justificativa** | Prevenir vazamento de credenciais |
| **Módulo** | `core/logging` |
| **Prioridade** | Critical |

---

## Regras de AI e Guardrails

### BR-010: Zero Alucinação Financeira

| Campo | Valor |
|-------|-------|
| **Regra** | A IA só pode reportar impacto financeiro se houver métricas explícitas no `.devbridge.yaml`. |
| **Justificativa** | Prevenir estimativas falsas que podem influenciar decisões de negócio |
| **Módulo** | `engine/agents` |
| **Prioridade** | Critical |

### BR-011: Saída Estruturada Obrigatória

| Campo | Valor |
|-------|-------|
| **Regra** | Toda resposta da LLM deve ser um objeto Pydantic validado, nunca texto livre. |
| **Justificativa** | Garantir consistência e evitar erros de parsing no frontend |
| **Módulo** | `engine/agents` |
| **Prioridade** | High |

### BR-012: Score de Confiança Mínimo

| Campo | Valor |
|-------|-------|
| **Regra** | Traduções com confidence_score < 50 devem ser reprocessadas pelo nó Auditor. |
| **Justificativa** | Garantir qualidade mínima das traduções |
| **Módulo** | `engine/agents` |
| **Prioridade** | High |

### BR-013: Fonte de Dados Rastreável

| Campo | Valor |
|-------|-------|
| **Regra** | Toda métrica de impacto deve incluir campo `source` indicando origem do dado. |
| **Justificativa** | Permitir auditoria e verificação de afirmações |
| **Módulo** | `models/translation` |
| **Prioridade** | High |

---

## Regras de Ingestão

### BR-020: Arquivos Ignorados

| Campo | Valor |
|-------|-------|
| **Regra** | Os seguintes padrões devem ser ignorados na análise: `*.lock`, `node_modules/**`, `dist/**`, `.git/**`, `*.min.js` |
| **Justificativa** | Evitar processamento de arquivos irrelevantes ou gerados |
| **Módulo** | `engine/parsing` |
| **Prioridade** | Medium |

### BR-021: Limite de Tamanho de Diff

| Campo | Valor |
|-------|-------|
| **Regra** | Diffs maiores que 10.000 linhas devem ser summarizados por arquivo antes de processamento completo. |
| **Justificativa** | Evitar timeout e custo excessivo com LLM |
| **Módulo** | `services/github` |
| **Prioridade** | Medium |

### BR-022: Rate Limiting por Repositório

| Campo | Valor |
|-------|-------|
| **Regra** | Máximo de 100 webhooks por hora por repositório. |
| **Justificativa** | Prevenir abuso e garantir disponibilidade |
| **Módulo** | `api/webhooks` |
| **Prioridade** | High |

---

## Regras de Entrega

### BR-030: Adaptação por Audience

| Campo | Valor |
|-------|-------|
| **Regra** | Respostas devem ser adaptadas ao perfil do usuário (PM = outcome-focused, CTO = technical, CEO = executive-summary). |
| **Justificativa** | Melhorar relevância e compreensão |
| **Módulo** | `engine/agents` |
| **Prioridade** | Medium |

### BR-031: Notificação Push para Slack

| Campo | Valor |
|-------|-------|
| **Regra** | Resumos diários devem ser enviados automaticamente para Slack às 18:00 (timezone do projeto). |
| **Justificativa** | Princípio "Push over Pull" - stakeholders não precisam buscar informação |
| **Módulo** | `services/slack` |
| **Prioridade** | Medium |

---

## Regras de Dados

### BR-040: Retenção de Histórico

| Campo | Valor |
|-------|-------|
| **Regra** | Dados de commits e traduções devem ser retidos por no mínimo 365 dias. |
| **Justificativa** | Permitir análise histórica e comparações |
| **Módulo** | `core/database` |
| **Prioridade** | Low |

### BR-041: Soft Delete Obrigatório

| Campo | Valor |
|-------|-------|
| **Regra** | Registros nunca devem ser deletados fisicamente (hard delete). Usar `deleted_at` timestamp. |
| **Justificativa** | Auditoria e recuperação de dados |
| **Módulo** | `models/base` |
| **Prioridade** | Medium |

---

## Versionamento deste Documento

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2025-01-01 | Pedro | Criação inicial |

## Como Adicionar Novas Regras

1. Determine o próximo ID disponível (BR-XXX)
2. Preencha todos os campos obrigatórios
3. Submeta via PR para revisão
4. Após aprovação, atualize a tabela de versionamento
