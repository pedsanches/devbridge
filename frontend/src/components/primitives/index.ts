/**
 * Primitives - Atomic Design "Atoms"
 *
 * Smallest reusable UI components with CVA variants.
 * Each primitive should be:
 * - Single responsibility
 * - Fully typed with TypeScript
 * - Documented with JSDoc
 */

// Button
export { Button, buttonVariants } from "./Button";
export type { ButtonProps, ButtonVariants } from "./Button";

// Typography
export { Heading, Text, headingVariants, textVariants } from "./Typography";
export type {
    HeadingProps,
    TextProps,
    HeadingVariants,
    TextVariants,
} from "./Typography";

// Glass
export { Glass, glassVariants } from "./Glass";
export type { GlassProps, GlassVariants } from "./Glass";
