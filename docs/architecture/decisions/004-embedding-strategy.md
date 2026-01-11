# ADR-004: Estratégia de Embeddings

**Status:** Aceito
**Data:** 2026-01-02
**Decisores:** Time de Arquitetura

## Contexto

O DevBridge precisa de embeddings vetoriais para:
1. Busca semântica em commits e traduções
2. RAG (Retrieval Augmented Generation) para o chat
3. Similaridade entre commits/traduções

Precisamos decidir entre:
- Usar embeddings via API externa (OpenAI, Cohere, Voyage)
- Usar modelos locais (sentence-transformers)
- Solução híbrida

## Decisão

**Utilizaremos OpenAI `text-embedding-3-small` como padrão**, com fallback para modelo local.

### Configuração

```yaml
# .env
EMBEDDING_PROVIDER=openai  # ou 'local'
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

## Justificativa

### OpenAI text-embedding-3-small

| Aspecto | Avaliação |
|---------|-----------|
| **Qualidade** | Excelente para português e código |
| **Custo** | $0.02/M tokens (~R$0.10/M tokens) |
| **Latência** | ~100-200ms por batch |
| **Dimensão** | 1536 (configurável até 3072) |
| **Manutenção** | Zero - API gerenciada |

### Alternativas Consideradas

#### OpenAI text-embedding-3-large
- ❌ Custo 5x maior
- ❌ Ganho marginal para nosso caso

#### Voyage AI voyage-code-2
- ✅ Excelente para código
- ❌ Menos robusto para português
- ❌ Vendor menos estabelecido

#### sentence-transformers (local)
- ✅ Custo zero
- ❌ Requer GPU para performance
- ❌ Qualidade inferior para PT-BR

## Implementação

### Abstração de Provider

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel


class EmbeddingResult(BaseModel):
    vector: list[float]
    model: str
    tokens_used: int


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.client = AsyncOpenAI()

    async def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [
            EmbeddingResult(
                vector=e.embedding,
                model=self.model,
                tokens_used=response.usage.total_tokens // len(texts),
            )
            for e in response.data
        ]
```

### Fallback Local

```python
class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)

    async def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        vectors = self.model.encode(texts)
        return [
            EmbeddingResult(vector=v.tolist(), model=self.model, tokens_used=0)
            for v in vectors
        ]
```

### Factory

```python
def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.EMBEDDING_PROVIDER

    if provider == "openai":
        return OpenAIEmbeddingProvider(settings.EMBEDDING_MODEL)
    elif provider == "local":
        return LocalEmbeddingProvider()
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

## Consequências

### Positivas

- ✅ Alta qualidade de embeddings para PT-BR e código
- ✅ Custo previsível e baixo ($0.02/M tokens)
- ✅ Zero manutenção de infraestrutura
- ✅ Abstração permite trocar provider facilmente

### Negativas

- ❌ Dependência de serviço externo
- ❌ Latência de rede (~100-200ms)
- ❌ Dados saem da infraestrutura (mitigado: PII já sanitizado)

### Mitigações

1. **Cache agressivo**: Embeddings são cacheados em Qdrant
2. **Batch processing**: Processamos em lotes de 100 textos
3. **Fallback local**: Se OpenAI indisponível, usa modelo local
4. **Sanitização prévia**: Presidio remove PII antes do embedding

## Métricas de Monitoramento

| Métrica | Alvo |
|---------|------|
| Latência P95 | < 500ms |
| Taxa de erro | < 0.1% |
| Custo mensal | < $50 |
| Cache hit rate | > 80% |

## Referências

- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [text-embedding-3 Announcement](https://openai.com/blog/new-embedding-models-and-api-updates)
- [ADR-003: Privacy by Design](./003-privacy-by-design.md)
