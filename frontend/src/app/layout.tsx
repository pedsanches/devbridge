import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import "@/config/env";
import { AuthProvider } from "@/hooks/use-auth";
import { AppLayout } from "@/components/layout/AppLayout";
import { ThemeProvider } from "@/components/layout/ThemeProvider";
import { OnboardingProvider, WelcomeModal } from "@/components/onboarding";

const inter = Inter({
    subsets: ["latin"],
    variable: "--font-sans",
    display: "swap",
});

const outfit = Outfit({
    subsets: ["latin"],
    variable: "--font-heading",
    weight: ["500", "600", "700"],
    display: "swap",
});

export const metadata: Metadata = {
    title: "DevBridge",
    description: "Making Technical Work Visible to Non-Technical Stakeholders via AI Translation",
};

// Disabled because Next.js typed app exports don't accept it in our current setup.
// If we want view transitions later, re-enable it alongside the proper Next.js config/type support.
// export const experimental_viewTransition = true;

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={`${inter.variable} ${outfit.variable} font-sans`} suppressHydrationWarning>
                <ThemeProvider>
                    <AuthProvider>
                        <OnboardingProvider>
                            <WelcomeModal />
                            <AppLayout>{children}</AppLayout>
                        </OnboardingProvider>
                    </AuthProvider>
                </ThemeProvider>
            </body>
        </html>
    );
}
