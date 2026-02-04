# Canonical Components

Lista de componentes oficiais do DevBridge. **Agentes devem usar estes blocos de construção para criar interfaces.**

---

## 🧠 Business Components (Core)

Estes são os componentes exclusivos do domínio do DevBridge.

### 1. InsightCard
Um container para exibir uma conclusão inteligente da IA.
- **Props**: `title`, `severity` (info/success/warn/error), `confidence` (high/med/low).
- **Slot**: `content` (texto), `actions` (botões), `evidence` (lista).
- **Uso**: Resultado de uma análise de PR, review de código, ou sugestão de arquitetura.

### 2. EvidenceTable
Tabela densa otimizada para dados técnicos.
- **Features Obrigatórias**: Sticky header, Fonte monospace para colunas de ID/Path.
- **Estilo**: Bordas sutis, zebra-striping opcional em alta densidade.
- **Uso**: Listar commits, arquivos alterados, linhas de log, violações de lint.

### 3. ReferenceChip (R#)
O menor átomo de rastreabilidade. Um link clicável que leva à fonte.
- **Variantes**:
  - `Code`: `📄 path/to/file.py:45`
  - `Commit`: `🔗 a1b2c3d`
  - `Rule`: `📜 BR-021`
- **Comportamento**: Ao clicar, abre o arquivo/diff no contexto lateral ou em nova aba.

### 4. DeltaIndicator
Mostra mudança numérica ou de estado.
- **Visual**: Ícone seta (↑/↓/→) + Valor + Cor semântica.
- **Exemplos**:
  - `↑ 15% Complexity` (Red/Warning)
  - `↓ 200ms Latency` (Green/Success)
  - `+ 3 Files` (Neutral)

### 5. TimelineRow
Linha única em uma lista de eventos cronológicos.
- **Layout**: [Hora/Data] -- [Linha Conectora] -- [Ícone Status] -- [Conteúdo].
- **Uso**: Logs de execução, histórico de chat, trilha de auditoria.

### 6. AIResponseBlock (Insight Block)
O wrapper padrão para toda comunicação inteligente da IA.

#### Slots Obrigatórios
1.  **Header**:
    - `Title`: Resumo curto da intenção (ex: "Análise de PR").
    - `ConfidenceBadge`: Nível de certeza (`High`=Verde, `Med`=Amarelo, `Low`=Vermelho).
2.  **Summary**: Texto explicativo direto (`text-base`).
3.  **Evidence List** (Obrigatório se houver afirmação técnica):
    - Lista de `ReferenceChip` apontando para commits, arquivos ou logs.
4.  **Actions**:
    - Botões de ação (`Primary` para correção, `Ghost` para ignorar).
5.  **Feedback**:
    - Curto (👍/👎) para RLHF.

#### Visual
- **Borda**: `border-l-4` colorida baseada na Confiança/Status.
- **Background**: `bg-neutral-50` (sutil destaque do chat normal).

---

## 🧱 UI Primitives (Base)

Componentes genéricos adaptados para a marca.

### Button
- **Primary**: Azul sólido (`bg-primary`). Apenas 1 por tela/card.
- **Secondary**: Cinza claro (`bg-neutral-100`).
- **Ghost**: Apenas texto/ícone. Para ações em tabelas/listas.

### StatusBadge
Badge arredondado (Pill) com cor de fundo suave e texto forte.
- `Success`: `bg-success-subtle` + `text-success`.
- `Warning`: `bg-warning-subtle` + `text-warning`.

### EmptyState
Componente placeholder para quando não há dados.
- **Anatomia**: Ícone (grande, cinza) + Título ("Nenhum commit") + Descrição + Ação CTA (opcional).
- **Regra**: Nunca deixe um espaço em branco "misterioso".

### SkeletonLoader
Indicador de carregamento que mimetiza a estrutura do conteúdo.
- **Uso**: Enquanto a IA processa ou busca dados no backend. Substitui spinners genéricos em áreas de conteúdo.

---

## 🚫 Don't Do This
- **NUNCA** crie cards com sombras gigantes ou bordas coloridas sem motivo semântico.
- **NUNCA** use botões primários vermelhos a menos que seja uma ação destrutiva irreversível (Ex: Delete Repo).
- **NUNCA** coloque texto longo (logs) sem container scrollável (`max-h-XXX overflow-y-auto`).
