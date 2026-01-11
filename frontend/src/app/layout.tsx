import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/hooks/use-auth";
import { AppLayout } from "@/components/layout/AppLayout";
import { ThemeProvider } from "@/components/layout/ThemeProvider";
import { OnboardingProvider, WelcomeModal } from "@/components/onboarding";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "DevBridge",
    description: "Making Technical Work Visible to Non-Technical Stakeholders via AI Translation",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={inter.className} suppressHydrationWarning>
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
