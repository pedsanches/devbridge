# UI Charter & Governance

Este documento define o "contrato visual" do DevBridge. Ele serve como fonte única de verdade para Agentes e humanos sobre **por que** a UI é como é e **quais limites** nunca devem ser cruzados.

## 🎯 Goal
A interface do DevBridge não é sobre estética, é sobre **confiança**. Deve traduzir dados técnicos complexos em *insights* de negócio acionáveis, com rastreabilidade absoluta. O usuário deve sentir que está pilotando uma ferramenta de precisão, não navegando em uma landing page de marketing.

## 👥 Users
- **Primary:** CTOs, Tech Leads, Engineering Managers (buscam dados para justificar decisões).
- **Secondary:** PMs e Stakeholders não-técnicos (buscam visibilidade sobre o "buraco negro" do desenvolvimento).

## 🚫 Non-Negotiables (Hard Rules)
1.  **Sem Glassmorphism / Blur Decorativo**: A UI deve ser nítida e de alto contraste.
2.  **Sem Cores Arbitrárias**: Cor é **semântica** (status, severidade, tipo de dado). Nunca use cor por "beleza".
3.  **Dados como First-Class Citizens**: Tabelas, logs e métricas têm prioridade sobre ilustrações ou white space excessivo.
4.  **Rastreabilidade (R#)**: Toda afirmação ou insight deve permitir drill-down até a evidência original (commit, diff, log).
5.  **Tokens Obrigatórios**: É proibido usar valores hardcoded (hex, px) em componentes. Valores literais são permitidos **APENAS** em `docs/design/foundations.md` e `frontend/src/app/globals.css`.
6.  **Fonte Única de Verdade**: `foundations.md` define os tokens. `globals.css` implementa. Componentes consomem. Tailwind mapeia 1:1.

## ⚠️ Anti-Patterns
- **"Dribbble Shot"**: UIs com sombras difusas gigantes, gradientes sem função e baixo contraste.
- **"Mystery Meat Navigation"**: Ícones sem label, ações escondidas em hovers não óbvios.
- **"Trust me, bro"**: Respostas da IA sem citar as fontes ou evidências técnicas.
- **Lorem Ipsum**: Nunca use dados falsos. Use dados de exemplo realistas se necessário.

## 🖥️ Interaction Surfaces
O sistema DevBridge interage com o usuário em três superfícies principais:

### 1. Assistive (Painel Lateral "Ask DevBridge")
- **Foco**: Diálogo, Q&A, refinamento de query.
- **UI**: Chat linear, cards compactos.
- **State**: Efêmero (histórico de sessão).

### 2. Embedded (Ações Inline)
- **Foco**: Contextualização imediata.
- **UI**: Chips, tooltips, botões pequenos dentro de tabelas/cards.
- **Exemplo**: Clicar em um commit SHA para ver a análise de impacto.

### 3. Apply/Preview (Ações de Mutação)
- **Foco**: Alterações de estado (criar docs, refatorar).
- **UI**: Modal ou Tela Cheia com Diff (Antes/Depois).
- **Regra**: Nenhuma ação destrutiva acontece sem confirmação explícita após preview.
