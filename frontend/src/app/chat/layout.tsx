"use client";

import { ChatSidebar } from "@/components/chat/ChatSidebar";

export default function ChatLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <div className="flex h-[calc(100vh-64px)] w-full overflow-hidden">
            <ChatSidebar />
            <div className="flex-1 bg-white dark:bg-neutral-950">
                {children}
            </div>
        </div>
    );
}
