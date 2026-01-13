"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { getConversation, ChatMessage } from "@/services/api";
import { Loader2 } from "lucide-react";

export default function ChatIdPage() {
    const params = useParams();
    const chatId = params.chatId as string;
    const [messages, setMessages] = useState<{
        id: string;
        role: "user" | "assistant";
        content: string;
        timestamp: string;
        metadata?: Record<string, unknown> | undefined;
    }[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadConversation() {
            try {
                setIsLoading(true);
                const data = await getConversation(chatId);

                // Map API messages to ChatInterface format
                const mappedMessages = data.messages.map((msg: ChatMessage) => {
                    const meta = msg.message_metadata as Record<string, unknown> | null;
                    return {
                        id: msg.id,
                        role: msg.role,
                        content: msg.content,
                        timestamp: new Date(msg.created_at).toLocaleTimeString("pt-BR", {
                            hour: "2-digit",
                            minute: "2-digit",
                        }),
                        metadata: msg.message_metadata,
                        sources: meta?.sources as string[] | undefined,
                        activitiesCount: meta?.activities_count as number | undefined,
                        confidenceScore: meta?.confidence_score as number | undefined,
                    };
                });

                setMessages(mappedMessages);
            } catch (err) {
                console.error("Failed to load conversation", err);
                setError("Não foi possível carregar a conversa.");
            } finally {
                setIsLoading(false);
            }
        }

        if (chatId) {
            loadConversation();
        }
    }, [chatId]);

    if (isLoading) {
        return (
            <div className="flex h-full items-center justify-center bg-neutral-50 dark:bg-neutral-900">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-full items-center justify-center bg-neutral-50 dark:bg-neutral-900">
                <div className="text-center">
                    <h3 className="text-lg font-semibold text-neutral-900 dark:text-white">Erro</h3>
                    <p className="text-neutral-500">{error}</p>
                </div>
            </div>
        );
    }

    return <ChatInterface conversationId={chatId} initialMessages={messages} />;
}
