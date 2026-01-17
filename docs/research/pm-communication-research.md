# Pesquisa: Comunicação de Trabalho Técnico para Product Managers

> **Objetivo:** Entender como PMs querem visualizar e comunicar o trabalho dos desenvolvedores.

---

## 1. Roteiro de Entrevista para PMs

### Preparação (5 min)
- Apresentar o DevBridge brevemente
- Explicar que estamos explorando como melhorar a comunicação entre devs e PMs
- Pedir permissão para gravar/anotar

### Bloco 1: Contexto Atual (10 min)

| # | Pergunta | Objetivo |
|---|----------|----------|
| 1 | "Como você acompanha o que o time está fazendo hoje?" | Entender workflow atual |
| 2 | "Com que frequência você precisa explicar progresso técnico para stakeholders?" | Medir demanda |
| 3 | "Qual a maior dificuldade em traduzir trabalho técnico para linguagem de negócio?" | Identificar pain points |

### Bloco 2: Comunicação com Stakeholders (15 min)

| # | Pergunta | Objetivo |
|---|----------|----------|
| 4 | "Quando um CEO ou sponsor pergunta 'o que o time entregou?', como você responde hoje?" | Descobrir formato preferido |
| 5 | "Que nível de detalhe técnico seus stakeholders toleram?" | Calibrar profundidade |
| 6 | "Como você comunica atrasos ou problemas? É 100% transparente ou 'suaviza'?" | Descobrir preferência de tom |
| 7 | "Você já recebeu feedback de que explicou algo técnico demais ou de menos?" | Identificar erros comuns |

### Bloco 3: Preferências de Formato (10 min)

| # | Pergunta | Objetivo |
|---|----------|----------|
| 8 | "Prefere receber resumos em bullets, texto corrido, ou números/métricas?" | Formato preferido |
| 9 | "Chat interativo ou relatório semanal automático?" | Frequência/canal |
| 10 | "Mostramos duas respostas diferentes para a mesma pergunta. Qual prefere?" | Teste A/B ao vivo |

### Bloco 4: Cenários Práticos (10 min)

**Cenário A:** "O time passou 2 semanas refatorando código. Como você explicaria isso para o CEO?"

**Cenário B:** "Uma feature atrasou 3 sprints por débito técnico. Como comunicar sem parecer desculpa?"

**Cenário C:** "O time não entregou nada visível, mas melhorou performance em 40%. Como mostrar valor?"

### Perguntas de Encerramento (5 min)

| # | Pergunta |
|---|----------|
| 11 | "Se pudesse mudar UMA coisa na comunicação dev-negócio, o que seria?" |
| 12 | "Algo que não perguntamos mas você gostaria de comentar?" |

---

## 2. Framework de Análise de Personas

### Dimensões de Comunicação

```
                    FORMAL
                       │
                       │
     EXECUTIVO ────────┼──────── TÉCNICO
     (Resumo)          │         (Detalhado)
                       │
                       │
                    CASUAL
```

### Matriz de Preferências por Persona

| Dimensão | PM (Produto) | CTO (Técnico) | CEO (Executivo) |
|----------|--------------|---------------|-----------------|
| **Linguagem** | Business-friendly | Termos técnicos OK | Zero jargão |
| **Profundidade** | Média | Alta | Mínima (bullets) |
| **Tom** | Colaborativo | Direto/objetivo | Confiante/estratégico |
| **Frequência** | Diário/conforme demanda | Semanal | Mensal/ad-hoc |
| **Métricas** | Entregas, velocidade | Coverage, complexity | ROI, headcount |
| **Formato** | Chat + resumos | Dashboards + chat | Reports executivos |
| **Sinceridade** | Transparente | Muito transparente | Calibrada/política |

### Template para Documentar Findings

