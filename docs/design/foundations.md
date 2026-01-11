# Design Foundations

Design tokens e princípios fundamentais do DevBridge. **Este é o arquivo principal para agentes que precisam implementar UI.**

---

## 🎨 Cores

### Paleta Semântica

| Token | Hex | Uso |
|-------|-----|-----|
| `--color-primary` | `#0071E3` | Ações principais, links, CTAs |
| `--color-primary-hover` | `#0077ED` | Hover em elementos primários |
| `--color-secondary` | `#86868B` | Texto secundário, ícones inativos |
| `--color-success` | `#34C759` | Confirmações, status positivo |
| `--color-warning` | `#FF9500` | Alertas, atenção necessária |
| `--color-error` | `#FF3B30` | Erros, ações destrutivas |

### Escala de Cinzas (Neutral)

| Token | Hex | Uso |
|-------|-----|-----|
| `--color-neutral-50` | `#FAFAFA` | Background claro |
| `--color-neutral-100` | `#F5F5F7` | Cards, surfaces |
| `--color-neutral-200` | `#E8E8ED` | Bordas, divisores |
| `--color-neutral-300` | `#D2D2D7` | Bordas ativas |
| `--color-neutral-400` | `#86868B` | Texto desabilitado |
| `--color-neutral-500` | `#6E6E73` | Texto secundário |
| `--color-neutral-600` | `#515154` | Texto terciário |
| `--color-neutral-700` | `#3A3A3C` | Texto em dark mode |
| `--color-neutral-800` | `#2C2C2E` | Background dark |
| `--color-neutral-900` | `#1D1D1F` | Texto principal |

### Dark Mode

| Token Light | Token Dark |
|-------------|------------|
| `--color-neutral-50` | `--color-neutral-900` |
| `--color-neutral-900` | `--color-neutral-50` |

> [!IMPORTANT]
> Sempre use variáveis CSS, nunca valores hex diretos no código.

---

## 🔤 Tipografia

### Font Family

```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
--font-mono: 'SF Mono', 'Fira Code', 'Consolas', monospace;
```

### Escala Tipográfica

| Token | Size | Line Height | Weight | Uso |
|-------|------|-------------|--------|-----|
| `--text-xs` | 11px | 1.4 | 400 | Labels menores, badges |
| `--text-sm` | 13px | 1.4 | 400 | Texto auxiliar, captions |
| `--text-base` | 15px | 1.5 | 400 | Corpo de texto padrão |
| `--text-lg` | 17px | 1.5 | 500 | Subtítulos, ênfase |
| `--text-xl` | 21px | 1.4 | 600 | Títulos de seção |
| `--text-2xl` | 28px | 1.3 | 600 | Títulos de página |
| `--text-3xl` | 34px | 1.2 | 700 | Headlines principais |

### Font Weights

| Token | Value | Uso |
|-------|-------|-----|
| `--font-regular` | 400 | Texto corrido |
| `--font-medium` | 500 | Ênfase sutil |
| `--font-semibold` | 600 | Títulos, labels |
| `--font-bold` | 700 | Headlines |

> [!TIP]
> Evite pesos leves (300, 200) para garantir legibilidade.

---

## 📐 Espaçamento (8pt Grid)

Todos os valores de espaçamento seguem múltiplos de 8px.

| Token | Value | Uso |
|-------|-------|-----|
| `--space-1` | 4px | Micro espaçamento (ícone + texto) |
| `--space-2` | 8px | Espaçamento interno de componentes |
| `--space-3` | 12px | Gap entre elementos relacionados |
| `--space-4` | 16px | Padding padrão de cards |
| `--space-5` | 24px | Margem entre seções |
| `--space-6` | 32px | Espaçamento de layout |
| `--space-8` | 48px | Margens de página |
| `--space-10` | 64px | Separação de blocos maiores |

```css
/* Exemplo de uso */
.card {
  padding: var(--space-4);
  margin-bottom: var(--space-5);
}
```

---

## 🔲 Border Radius

| Token | Value | Uso |
|-------|-------|-----|
| `--radius-sm` | 6px | Inputs, badges |
| `--radius-md` | 10px | Buttons, cards menores |
| `--radius-lg` | 14px | Cards, modais |
| `--radius-xl` | 20px | Containers maiores |
| `--radius-full` | 9999px | Avatares, pills |

---

## 🌑 Sombras (Elevação)

| Token | Value | Uso |
|-------|-------|-----|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.04)` | Inputs, elementos sutis |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.08)` | Cards, dropdowns |
| `--shadow-lg` | `0 12px 40px rgba(0,0,0,0.12)` | Modais, popovers |
| `--shadow-xl` | `0 24px 80px rgba(0,0,0,0.16)` | Overlays flutuantes |

---

## ⏱️ Animações

| Token | Value | Uso |
|-------|-------|-----|
| `--duration-fast` | 100ms | Micro-interações |
| `--duration-normal` | 200ms | Transições padrão |
| `--duration-slow` | 300ms | Animações de entrada |
| `--easing-default` | `cubic-bezier(0.25, 0.1, 0.25, 1)` | Easing natural |
| `--easing-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Efeito bounce |

```css
/* Exemplo de uso */
.button {
  transition: all var(--duration-normal) var(--easing-default);
}
```

---

## ♿ Acessibilidade

| Regra | Valor |
|-------|-------|
| Contraste mínimo (texto) | 4.5:1 |
| Contraste recomendado | 7:1 |
| Touch target mínimo | 44x44px |
| Focus visible | Obrigatório em todos os interativos |

```css
/* Focus ring padrão */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

---

## 📋 CSS Variables (Copiar)

```css
:root {
  /* Colors */
  --color-primary: #0071E3;
  --color-primary-hover: #0077ED;
  --color-secondary: #86868B;
  --color-success: #34C759;
  --color-warning: #FF9500;
  --color-error: #FF3B30;

  /* Neutrals */
  --color-neutral-50: #FAFAFA;
  --color-neutral-100: #F5F5F7;
  --color-neutral-200: #E8E8ED;
  --color-neutral-300: #D2D2D7;
  --color-neutral-400: #86868B;
  --color-neutral-500: #6E6E73;
  --color-neutral-600: #515154;
  --color-neutral-700: #3A3A3C;
  --color-neutral-800: #2C2C2E;
  --color-neutral-900: #1D1D1F;

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
  --font-mono: 'SF Mono', 'Fira Code', 'Consolas', monospace;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-8: 48px;
  --space-10: 64px;

  /* Border Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 20px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 12px 40px rgba(0,0,0,0.12);
  --shadow-xl: 0 24px 80px rgba(0,0,0,0.16);

  /* Animation */
  --duration-fast: 100ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --easing-default: cubic-bezier(0.25, 0.1, 0.25, 1);
  --easing-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```
