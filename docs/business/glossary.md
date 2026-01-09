# Glossário

Definições padronizadas de termos usados no DevBridge.

---

## A

### ADR (Architecture Decision Record)
Documento que registra uma decisão arquitetural significativa, incluindo contexto, alternativas consideradas e consequências.

### AST (Abstract Syntax Tree)
Representação estruturada do código-fonte que permite análise sem executar o código. DevBridge usa Tree-sitter para parsing.

### Alucinação
Quando uma LLM gera informações plausíveis mas incorretas ou inventadas, sem base em dados reais.

---

## B

### Business Translation
Objeto estruturado que representa a tradução de trabalho técnico para linguagem de negócio. Inclui título, resumo técnico, valor de negócio e métricas.

---

## C

### Celery
Framework Python para processamento de tarefas assíncronas. DevBridge usa para processar webhooks em background.

### Confidence Score
Pontuação de 0-100 indicando o nível de certeza da IA sobre uma tradução. Scores < 50 requerem reprocessamento.

### Context Injector
Componente que carrega o `.devbridge.yaml` e contexto histórico relevante antes do processamento pela LLM.

---

## D

### .devbridge.yaml
Arquivo de configuração na raiz do repositório monitorado que define métricas de negócio, pilares estratégicos e perfis de audiência.

### Diff
Diferença entre duas versões de código, geralmente entre commits ou branches.

### DORA (DevOps Research and Assessment)
Framework de métricas focado em velocidade (Deployment Frequency, Lead Time) e estabilidade (Change Failure Rate, MTTR) de times de software.

---

## E

### Embedding
Representação vetorial de texto que permite busca semântica. DevBridge usa jina-embeddings-v3.

---

## G

### Guardrails
Mecanismos que limitam e validam as respostas da LLM para prevenir alucinações e erros.

---

## I

### Instructor
Biblioteca Python que força LLMs a retornarem objetos Pydantic validados, garantindo saída estruturada.

---

## L

### LangGraph
Framework de orquestração de AI que permite fluxos cíclicos e controle de estado. Usado para o pipeline de tradução.

### Lead Time for Changes
Métrica DORA que mede o tempo desde o primeiro commit até o deploy em produção (ou merge na master).

### LLM (Large Language Model)
Modelo de linguagem de grande escala. DevBridge usa Claude 3.5 Sonnet da Anthropic.

---

## M

### MTTR (Mean Time To Recovery)
Métrica DORA que mede o tempo médio necessário para restaurar o serviço após uma falha em produção.

---

## P

### PII (Personally Identifiable Information)
Informação que pode identificar uma pessoa, como email, CPF, telefone. Deve ser sanitizado antes de enviar para LLM.

### Presidio
Biblioteca Microsoft para detecção e anonimização de PII. DevBridge usa para garantir privacidade.

### Pydantic
Biblioteca Python para validação de dados usando type hints. Garante que respostas da LLM são estruturadas.

### Push over Pull
Princípio de design onde o sistema envia informações proativamente para stakeholders, ao invés de esperar que consultem.

---

## Q

### Qdrant
Banco de dados vetorial usado para busca semântica. Permite encontrar commits/PRs semanticamente relacionados.

---

## R

### RAG (Retrieval-Augmented Generation)
Técnica que combina recuperação de informações com geração de texto. DevBridge recupera contexto relevante antes de gerar respostas.

---

## S

### SPACE Framework
Framework holístico para medir produtividade de desenvolvedores considerando: Satisfaction, Performance, Activity, Communication, e Efficiency.

### Stakeholder
Pessoa interessada no progresso técnico mas sem background técnico profundo (ex: PM, Product, C-Level).

### Strategic Pillar
Objetivo estratégico de negócio definido no `.devbridge.yaml` (ex: "Aumentar conversão", "Reduzir dívida técnica").

---

## T

### Tech Debt (Dívida Técnica)
Trabalho técnico pendente que acumula custo ao longo do tempo. Inclui refactoring, atualizações, documentação.

### Trabalho Invisível
Trabalho técnico que não resulta em features visíveis mas é essencial (refactoring, infraestrutura, testes).

### Tree-sitter
Parser incremental universal para código-fonte. DevBridge usa para entender estrutura de múltiplas linguagens.

---

## W

### Webhook
Callback HTTP que o GitHub envia quando eventos ocorrem (push, PR, etc.). DevBridge processa esses eventos.

---

## Adições

Para adicionar novos termos:
1. Insira em ordem alfabética
2. Use formato: `### Termo` seguido de definição
3. Adicione contexto específico do DevBridge quando relevante