```yaml
persona_id: pm_startup_series_a
profile:
  cargo: Product Manager
  empresa_tipo: Startup B2B SaaS
  time_size: 5-10 devs
  reporting_to: CEO direto

communication_needs:
  linguagem:
    preferencia: "business-friendly"
    quote: "Não quero saber de PR ou commit, quero saber se vai entregar"

  profundidade:
    preferencia: "média"
    quote: "Me diz o 'o quê' e o 'quando', não o 'como'"

  tom:
    preferencia: "transparente"
    quote: "Prefiro saber que vai atrasar cedo do que ter surpresa"

  formato:
    preferencia: "bullets + métricas"
    exemplo: "3 features entregues, 2 em progresso, 1 bloqueada"

pain_points:
  - "Devs explicam em linguagem que não entendo"
  - "Não sei o impacto de 'refactoring' em business value"
  - "CEO me cobra atualização e eu não sei o status real"

ideal_response_example: |
  **Esta semana:**
  ✅ Checkout otimizado (deve aumentar conversão ~2%)
  🔄 Integração Stripe 70% completa (entrega: próxima terça)
  ⚠️ Bug de pagamento resolvido (afetava 3% das transações)
```

---

## 3. Proposta de Experimento A/B

### Objetivo
Validar qual estilo de resposta gera mais satisfação em PMs.

### Hipótese
> PMs preferem respostas focadas em impacto de negócio e próximos passos,
> com tom confiante mas honesto sobre bloqueios.

### Variantes de Teste

#### Variante A: "Status Report" (Atual)
```
O time trabalhou em 3 PRs esta semana. O PR #123 implementou feature X,
o PR #124 corrigiu bug Y, e o PR #125 refatorou o módulo Z.
```

#### Variante B: "Outcome-Focused"
```
**Entregas da semana:**
- Feature X live → deve aumentar retenção em ~5%
- Bug de pagamento corrigido → afetava 200 transações/dia

**Em progresso:**
- Integração com Stripe (70%) → entrega estimada: terça-feira
```

#### Variante C: "Executive Brief"
```
✅ 2 entregas que impactam receita
🔄 1 projeto crítico no prazo
📊 Velocity: +15% vs mês anterior
```

### Métricas de Sucesso

| Métrica | Como medir |
|---------|-----------|
| **Satisfação** | Feedback thumbs up/down por resposta |
| **Clareza** | "Você entendeu o status do time?" (1-5) |
| **Acionabilidade** | "Você saberia o que responder ao CEO?" (sim/não) |
| **Preferência** | "Qual formato prefere?" (escolha forçada) |

### Implementação Técnica

```typescript
// Nova prop no PersonaSelector
interface CommunicationStyle {
  id: 'status_report' | 'outcome_focused' | 'executive_brief';
  name: string;
  promptModifier: string;
}

// A/B test no backend
const stylePrompts = {
  status_report: "Liste as atividades de forma cronológica...",
  outcome_focused: "Foque em resultados e impacto de negócio...",
  executive_brief: "Máximo 5 bullets, emoji de status, zero jargão..."
};
```

### Cronograma Sugerido

| Semana | Atividade |
|--------|-----------|
| 1 | Conduzir 5-8 entrevistas com PMs |
| 2 | Analisar findings, documentar personas |
| 3 | Implementar variantes A/B no chat |
| 4 | Rodar experimento com users beta |
| 5 | Analisar resultados, definir default |

---

---

## 4. Respostas Simuladas (Síntese de Comunidades)

> **Fontes:** Reddit r/ProductManagement, Hacker News, ProductPlan, Medium, Quora
> **Data da pesquisa:** Janeiro 2026

### Bloco 1: Contexto Atual

#### P1: "Como você acompanha o que o time está fazendo hoje?"

**Síntese das comunidades:**
- **Maioria usa Jira/Linear + standups diários**, mas reclama que é fragmentado
- Muitos PMs dependem de "perguntar diretamente" aos devs ou tech leads
- Spreadsheets manuais ainda são comuns para reportar para stakeholders
- **Dor principal:** "O processo de atualizar status é manual, propenso a erros e consome muito tempo"

> *"Uso Jira, mas tenho que acessar 3-4 dashboards diferentes e consolidar manualmente em um Google Sheet pro board meeting."* — PM em startup B2B

#### P2: "Com que frequência você precisa explicar progresso técnico para stakeholders?"

**Síntese:**
- **Diariamente** para times internos (design, marketing)
- **Semanalmente** para liderança/C-level
- **Ad-hoc** para board/investidores (mensal ou trimestral)
- CEOs frequentemente pedem "resumo de 30 segundos" sem aviso

> *"Meu CEO me para no corredor e pergunta 'e aí, como está a feature X?' — preciso ter isso na ponta da língua."*

#### P3: "Qual a maior dificuldade em traduzir trabalho técnico para linguagem de negócio?"

