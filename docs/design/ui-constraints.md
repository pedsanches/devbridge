# UI Constraints & Rules

Restrições técnicas e objetivas para manter a consistência e a "saúde" do sistema de design. Agentes devem validar suas propostas de UI contra estas regras.

## 🎨 Token System Constraints

### Paleta de Cores
- **Neutral é rei**: 90% da interface deve ser tons de cinza (`neutral-50` a `neutral-900`).
- **Accent sob demanda**: Use `primary` apenas para ações principais e links.
- **Semântica estrita**:
  - `success`: Apenas para conclusões positivas confirmadas.
  - `warning`: Apenas para degrades de performance ou atenção necessária.
  - `error`: Falhas, bugs críticos, blockers.
  - `info`: Notas de contexto neutras.

### Tipografia & Densidade
- **Escala**: Use `text-sm` (13px) como padrão para dados densos (tabelas, logs). `text-base` (15px) para leitura.
- **Line Height**: Reduzida em componentes de dados (1.2 a 1.3) para compactação.
- **Mono**: Use `font-mono` para todos os identificadores técnicos: SHA, IDs, nomes de arquivos, paths, stack traces.

### Espaçamento
- **Grid de 4px**: Todos os spacings são múltiplos de 4 (ex: 4, 8, 12, 16, 24).
- **Densidade**: Prefira "Compact" por padrão em dashboards. "Comfortable" apenas em páginas de leitura (docs).

## 📐 Layout Rules

### Grids & Estrutura
- **Sidebar Fixa**: A navegação principal e o contexto do agente residem na esquerda ou direita, fixos.
- **Conteúdo Scrollável**: O centro da tela é para consumo de conteúdo.
- **Cards como Unity**: O conteúdo é agupado em Cards (`bg-surface`, `border-neutral`).

### Comportamento de Tabelas (Critical)
- **Sticky Headers**: Obrigatório para tabelas longas.
- **Pagination vs Infinite Scroll**:
  - Dados finitos (< 100 itens): Listagem completa.
  - Dados massivos (Logs, Commits): Paginação numerada.
  - *Nunca usar infinite scroll para dados que precisam de busca/ctrl+f.*

## 📝 Content Rules

### Writing Style
- **Headlines**: Verbo + Objeto ("Analisar Repositório", "Gerar Report").
- **Labels**: Curtos e diretos ("Status", "Owner", "Time").
- **Empty States**: Sempre explicar *por que* está vazio e *o que fazer* para preencher.
  - ❌ "Sem dados"
  - ✅ "Nenhum commit encontrado na branch 'main'. Tente alterar o filtro de data."

### Evidências (Obrigatório)
Qualquer bloco de insight gerado por IA deve ter uma seção ou rodapé de "Evidências":
- Lista de arquivos analisados.
- IDs de commits ou PRs.
- Trechos de logs relevantes.

## ⚡ Performance & Interação
- **Feedback Visual (< 100ms)**: Todo clique deve ter resposta visual imediata (estado `:active`, mudança de cor, borda).
- **Resposta Útil (SLA)**:
  - Ações locais: < 100ms.
  - Ações de IA/Fetch: Mostrar Skeleton ou Spinner imediatamente. O conteúdo pode levar mais tempo, mas a UI não pode travar.
- **Não bloqueante**: Ações longas da IA devem ir para background (Toasts/Notifications), liberando a UI.
