# Component Guidelines

Diretrizes para componentes de UI do DevBridge. Use em conjunto com `foundations.md` para os tokens.

---

## 🔘 Buttons

### Variantes

| Variante | Uso | Estilo |
|----------|-----|--------|
| **Primary** | Ação principal | `bg: primary`, `text: white` |
| **Secondary** | Ação secundária | `bg: neutral-100`, `text: neutral-900` |
| **Ghost** | Ação terciária | `bg: transparent`, `text: primary` |
| **Destructive** | Ações perigosas | `bg: error`, `text: white` |

### Tamanhos

| Size | Height | Padding | Font Size |
|------|--------|---------|-----------|
| `sm` | 32px | 12px 16px | 13px |
| `md` | 40px | 12px 20px | 15px |
| `lg` | 48px | 16px 24px | 17px |

### Exemplo CSS

```css
.button-primary {
  background: var(--color-primary);
  color: white;
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-md);
  font-weight: var(--font-medium);
  transition: background var(--duration-normal) var(--easing-default);
}

.button-primary:hover {
  background: var(--color-primary-hover);
}

.button-primary:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

---

## 📝 Inputs

### Text Input

| Estado | Border | Background |
|--------|--------|------------|
| Default | `neutral-200` | `white` |
| Hover | `neutral-300` | `white` |
| Focus | `primary` | `white` |
| Error | `error` | `white` |
| Disabled | `neutral-200` | `neutral-100` |

### Dimensões

| Propriedade | Valor |
|-------------|-------|
| Height | 40px |
| Padding | 12px 16px |
| Border Width | 1px |
| Border Radius | `--radius-sm` |

### Exemplo CSS

```css
.input {
  height: 40px;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
  transition: border-color var(--duration-fast);
}

.input:focus {
  border-color: var(--color-primary);
  outline: none;
}

.input--error {
  border-color: var(--color-error);
}
```

---

## 🃏 Cards

### Estrutura

```
┌─────────────────────────────┐
│  Header (opcional)          │
├─────────────────────────────┤
│                             │
│  Content                    │
│                             │
├─────────────────────────────┤
│  Footer (opcional)          │
└─────────────────────────────┘
```

### Tokens

| Propriedade | Valor |
|-------------|-------|
| Background | `--color-neutral-100` ou `white` |
| Border Radius | `--radius-lg` |
| Padding | `--space-4` (16px) |
| Shadow | `--shadow-md` |
| Gap interno | `--space-3` |

### Exemplo CSS

```css
.card {
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  box-shadow: var(--shadow-md);
}

.card-header {
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-neutral-200);
  margin-bottom: var(--space-3);
}
```

---

## 🔔 Toasts / Notifications

### Tipos

| Tipo | Cor de Fundo | Ícone |
|------|--------------|-------|
| Info | `primary` (10% opacity) | `Info` |
| Success | `success` (10% opacity) | `CheckCircle` |
| Warning | `warning` (10% opacity) | `AlertTriangle` |
| Error | `error` (10% opacity) | `XCircle` |

### Posicionamento
- Padrão: **Bottom Right**
- Stack: Máximo 3 toasts visíveis
- Auto-dismiss: 5 segundos

---

## 🪟 Modals

### Estrutura

| Elemento | Especificação |
|----------|---------------|
| Overlay | `rgba(0,0,0,0.5)` com blur (8px) |
| Container | `max-width: 480px`, `--radius-xl` |
| Padding | `--space-5` (24px) |
| Shadow | `--shadow-xl` |

### Animação de Entrada

```css
.modal-enter {
  opacity: 0;
  transform: scale(0.95);
}

.modal-enter-active {
  opacity: 1;
  transform: scale(1);
  transition: all var(--duration-slow) var(--easing-spring);
}
```

---

## 📐 Layout Patterns

### Sidebar Layout

```
┌──────────┬─────────────────────────────┐
│          │  Header                     │
│  Side    ├─────────────────────────────┤
│  bar     │                             │
│  (240px) │  Main Content               │
│          │                             │
└──────────┴─────────────────────────────┘
```

| Elemento | Largura |
|----------|---------|
| Sidebar | 240px (collapsible) |
| Content | Flex-grow |

### Responsive Breakpoints

| Breakpoint | Value | Sidebar |
|------------|-------|---------|
| Mobile | < 768px | Hidden |
| Tablet | 768px - 1024px | Collapsed (icons only) |
| Desktop | > 1024px | Full |

---

## ✅ Checklist para Novos Componentes

- [ ] Usa tokens do `foundations.md`
- [ ] Suporta Dark Mode
- [ ] Touch target mínimo de 44x44px
- [ ] Estado `:focus-visible` definido
- [ ] Transições suaves aplicadas
- [ ] Testado em mobile

> [!TIP]
> Use a biblioteca de ícones **Lucide** para consistência.
