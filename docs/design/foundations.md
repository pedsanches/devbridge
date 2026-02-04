# Design Foundations

Design tokens e princípios fundamentais do DevBridge. **Este é o arquivo-fonte para Agentes.**

## 🛑 Regras de Ouro (Non-Negotiables)
16.  **Nunca hardcode (Exceto Aqui)**: Valores hex `#` ou px só podem existir neste arquivo e em `frontend/src/app/globals.css`. Todo o resto deve usar tokens.
7.  **Sempre token**: Use `var(--color-primary)` ou classes utilitárias mapeadas.
8.  **Consistência > Criatividade**: Se não existe um token para isso, não invente.

---

## 🎨 Cores Semânticas

| Token | Hex | Significado Rígido |
|-------|-----|--------------------|
| `--color-primary` | `#0071E3` | Ação principal, Links, Brand. |
| `--color-success` | `#34C759` | Sucesso confirmado, Melhoria de métrica, Teste passou. |
| `--color-warning` | `#FF9500` | Deprecation, Code Smell, High Complexity, Teste flaky. |
| `--color-error` | `#FF3B30` | Bug crítico, Falha de build, Vulnerabilidade, Regressão. |
| `--color-info` | `#007AFF` | Estado neutro, Logs info. |
| `--color-neutral` | `Scala Gray` | Estrutura, Texto, Bordas (veja abaixo). |

### Neutral Scale (Utilitarian / Technical)
Baseada em tons neutros industriais, focada em alto contraste para leitura de dados e código (inspirada em System UI/Inter).
- Backgrounds: `neutral-50` (App), `neutral-100` (Card), `white` (Input/Elevated).
- Borders: `neutral-200` (Subtle), `neutral-300` (Active).
- Text: `neutral-500` (Meta), `neutral-700` (Body), `neutral-900` (Titles).

---

## 🔤 Tipografia

**Font Family**: `Inter` (UI) e `JetBrains Mono` ou `SF Mono` (Code).

| Token | Size/LineHeight | Uso Canônico |
|-------|-----------------|--------------|
| `text-xs` | 11px / 1.4 | Badges, Reference Chips, Timestamps. |
| `text-sm` | 13px / 1.4 | **Padrão para Tabelas**, Logs, Listas densas. |
| `text-base` | 15px / 1.5 | Texto corrido, Chat messages, Descrições. |
| `text-lg` | 17px / 1.5 | H3, Insights Titles. |
| `text-xl` | 20px / 1.4 | H2, Page Titles. |
| `text-2xl` | 24px / 1.3 | H1, Hero Numbers. |

---

## 📐 Espaçamento (4pt Grid)

| Token | Pixels | Uso |
|-------|--------|-----|
| `space-1` | 4px | Atomic (icon + text). |
| `space-2` | 8px | **Padrão denso**. |
| `space-3` | 12px | Padrão confortável. |
| `space-4` | 16px | Padding de containers/cards. |
| `space-6` | 24px | Separação de seções. |
| `space-8` | 32px | Layout gaps. |

---

## 🔲 Radius & Shadows

**Radius**:
- `radius-sm` (4px/6px): Tags, Chips, Inputs compactos.
- `radius-md` (8px/10px): Cards, Botões padrão.
- `radius-lg` (12px/14px): Modais, Containers principais.

**Shadows** (Minimalistas):
- `shadow-sm`: Bordas sutis + 1px y-offset. Para inputs/cards low profile.
- `shadow-md`: Dropdowns, Popovers.
- `shadow-lg`: Modais e Paineis flutuantes.

---

## 📋 CSS Variables Reference

```css
:root {
  /* Semantic */
  --color-primary: #0071E3;
  --color-success: #34C759;
  --color-warning: #FF9500;
  --color-error: #FF3B30;

  /* Neutrals */
  --color-neutral-50: #FAFAFA;
  --color-neutral-100: #F5F5F7;
  --color-neutral-200: #E8E8ED;
  --color-neutral-300: #D2D2D7;
  --color-neutral-500: #6E6E73;
  --color-neutral-700: #3A3A3C;
  --color-neutral-900: #1D1D1F;

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```
