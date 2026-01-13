# DevBridge Design System

> A comprehensive guide to the visual identity and UI components of DevBridge.

---

## 1. Brand Overview

**DevBridge** is a developer productivity platform that bridges the gap between code activity and business insights.

### Brand Values
- **Clarity** — Clean, intuitive interfaces
- **Modern** — Contemporary design patterns
- **Professional** — Enterprise-ready aesthetics
- **Accessible** — Inclusive for all users

---

## 2. Logo

### Primary Logo
The DevBridge logo combines a stylized bridge icon with modern typography, representing the connection between developers and business stakeholders.

### Logo Variations
| Variant | Use Case |
|---------|----------|
| **Primary** | Light backgrounds |
| **Inverted** | Dark backgrounds |
| **Monochrome** | Single-color contexts |
| **Icon Only** | Favicons, app icons |

### Clear Space
Maintain minimum padding equal to the height of the "D" in DevBridge around all sides.

### Minimum Size
- **Digital**: 24px height minimum
- **Print**: 10mm height minimum

### Incorrect Usage
- ❌ Do not stretch or distort
- ❌ Do not rotate
- ❌ Do not change colors outside brand palette
- ❌ Do not add effects (shadows, gradients)

---

## 3. Color Palette

### Primary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Primary** | `#0071E3` | `0, 113, 227` | CTAs, links, key elements |
| **Primary Hover** | `#0077ED` | `0, 119, 237` | Hover states |

### Semantic Colors

| Name | Hex | WCAG | Usage |
|------|-----|------|-------|
| **Success** | `#30A46C` | AA ✅ | Positive feedback |
| **Warning** | `#F5A623` | AA (large) | Caution states |
| **Error** | `#E5484D` | AA ✅ | Error states |

### Neutral Scale

```
50   #FAFAFA   ████  Background
100  #F5F5F7   ████  Subtle background
200  #E8E8ED   ████  Borders
300  #D2D2D7   ████  Disabled
400  #86868B   ████  Placeholder
500  #6E6E73   ████  Secondary text
600  #515154   ████  Body text
700  #3A3A3C   ████  Headings
800  #2C2C2E   ████  Dark mode card
900  #1D1D1F   ████  Dark mode text
```

### Dark Mode
All semantic colors automatically adapt:
- Background: `#0A0A0A`
- Foreground: `#FAFAFA`
- Cards: `#171717`
- Borders: `#262626`

---

## 4. Typography

### Font Stack

| Category | Font | Fallback |
|----------|------|----------|
| **Sans** | Inter | SF Pro, system-ui |
| **Mono** | JetBrains Mono | SF Mono, Consolas |

### Type Scale

| Name | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| `xs` | 12px | 400 | 1.5 | Captions |
| `sm` | 14px | 400 | 1.5 | Secondary text |
| `base` | 16px | 400 | 1.5 | Body text |
| `lg` | 18px | 500 | 1.5 | Lead text |
| `xl` | 20px | 600 | 1.25 | H4 |
| `2xl` | 24px | 600 | 1.25 | H3 |
| `3xl` | 30px | 700 | 1.25 | H2 |
| `4xl` | 36px | 700 | 1.25 | H1 |

---

## 5. Spacing

Based on a 4px grid system:

| Token | Value | Usage |
|-------|-------|-------|
| `1` | 4px | Tight spacing |
| `2` | 8px | Component padding |
| `3` | 12px | Small gaps |
| `4` | 16px | Standard padding |
| `5` | 24px | Section spacing |
| `6` | 32px | Large gaps |
| `8` | 48px | Section breaks |
| `10` | 64px | Page sections |

---

## 6. Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | 6px | Buttons, inputs |
| `md` | 10px | Cards |
| `lg` | 14px | Modals |
| `xl` | 20px | Large containers |
| `full` | 9999px | Pills, avatars |

---

## 7. Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | `0 1px 2px rgba(0,0,0,0.04)` | Subtle elevation |
| `md` | `0 4px 12px rgba(0,0,0,0.08)` | Cards |
| `lg` | `0 12px 40px rgba(0,0,0,0.12)` | Dropdowns |
| `xl` | `0 24px 80px rgba(0,0,0,0.16)` | Modals |

---

## 8. Iconography

**Library**: [Lucide Icons](https://lucide.dev)

### Sizes
| Size | Pixels | Usage |
|------|--------|-------|
| `sm` | 16px | Inline, buttons |
| `md` | 20px | Navigation |
| `lg` | 24px | Headers |

### Style Guidelines
- Stroke width: 1.5px (default)
- Consistent with the minimalist brand aesthetic

---

## 9. Motion

### Duration
| Token | Value | Usage |
|-------|-------|-------|
| `fast` | 100ms | Micro-interactions |
| `normal` | 200ms | Standard transitions |
| `slow` | 300ms | Complex animations |

### Easing
| Token | Value | Usage |
|-------|-------|-------|
| `default` | `ease-out` | Most transitions |
| `spring` | `cubic-bezier(0.175, 0.885, 0.32, 1.275)` | Playful feedback |

---

## 10. Accessibility

### WCAG 2.1 AA Compliance
- ✅ All text has 4.5:1 contrast ratio minimum
- ✅ Interactive elements have visible focus states
- ✅ Color is not the only means of conveying information
- ✅ All interactive elements are keyboard accessible

### Focus States
```css
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

---

## Design Tokens

All design decisions are stored as tokens in:
- **Source**: `frontend/src/tokens/tokens.json`
- **Format**: W3C Design Tokens Community Group (DTCG)

---

*Last updated: January 2026*
