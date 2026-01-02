# Brand Identity

Identidade visual e diretrizes de marca do DevBridge.

---

## 🎯 Essência da Marca

### Propósito
> **Tornando o trabalho técnico visível para stakeholders não-técnicos.**

### Personalidade

| Atributo | Expressão |
|----------|-----------|
| **Profissional** | Design limpo, sem excessos |
| **Confiável** | Consistência visual, previsibilidade |
| **Inteligente** | Detalhes sutis, organização lógica |
| **Acessível** | Linguagem clara, hierarquia óbvia |

---

## 🏷️ Logo

### Uso Principal

O logo do DevBridge consiste no ícone + wordmark.

```
┌─────────────────────────────┐
│   🌉  DevBridge             │
│   [icon] [wordmark]         │
└─────────────────────────────┘
```

### Variantes

| Variante | Uso |
|----------|-----|
| **Full (Icon + Wordmark)** | Headers, marketing |
| **Icon Only** | Favicon, app icons, espaços pequenos |
| **Wordmark Only** | Documentos formais |

### Espaço de Proteção

Manter **1x** do tamanho do ícone ao redor do logo.

```
    ┌─────────────────┐
    │     ░░░░░░░     │
    │   ░ LOGO ░░░    │
    │     ░░░░░░░     │
    └─────────────────┘
```

### Tamanhos Mínimos

| Formato | Mínimo |
|---------|--------|
| Full Logo | 120px largura |
| Icon Only | 24px |
| Favicon | 16px |

### Cores do Logo

| Contexto | Versão |
|----------|--------|
| Fundo claro | Logo em `--color-neutral-900` |
| Fundo escuro | Logo em `white` |
| Accent | Logo em `--color-primary` |

> [!WARNING]
> Nunca altere as cores do logo fora das versões aprovadas.

---

## 🎨 Cor Primária da Marca

| Nome | Hex | RGB |
|------|-----|-----|
| DevBridge Blue | `#0071E3` | `rgb(0, 113, 227)` |

Esta cor deve ser usada para:
- CTAs principais
- Links
- Elementos de destaque
- Ícones de ação

---

## 🔤 Tipografia da Marca

### Font Principal: Inter

**Por que Inter?**
- Open source e gratuita
- Excelente legibilidade em telas
- Compatível com SF Pro (Apple)
- Suporta muitos idiomas

### Hierarquia Tipográfica para Marketing

| Nível | Size | Weight |
|-------|------|--------|
| H1 | 48px | Bold (700) |
| H2 | 34px | Semibold (600) |
| H3 | 24px | Semibold (600) |
| Body | 17px | Regular (400) |
| Caption | 13px | Regular (400) |

---

## 🎭 Iconografia

### Biblioteca Padrão: Lucide

[Lucide Icons](https://lucide.dev) é a biblioteca oficial de ícones.

**Razões:**
- Consistente com estética Apple
- Stroke width uniforme
- Open source
- Fácil integração com React

### Tamanhos de Ícones

| Contexto | Size |
|----------|------|
| Inline (texto) | 16px |
| Buttons | 18px |
| Navigation | 20px |
| Feature | 24px |
| Large | 32px |

### Stroke Width

Padrão: **1.5px** (default do Lucide)

> [!TIP]
> Nunca misture ícones de bibliotecas diferentes.

---

## 🗣️ Voz e Tom

### Voz (constante)

| Característica | Descrição |
|----------------|-----------|
| **Clara** | Sem jargões desnecessários |
| **Direta** | Frases curtas, objetivas |
| **Empática** | Entende o problema do usuário |
| **Profissional** | Formal, mas não frio |

### Tom (varia por contexto)

| Contexto | Tom |
|----------|-----|
| Onboarding | Acolhedor, paciente |
| Erros | Calmo, solucionador |
| Sucesso | Breve, celebratório |
| Documentação | Neutro, técnico |

### Exemplos

| ❌ Evite | ✅ Use |
|----------|-------|
| "Oops! Algo deu errado..." | "Não foi possível completar a ação. Tente novamente." |
| "Dados super importantes!" | "Informações essenciais" |
| "Clique aqui" | "Ver detalhes" |

---

## 📁 Assets

### Onde Encontrar

| Asset | Localização |
|-------|-------------|
| Logo (SVG/PNG) | `/public/brand/logo/` |
| Ícones customizados | `/public/icons/` |
| Ilustrações | `/public/illustrations/` |

### Formatos

| Tipo | Formatos |
|------|----------|
| Logo | SVG (preferencial), PNG |
| Ícones | SVG |
| Imagens | WebP (preferencial), PNG |

---

## ✅ Checklist de Marca

Antes de publicar qualquer material visual:

- [ ] Logo está na versão correta?
- [ ] Espaço de proteção respeitado?
- [ ] Cores da paleta oficial?
- [ ] Tipografia Inter?
- [ ] Ícones Lucide?
- [ ] Tom de voz apropriado?
