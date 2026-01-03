# ADR-007: Estratégia de Autenticação

**Data:** 2026-01-03

**Status:** Proposed

**Deciders:** Time de Arquitetura

## Contexto

O DevBridge precisa de autenticação para:
1. Identificar usuários e vincular a organizações
2. Proteger endpoints de API
3. Personalizar respostas por role/persona (ADR-005)

Conforme [ADR-005](./005-product-strategy.md), a estratégia é **phaseada**:
- **MVP:** Magic Link (passwordless)
- **Fase 2:** OAuth (GitHub/Google)
- **Enterprise:** SAML/SSO

## Decisão

### Arquitetura de Auth

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FLUXO MAGIC LINK                                 │
│                                                                          │
│  1. User entra email    2. API gera token    3. Email enviado           │
│  ┌─────────────┐        ┌─────────────┐      ┌─────────────┐            │
│  │  Frontend   │───────▶│   /auth/    │─────▶│   Resend    │            │
│  │  /login     │        │   magic     │      │   (email)   │            │
│  └─────────────┘        └─────────────┘      └─────────────┘            │
│                                                     │                    │
│  4. User clica link     5. Token validado    6. JWT retornado           │
│  ┌─────────────┐        ┌─────────────┐      ┌─────────────┐            │
│  │  Email      │───────▶│   /auth/    │─────▶│   Set       │            │
│  │  inbox      │        │   verify    │      │   Cookie    │            │
│  └─────────────┘        └─────────────┘      └─────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
```

### Componentes

#### 1. MagicLink Model

```python
class MagicLink(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "magic_links"

    email = Column(String(255), nullable=False, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
```

#### 2. JWT Structure

```json
{
  "sub": "user_uuid",
  "email": "user@example.com",
  "org_id": "organization_uuid",
  "role": "member",
  "exp": 1704326400,
  "iat": 1704240000
}
```

#### 3. Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/auth/magic` | POST | Solicita magic link (envia email) |
| `/auth/verify` | GET | Valida token e retorna JWT |
| `/auth/me` | GET | Retorna usuário atual |
| `/auth/logout` | POST | Invalida sessão |

### Email Provider: Resend

**Por que Resend:**
- API simples (SDKs Python/Node)
- Plano gratuito: 3.000 emails/mês
- Templates em React
- Deliverability alta

```python
import resend

resend.api_key = settings.RESEND_API_KEY

resend.Emails.send({
    "from": "DevBridge <auth@devbridge.io>",
    "to": email,
    "subject": "Seu link de acesso ao DevBridge",
    "html": render_magic_link_email(token, expires_in_minutes=15),
})
```

### Segurança

| Aspecto | Implementação |
|---------|---------------|
| Token | 32 bytes random (secrets.token_urlsafe) |
| Expiração | 15 minutos |
| Rate Limit | 5 requests/email/hora |
| JWT Secret | 256-bit, via env var |
| JWT Expiry | 7 dias (com refresh) |
| HTTPS Only | Cookie secure + httponly |

### Fluxo de Primeiro Acesso

1. User solicita magic link com email
2. Sistema verifica se email existe em `users`
3. Se **não existe**: cria User + cria "Personal Organization" + Membership(OWNER)
4. Se **existe**: reutiliza User
5. Gera MagicLink e envia email
6. User clica link → valida → gera JWT com `org_id` da primeira org

## Alternativas Consideradas

| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| **Magic Link (escolhido)** | Sem senha, UX simples | Depende de email | ✅ MVP |
| Auth0/Clerk | Rápido, features prontas | Custo ($25+/mês), vendor lock | Futuro |
| Password-based | Familiar | Complexidade (reset, hash) | ❌ |
| OAuth-only | Sem gerenciar credenciais | Nem todos têm GitHub/Google | Fase 2 |

## Consequências

### Positivas
- ✅ Zero fricção: usuário não precisa criar senha
- ✅ Seguro: token de uso único, expira rápido
- ✅ Simples: ~200 linhas de código
- ✅ Extensível: adicionar OAuth depois é fácil

### Negativas
- ❌ Depende de email ser entregue
- ❌ Latência: usuário precisa ir ao email
- ❌ Email corporativo pode bloquear

### Mitigações
- Fallback para reenvio de email
- Link direto "Não recebeu? Reenviar"
- Monitorar taxa de entrega no Resend

## Implementação

### Arquivos a Criar

| Arquivo | Descrição |
|---------|-----------|
| `models/magic_link.py` | Model MagicLink |
| `services/auth_service.py` | Lógica de auth |
| `services/email_service.py` | Wrapper Resend |
| `api/v1/auth.py` | Endpoints REST |
| `core/security.py` | JWT utilities |
| `api/deps.py` | `get_current_user` dependency |

### Variáveis de Ambiente

```bash
JWT_SECRET_KEY=your-256-bit-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7
RESEND_API_KEY=re_...
MAGIC_LINK_EXPIRE_MINUTES=15
```
