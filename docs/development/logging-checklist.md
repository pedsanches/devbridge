# Checklist de Logging - DevBridge

Guia padronizado para logging estruturado no backend.

> **Para agentes de IA**: Siga este checklist ao adicionar logs em qualquer código novo.

---

## Regras Gerais

### ✅ SEMPRE faça

1. **Use structlog** (nunca `print()` ou `logging` padrão)
   ```python
   from app.core.logging import get_logger
   logger = get_logger(__name__)
   ```

2. **Inclua contexto relevante** como kwargs
   ```python
   # ✅ BOM
   logger.info("User created", user_id=user.id, email=user.email)

   # ❌ RUIM
   logger.info(f"User created: {user.id}")
   ```

3. **Use níveis corretos**
   ```python
   logger.debug("Processing item", item_id=1)     # Detalhes de debug
   logger.info("Operation completed", count=10)   # Eventos normais
   logger.warning("Retry needed", attempt=3)      # Situações anômalas
   logger.error("Operation failed", error=str(e)) # Erros que afetam funcionalidade
   logger.exception("Fatal error")                # Erros com stacktrace
   ```

4. **Use contexto de operação** para agrupar logs
   ```python
   from app.core.logging import log_operation

   with log_operation("sync_repository", repository="owner/repo"):
       logger.info("Starting sync")
       # ... código ...
       logger.info("Sync completed", commits=10)
   ```

### ❌ NUNCA faça

1. **Nunca logue informações sensíveis**
   ```python
   # ❌ NUNCA
   logger.info("Login attempt", password=password)
   logger.info("Payment", credit_card=card_number)
   logger.info("Token", api_key=key)
   ```

2. **Nunca use print() ou logging.info()**
   ```python
   # ❌ NUNCA
   print(f"Debug: {value}")
   logging.info("Something happened")
   ```

3. **Nunca logue objetos inteiros** (pode conter PII)
   ```python
   # ❌ NUNCA
   logger.info("User data", user=user)

   # ✅ BOM
   logger.info("User data", user_id=user.id = user.name)
   ```

---

## Níveis de Log

| Nível | Quando Usar | Exemplo |
|-------|-------------|---------|
| `DEBUG` | Detalhes para troubleshooting | `"Processing item"` |
| `INFO` | Eventos normais de negócio | `"User created"`, `"Webhook received"` |
| `WARNING` | Situações anômalas que não impedem operação | `"Retry needed"`, `"Rate limit close"` |
| `ERROR` | Erros que afetam funcionalidade | `"Failed to process"`, `"External API error"` |
| `EXCEPTION` | Erros com stacktrace (fatal) | `"Unhandled exception"` |

---

## Campos Obrigatórios por Tipo de Operação

### Requests HTTP
```python
# Já são adicionados automaticamente pelo middleware:
# - request_id
# - trace_id
# - http_method
# - http_path
# - user_id (se autenticado)
# - org_id (se autenticado)
```

### Operações de Banco
```python
logger.info("Query executed",
    table="users",
    operation="select",
    record_count=10,
    duration_ms=50
)
```

### Chamadas a APIs Externas
```python
logger.info("External API call",
    service="github",
    endpoint="/repos",
    status_code=200,
    duration_ms=150
)
```

### Tasks Celery
```python
logger.info("Task started",
    task_name="sync_repository",
    task_id=task_id,
    args=repr(args)[:200]  # Limitar tamanho
)
```

### Erros
```python
logger.error("Operation failed",
    error_type=type(e).__name__,
    error_message=str(e),
    trace_id=trace_id,
    # NÃO incluir stacktrace aqui
)

# OU para stacktrace completo:
logger.exception("Unhandled exception",
    trace_id=trace_id
)
```

---

## Buscando Logs

### Por trace_id (mais comum)
```bash
docker logs devbridge-backend-1 2>&1 | grep "trace_id=SEU_ID"
```

### Por operação
```bash
docker logs devbridge-backend-1 2>&1 | grep "operation=sync_repository"
```

### Por nível de erro
```bash
docker logs devbridge-backend-1 2>&1 | grep '"level":"error"'
```

### Via Grafana/Loki
```
{container="devbridge-backend-1"} |= "trace_id=SEU_ID"
```

---

## Exemplos Completos

### Service com logging correto
```python
from app.core.logging import get_logger, log_operation

logger = get_logger(__name__)


async def create_user(email: str, name: str) -> User:
    """Create a new user with proper logging."""
    logger.info("Creating user", email=email)

    try:
        user = await db.create(User(email=email, name=name))

        logger.info("User created successfully",
            user_id=str(user.id),
            email=email
        )
        return user

    except IntegrityError:
        logger.warning("User already exists", email=email)
        raise ValidationError("User with this email already exists")

    except Exception as e:
        logger.error("Failed to create user",
            email=email,
            error=str(e)
        )
        raise
```

### Endpoint com logging correto
```python
from app.core.logging import get_logger

logger = get_logger(__name__)


@router.post("/users")
async def create_user_endpoint(data: UserCreate) -> UserResponse:
    """Create user endpoint with logging."""
    # trace_id já está no contexto via middleware

    logger.info("Create user request received")

    try:
        user = await user_service.create(data)

        logger.info("Create user completed",
            user_id=str(user.id)
        )
        return UserResponse.from_orm(user)

    except ValidationError as e:
        logger.warning("Validation failed", error=str(e))
        raise HTTPException(422, detail=str(e))
```

---

## Arquivos Relevantes

| Arquivo | Propósito |
|---------|-----------|
| `backend/app/core/logging.py` | Configuração do structlog |
| `backend/app/core/middleware.py` | Middleware que injeta trace_id |
| `docs/operations/monitoring.md` | Guia de monitoramento |
