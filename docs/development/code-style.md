# Padrões de Código

Guia de estilo para código Python e TypeScript no DevBridge.

---

## Python

### Ferramentas

| Ferramenta | Uso |
|------------|-----|
| **Ruff** | Linting + Formatting (substitui black, isort, flake8) |
| **mypy** | Type checking |
| **pytest** | Testes (Coverage min: 70%) |
| **Bandit** | Análise de Segurança (`make security`) |
| **Radon** | Complexidade Ciclomática (`make complexity`) |
| **Interrogate** | Cobertura de Docstrings (`make check-docs`) |

### Configuração (pyproject.toml)

```toml
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]

[tool.mypy]
python_version = "3.11"
strict = true
```

### Convenções

#### Imports

```python
# ✅ Correto - ordem: stdlib, third-party, local
from typing import Optional

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.models.translation import BusinessTranslation
```

#### Type Hints

```python
# ✅ Sempre usar type hints
def process_webhook(payload: dict[str, Any]) -> BusinessTranslation:
    ...

# ✅ Usar Optional para valores que podem ser None
def get_user(user_id: str) -> Optional[User]:
    ...

# ✅ Usar Union ou | para múltiplos tipos (Python 3.10+)
def handle_result(result: str | dict[str, Any]) -> None:
    ...
```

#### Classes e Funções

```python
# ✅ Docstrings para funções públicas
def sanitize_content(content: str, language: str = "pt") -> str:
    """Remove PII from content before LLM processing.

    Args:
        content: Raw content to sanitize
        language: Language code for Presidio

    Returns:
        Sanitized content with PII replaced by placeholders

    Raises:
        SanitizationError: If content cannot be processed
    """
    ...

# ✅ Pydantic para modelos de dados
class CommitAnalysis(BaseModel):
    """Analysis result for a single commit."""

    commit_sha: str
    files_changed: list[str]
    impact_score: int = Field(..., ge=0, le=100)

    model_config = ConfigDict(frozen=True)
```

#### Erros e Exceções

```python
# ✅ Exceções customizadas com contexto
class WebhookValidationError(Exception):
    """Raised when webhook signature validation fails."""

    def __init__(self, signature: str, expected: str):
        self.signature = signature
        self.expected = expected
        super().__init__(f"Invalid signature: got {signature[:10]}...")

# ✅ Usar raise from para encadear exceções
try:
    result = await client.post(url, json=payload)
except httpx.RequestError as e:
    raise GitHubAPIError(f"Failed to fetch diff") from e
```

#### Async/Await

```python
# ✅ Usar async para I/O bound
async def fetch_commit_details(commit_sha: str) -> CommitDetails:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/commits/{commit_sha}")
        return CommitDetails.model_validate(response.json())

# ✅ Usar gather para paralelismo
async def analyze_commits(commits: list[str]) -> list[Analysis]:
    tasks = [analyze_single_commit(sha) for sha in commits]
    return await asyncio.gather(*tasks)
```

---

## TypeScript

### Ferramentas

| Ferramenta | Uso |
|------------|-----|
| **ESLint** | Linting |
| **Prettier** | Formatting |
| **TypeScript** | Type checking |

### Configuração

```json
// .eslintrc.json
{
  "extends": ["next/core-web-vitals", "prettier"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn"
  }
}
```

### Convenções

#### Imports

```typescript
// ✅ Ordem: React, libraries, local
import { useState, useEffect } from 'react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

import { ChatMessage } from './ChatMessage';
import type { Message } from './types';
```

#### Types e Interfaces

```typescript
// ✅ Interface para objetos
interface User {
  id: string;
  name: string;
  email: string;
}

// ✅ Type para unions e primitives
type MessageRole = 'user' | 'assistant' | 'system';

// ✅ Sempre tipar props de componentes
interface ChatInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}
```

#### Componentes React

```typescript
// ✅ Function components com tipos explícitos
export function ChatInput({
  onSubmit,
  disabled = false,
  placeholder = "Digite sua mensagem..."
}: ChatInputProps): JSX.Element {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input);
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
      />
    </form>
  );
}
```

---

## Convenções Gerais

### Nomenclatura

| Contexto | Python | TypeScript |
|----------|--------|------------|
| Variáveis | `snake_case` | `camelCase` |
| Funções | `snake_case` | `camelCase` |
| Classes | `PascalCase` | `PascalCase` |
| Constantes | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| Arquivos | `snake_case.py` | `kebab-case.ts` |

### Comentários

```python
# ✅ Explica o "porquê", não o "o quê"
# Rate limit de 100 req/hora por repositório (BR-022)
if request_count > RATE_LIMIT:
    raise RateLimitExceeded()

# ❌ Evite comentários óbvios
# Incrementa o contador
counter += 1
```

### Magic Numbers

```python
# ❌ Evite magic numbers
if confidence < 50:
    reprocess()

# ✅ Use constantes nomeadas
MIN_CONFIDENCE_THRESHOLD = 50  # Score mínimo para aceitar (BR-012)

if confidence < MIN_CONFIDENCE_THRESHOLD:
    reprocess()
```

---

## Verificação Automática

```bash
# Pre-commit hooks (configurado na instalação)
poetry run pre-commit run --all-files

# Ou manualmente
poetry run ruff check .
poetry run ruff format .
poetry run mypy app/
```
