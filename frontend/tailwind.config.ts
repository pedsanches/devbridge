import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "var(--background)",
                foreground: "var(--foreground)",
                primary: {
                    DEFAULT: "var(--color-primary)",
                    hover: "var(--color-primary-hover)",
                },
                secondary: "var(--color-secondary)",
                success: "var(--color-success)",
                warning: "var(--color-warning)",
                error: "var(--color-error)",
                neutral: {
                    50: "var(--color-neutral-50)",
                    100: "var(--color-neutral-100)",
                    200: "var(--color-neutral-200)",
                    300: "var(--color-neutral-300)",
                    400: "var(--color-neutral-400)",
                    500: "var(--color-neutral-500)",
                    600: "var(--color-neutral-600)",
                    700: "var(--color-neutral-700)",
                    800: "var(--color-neutral-800)",
                    900: "var(--color-neutral-900)",
                },
            },
            fontFamily: {
                sans: "var(--font-sans)",
                mono: "var(--font-mono)",
            },
            borderRadius: {
                sm: "var(--radius-sm)",
                md: "var(--radius-md)",
                lg: "var(--radius-lg)",
                xl: "var(--radius-xl)",
                full: "var(--radius-full)",
            },
            boxShadow: {
                sm: "var(--shadow-sm)",
                md: "var(--shadow-md)",
                lg: "var(--shadow-lg)",
                xl: "var(--shadow-xl)",
            },
        },
    },
    plugins: [require("@tailwindcss/typography")],
};
export default config;
