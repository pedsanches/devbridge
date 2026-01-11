# ADR-002: Guardrails de AI para Zero Alucinação

**Data:** 2025-01-01

**Status:** Accepted

**Deciders:** Pedro (Tech Lead)

## Contexto

LLMs são propensas a "alucinar" - gerar informações plausíveis mas incorretas. No contexto do DevBridge, isso é especialmente perigoso para:

1. **Valores financeiros:** IA inventando "$50k de economia" sem dados
2. **Métricas técnicas:** "40% de melhoria de performance" sem medição
3. **Atribuições:** Dizer que "João fez X" quando foi Maria

Precisamos de mecanismos que **impeçam** a IA de gerar dados não fundamentados.

## Decisão

> Implementaremos **três camadas de guardrails** para garantir zero alucinação em dados críticos.

### Camada 1: Saída Estruturada (Instructor + Pydantic)

A LLM nunca retorna texto livre. Todas as respostas são objetos validados:

```python
class ImpactMetrics(BaseModel):
    metric_name: str
    improvement_percentage: Optional[float]
    confidence_score: int = Field(..., ge=0, le=100)
    is_financial_estimate: bool
    source: str = Field(..., description="De onde veio este dado")
```

### Camada 2: Contexto Explícito (.devbridge.yaml)

Métricas de negócio só são reportadas se existirem no arquivo de configuração:

```yaml
# .devbridge.yaml
business_metrics:
  average_cart_value: 150.00
  downtime_cost_per_hour: 15000.00
```

Se não houver métricas configuradas, a IA **não pode** gerar estimativas financeiras.

### Camada 3: Score de Confiança Obrigatório

Toda afirmação deve vir com um score de confiança (0-100):

| Score | Significado |
|-------|-------------|
| 80-100 | Alta confiança, baseado em dados explícitos |
| 50-79 | Média confiança, inferência razoável |
| 0-49 | Baixa confiança, **deve ser reescrito** |

## Alternativas Consideradas

### Alternativa A: Confiar na LLM com Prompting

- **Prós:** Simples de implementar
- **Contras:** Prompts não são garantias; LLM pode ignorar instruções
- **Por que descartada:** Não oferece garantias reais

### Alternativa B: Pós-processamento com Regex

- **Prós:** Funciona para casos simples
- **Contras:** Frágil, não escala, fácil de burlar
- **Por que descartada:** Muito limitado

### Alternativa C: LLM Secundária para Validação

- **Prós:** IA validando IA pode pegar erros sutis
- **Contras:** Dobra latência e custo, ainda não é garantia
- **Por que descartada:** Custo-benefício ruim

## Consequências

### Positivas
- **Garantia forte:** Schema validation é binário - ou passa ou falha
- **Rastreabilidade:** Cada métrica tem `source` documentado
- **Confiança:** Stakeholders podem confiar nos números

### Negativas
- **Complexidade:** Mais código para definir schemas
- **Rigidez:** Novos tipos de output requerem novos schemas
- **Latência:** Instructor adiciona ~100ms de overhead

### Neutras
- Time precisa aprender Pydantic e Instructor

## Notas de Implementação

```python
import instructor
from openai import OpenAI

client = instructor.from_openai(OpenAI())

response = client.chat.completions.create(
    model="gpt-4o",
    response_model=BusinessTranslation,  # Pydantic model
    messages=[{"role": "user", "content": prompt}]
)
# Se não passar na validação, levanta exceção
```

## Links Relacionados

- [Instructor Documentation](https://instructor-ai.github.io/instructor/)
- [Pydantic V2](https://docs.pydantic.dev/)
- [ADR-001: Stack Choice](./001-stack-choice.md)
