# Brand Assets & Logo

## 1. Logo Canônico

O único arquivo fonte da verdade atualmente é o raster.

- **Path Oficial**: `/frontend/public/logo.png`
- **Uso**: Web, Favicon, Relatórios.

> [!CAUTION]
> **TODO: Vectorization**. A vetorização do logo (SVG) é prioritária para garantir escalabilidade. Até lá, use o PNG respeitando limites de resolução.
> **Issue**: #LogoVector (To be created)

## 2. Regras de Aplicação

### Cores e Fundos
O logo atual foi desenhado para fundo **claro**.
- **Dark Mode**: O logo deve ser envelopado ou usado em sua versão invertida (ainda não disponível).
    - *Bypass Temporário*: Use um container branco com border-radius suave se precisar aplicar sobre fundo escuro, ou opacity reduction se for marca d'água.

### Clear Space & Tamanho
- **Clear Space**: `0.5x` a largura do logo de respiro em volta.
- **Tamanhos Recomendados**:
    - Navbar: `h-8`
    - Footer: `h-6`
    - Login/Hero: `h-16`

## 3. Componente React (Padrão)

Use o componente `Next/Image` para otimização automática.

```tsx
// Exemplo de Implementação
import Image from "next/image";

export const BrandLogo = ({ size = "base" }: { size?: "sm" | "base" | "lg" }) => {
  const sizes = { sm: "h-6 w-auto", base: "h-8 w-auto", lg: "h-16 w-auto" };

  return (
    <div className={`relative ${sizes[size]}`}>
      <Image
        src="/logo.png"
        alt="DevBridge Logo"
        fill
        className="object-contain" // Garante aspect-ratio
        priority
      />
    </div>
  );
};
```
