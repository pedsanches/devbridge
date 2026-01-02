# Política de Segurança

## Versões Suportadas

| Versão | Suportada |
|--------|-----------|
| 1.x    | ✅        |
| < 1.0  | ❌        |

## Reportando Vulnerabilidades

**Não abra issues públicas para vulnerabilidades de segurança.**

Envie um email para **security@devbridge.io** com:

1. Descrição da vulnerabilidade
2. Passos para reproduzir
3. Impacto potencial
4. Sugestão de correção (se houver)

### Tempo de Resposta

- **Confirmação**: 48 horas
- **Avaliação inicial**: 7 dias
- **Correção**: depende da severidade

### Disclosure Responsável

Pedimos que:
- Nos dê tempo razoável para corrigir antes de divulgar
- Não acesse dados de outros usuários
- Não degrade a disponibilidade do serviço

## Práticas de Segurança

### Privacidade por Design

- Todo PII é sanitizado via **Microsoft Presidio** antes de processamento
- API Keys e secrets são ofuscados automaticamente
- Dados nunca saem da infraestrutura sem anonimização

### Validação de Entrada

- Todas as entradas são validadas via **Pydantic**
- Rate limiting implementado em todos os endpoints
- Webhooks verificados via assinatura HMAC

### Autenticação

- OAuth2 via GitHub
- Tokens JWT com expiração curta
- Refresh tokens com rotação
