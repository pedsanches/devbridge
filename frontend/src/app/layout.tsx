import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/hooks/use-auth";
import { GlobalHeader } from "@/components/layout/GlobalHeader";
import { ThemeProvider } from "@/components/layout/ThemeProvider";

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
                        <GlobalHeader />
                        {children}
                    </AuthProvider>
                </ThemeProvider>
            </body>
        </html>
    );
}
