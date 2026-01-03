"use client";

import { usePathname } from "next/navigation";
import { Header } from "./Header";

export function GlobalHeader() {
    const pathname = usePathname();

    // Determine variant based on path
    const getVariant = () => {
        if (pathname === "/login" || pathname === "/auth/verify") {
            return "auth";
        }
        if (pathname === "/chat") {
            // Chat uses the unified header but might want 'minimal' style logic if we strictly separated them again,
            // but per previous unification, it shares the main structure.
            // We'll pass 'minimal' to trigger the specific back-button logic we kept in Header.tsx
            return "minimal";
        }
        return "default";
    };

    // Determine props based on variant
    const variant = getVariant();
    const props = {
        variant: variant as "default" | "minimal" | "auth",
        // Logic for back button in chat
        ...(variant === "minimal" && {
            backHref: "/",
            backLabel: "Voltar"
        })
    };

    return <Header {...props} />;
}