**Síntese dos pain points:**
1. **Devs explicam em jargão técnico** — "Eles falam de 'refactoring' e 'technical debt' mas não explicam o impacto"
2. **Dificuldade em quantificar valor de trabalho invisível** — manutenção, otimização, segurança
3. **Comunicar atrasos sem parecer desculpa** — "Como explico que 2 semanas de infra 'invisível' foi crucial?"
4. **Métricas de engenharia não traduzem para negócio** — "Story points não significam nada para o CEO"

> *"Refactoring é provavelmente o exemplo mais difícil. Como convencer o board que gastar 3 sprints em algo que o usuário não vê foi a coisa certa?"*

---

### Bloco 2: Comunicação com Stakeholders

#### P4: "Quando um CEO pergunta 'o que o time entregou?', como você responde?"

**Padrões identificados:**

| Formato | Frequência | Quando usar |
|---------|------------|-------------|
| **Bullets com emojis de status** | Mais comum | Updates rápidos, Slack |
| **"BLUF" (Bottom Line Up Front)** | Alta | Emails para executivos |
| **RAG (Red/Yellow/Green)** | Média | Reports semanais formais |
| **Narrative + métricas** | Menos comum | Board decks, investidores |

> *"Sempre começo com o impacto: 'Lançamos X e isso deve aumentar conversão em Y%'. Só depois entro em detalhes se pedirem."*

#### P5: "Que nível de detalhe técnico seus stakeholders toleram?"

**Matriz de tolerância (baseada em feedback da comunidade):**

| Stakeholder | Tolerância | Preferência |
|-------------|------------|-------------|
| CEO/Board | **Zero** | Impacto em receita/custos only |
| CFO | Mínima | Custo, ROI, headcount |
| CMO/Marketing | Baixa | Features, timing, UX |
| CTO | Alta | Arquitetura, tradeoffs |
| Devs do time | Total | Código, PRs, implementação |

> *"Regra geral: fale para o menor nível técnico da sala. Se tem um CEO presente, simplifique até ele entender."*

#### P6: "Como você comunica atrasos ou problemas? É 100% transparente?"

**Insights da comunidade:**

| Abordagem | Quando usar |
|-----------|-------------|
| **Transparência total + solução** | Time interno, CTO, eng leads |
| **Transparência calibrada** | CEO, board — foco em "como vamos resolver" |
| **Proativo, não reativo** | Sempre comunicar ANTES de virar crise |
| **Nunca culpar pessoas** | Foco no problema, não em quem errou |

> *"Comunico riscos CEDO. É muito melhor dizer 'podemos atrasar' com 3 semanas de antecedência do que dar surpresa no deadline."*

> *"Para o CEO, nunca uso 'technical debt' — digo 'investimento em estabilidade que vai acelerar a velocidade no próximo quarter'."*

#### P7: "Você já recebeu feedback de que explicou algo técnico demais?"

**Sim, é extremamente comum:**
- "Perdi o executivo na segunda frase"
- "Me pediram para 'traduzir em português'"
- "O board ficou impaciente quando comecei a falar de arquitetura"

**Também o oposto acontece:**
- "Devs sentiram que eu estava simplificando demais"
- "CTO queria mais profundidade técnica"

> *"Aprendi a ter versões diferentes do mesmo update: 1 frase para CEO, 3 bullets para VP, página inteira para o CTO."*

---

### Bloco 3: Preferências de Formato

#### P8: "Prefere bullets, texto corrido, ou métricas?"

**Consenso esmagador:**
1. **Bullets com contexto** > bullets puros > texto corrido
2. **Sempre incluir "so what?"** — o impacto de cada item
3. **Métricas quando relevantes**, mas não métricas por métricas
4. **Hierarquia visual** — títulos, status icons, cores

> *"Não quero só 'Feature X lançada'. Quero 'Feature X lançada → espera-se +15% em retenção'."*

**Estrutura mais citada (Reddit r/ProductManagement):**
```
📊 Status Semanal

**Conquistas:**
- ✅ Checkout otimizado (impacto: -40% tempo de loading)
- ✅ Bug crítico de pagamento corrigido

**Em progresso:**
- 🔄 Integração Stripe (70% completa, ETA: terça)

**Riscos:**
- ⚠️ API de terceiro instável (trabalhando em fallback)
```

#### P9: "Chat interativo ou relatório semanal automático?"

**Depende do caso de uso:**

