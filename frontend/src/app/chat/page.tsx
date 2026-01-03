"use client";

import { MessageSquare, Sparkles } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { sendChatMessage, ChatResponse } from "@/services/api";


interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: string;
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async (content: string) => {
        setError(null);

        // Add user message
        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content,
            timestamp: new Date().toLocaleTimeString("pt-BR", {
                hour: "2-digit",
                minute: "2-digit",
            }),
        };
        setMessages((prev) => [...prev, userMessage]);
        setIsLoading(true);

        try {
            const response: ChatResponse = await sendChatMessage({ message: content });

            // Add assistant message
            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: response.answer,
                timestamp: new Date().toLocaleTimeString("pt-BR", {
                    hour: "2-digit",
                    minute: "2-digit",
                }),
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao enviar mensagem");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen flex-col bg-neutral-50 dark:bg-neutral-900">


            {/* Messages Area */}
            <main className="flex-1 overflow-y-auto">
                <div className="container mx-auto max-w-3xl px-4 py-6">
                    {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-16 text-center">
                            <div className="mb-4 rounded-full bg-primary/10 p-4">
                                <MessageSquare className="h-8 w-8 text-primary" />
                            </div>
                            <h2 className="mb-2 text-xl font-semibold">
                                Converse sobre o trabalho do time
                            </h2>
                            <p className="max-w-md text-secondary">
                                Pergunte sobre commits, pull requests e atividades recentes.
                                A IA vai analisar os dados e responder em linguagem de negócio.
                            </p>
                            <div className="mt-6 flex flex-wrap justify-center gap-2">
                                {[
                                    "O que o time fez essa semana?",
                                    "Quais PRs foram abertos?",
                                    "Resumo das atividades",
                                ].map((suggestion) => (
                                    <button
                                        key={suggestion}
                                        onClick={() => handleSendMessage(suggestion)}
                                        className="rounded-full border border-neutral-200 bg-white px-4 py-2 text-sm transition-colors hover:border-primary hover:text-primary dark:border-neutral-700 dark:bg-neutral-800"
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {messages.map((message) => (
                                <ChatMessage
                                    key={message.id}
                                    role={message.role}
                                    content={message.content}
                                    timestamp={message.timestamp}
                                />
                            ))}
                            {isLoading && (
                                <div className="flex gap-3">
                                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-white">
                                        <Sparkles className="h-4 w-4 animate-pulse" />
                                    </div>
                                    <div className="rounded-2xl bg-neutral-100 px-4 py-3 dark:bg-neutral-800">
                                        <div className="flex gap-1">
                                            <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-400" style={{ animationDelay: "0ms" }} />
                                            <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-400" style={{ animationDelay: "150ms" }} />
                                            <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-400" style={{ animationDelay: "300ms" }} />
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    )}

                    {error && (
                        <div className="mt-4 rounded-lg bg-red-50 p-4 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
                            {error}
                        </div>
                    )}
                </div>
            </main>

            {/* Input Area */}
            <footer className="sticky bottom-0 border-t border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
                <div className="container mx-auto max-w-3xl">
                    <ChatInput onSend={handleSendMessage} disabled={isLoading} />
                </div>
            </footer>
        </div>
    );
}