| Uso | Formato preferido |
|-----|-------------------|
| Pergunta ad-hoc do CEO | **Chat rápido** |
| Status semanal para liderança | **Relatório estruturado** |
| Deep-dive mensal | **Dashboard + call** |
| Investigação de problema | **Chat interativo** |

> *"Quero os dois: relatório automático para não perder tempo, mas chat para quando preciso investigar algo específico."*

---

### Bloco 4: Cenários Práticos

#### Cenário A: "Como explicar 2 semanas de refactoring?"

**Melhores práticas identificadas:**

❌ **Evitar:** "Fizemos refactoring do módulo de pagamentos"

✅ **Preferir:** "Investimos em estabilidade do checkout. Resultado:
- Reduzimos bugs de pagamento em 60%
- Próximas features serão 2x mais rápidas de implementar
- Custo de manutenção cai ~30% no próximo quarter"

> *"Não use 'refactoring' com não-técnicos. Use 'investimento em velocidade futura' ou 'manutenção preventiva'."*

#### Cenário B: "Feature atrasou 3 sprints por débito técnico"

**Framework de comunicação:**

1. **Reconheça o atraso** (não esconda)
2. **Explique a causa em termos de negócio** (não técnicos)
3. **Mostre ação corretiva**
4. **Apresente nova data realista**

> *"A integração com parceiro X atrasou porque precisamos reescrever parte do sistema de autenticação. Isso era um risco conhecido que optamos por não resolver antes. Agora está corrigido e a feature estará pronta em 2 semanas, mas mais importante: esse tipo de atraso não vai mais acontecer."*

#### Cenário C: "Time melhorou performance em 40%, mas nada visível"

**Abordagem recomendada:**

1. **Traduza para impacto no usuário:** "Páginas carregam 40% mais rápido"
2. **Conecte com métricas de negócio:** "Isso historicamente melhora conversão em X%"
3. **Use comparação:** "Antes demorava 4 segundos, agora 2.4 segundos"
4. **Visualize se possível:** Side-by-side before/after

> *"Performance é mais fácil que refactoring porque dá pra mostrar. Faço um GIF comparativo: 'antes vs depois' — até o CEO entende."*

---

### Bloco 5: Insights Extras

#### O que PMs querem que NÃO têm hoje:

1. **Resumo automático** do que o time fez (sem perguntar)
2. **Tradução automática** de linguagem técnica → negócio
3. **Alertas proativos** de riscos antes de virarem problemas
4. **Templates prontos** para diferentes audiências (CEO vs CTO)
5. **Histórico pesquisável** de decisões e contexto

> *"Sonho com um assistente que me diz 'o time entregou X, Y, Z essa semana e o impacto esperado é W' sem eu ter que perguntar."*

#### O que devs reclamam sobre PMs:

1. "PM não entende o suficiente de tech para fazer boas perguntas"
2. "PM simplifica tanto que perde nuance importante"
3. "PM promete prazos sem consultar o time"
4. "PM não comunica o 'porquê' — só cobra entregas"

> *"Um bom PM traduz pro negócio MAS também entende o suficiente pra saber quando o dev está simplificando demais ou exagerando complexidade."*

---

## Implicações para o DevBridge

### Gaps no sistema atual:

| Gap | O que temos | O que PMs querem |
|-----|-------------|------------------|
| **Formato** | Texto corrido | Bullets + status + impacto |
| **Linguagem** | 1 tom por persona | Adaptação por audiência |
| **Proatividade** | Chat reativo | Resumos automáticos |
| **Sinceridade** | Mesmo tom sempre | Calibrada por stakeholder |
| **Contexto** | Por mensagem | Histórico + tendências |

### Melhorias prioritárias sugeridas:

1. **Estilo "Outcome-Focused"** como default para persona Product
2. **Template estruturado** com conquistas/progresso/riscos
3. **Modo "CEO-ready"** — máximo 3 bullets, zero jargão
4. **Tradução automática** de termos técnicos
5. **Resumos semanais automáticos** (não só chat)

---

## Próximos Passos

1. [x] ~~Pesquisar insights de comunidades~~
2. [ ] Validar findings com 2-3 PMs reais
3. [ ] Priorizar melhorias baseado em impacto/esforço
4. [ ] Implementar estilo "Outcome-Focused" como experimento
5. [ ] Iterar baseado em feedback de uso real
