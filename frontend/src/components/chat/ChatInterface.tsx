"use client";

import { MessageSquare, Sparkles, Search, Zap } from "lucide-react";
import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { PersonaSelector } from "@/components/chat/PersonaSelector";
import { RepositorySelector } from "@/components/chat/RepositorySelector";
import { TeamSelector } from "@/components/teams";
import { sendChatMessageStream, Persona, Team, getTeam } from "@/services/api";

interface Source {
    title: string;
    repository: string;
    type: string;
    author?: string | null;
    url?: string | null;
}

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: string;
    isStreaming?: boolean;
    sources?: Source[];
    activitiesCount?: number;
    confidenceScore?: number;
    metadata?: {
        search_method?: "semantic" | "sql";
        confidence_score?: number;
    };
}

interface ChatInterfaceProps {
    conversationId?: string;
    initialMessages?: Message[];
}

export function ChatInterface({ conversationId, initialMessages }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>(initialMessages || []);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [persona, setPersona] = useState<Persona>("product");
    const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
    const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
    const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(conversationId);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const router = useRouter();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Update messages if initialMessages change (e.g. navigation)
    useEffect(() => {
        if (initialMessages) {
            setMessages(initialMessages);
        }
    }, [initialMessages]);

    // Sync currentConversationId with prop when it changes
    useEffect(() => {
        setCurrentConversationId(conversationId);
    }, [conversationId]);

    // Handle team selection - load team repos
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const handleTeamChange = useCallback(async (teamId: string | null, _team: Team | null) => {
        setSelectedTeamId(teamId);

        // If team selected, load its repositories as default filter
        if (teamId) {
            try {
                const teamDetail = await getTeam(teamId);
                const repoNames = teamDetail.repositories.map(r => r.name);
                setSelectedRepos(repoNames);
            } catch (err) {
                console.error("Failed to load team repos:", err);
            }
        } else {
            setSelectedRepos([]);
        }
    }, []);

    const handleSendMessage = useCallback(async (content: string) => {
        setError(null);

        // Parse @mentions for repository filtering
        const mentionRegex = /@([\w\-]+)/g;
        const matches = [...content.matchAll(mentionRegex)];
        let repositories: string[] | undefined = undefined;

        const mentionedRepos = matches.map((match) => match[1]);

        // Combine mentions and selected filters (unique values)
        if (mentionedRepos.length > 0 || selectedRepos.length > 0) {
            repositories = Array.from(new Set([...selectedRepos, ...mentionedRepos]));
        }

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

        // Create streaming assistant message
        const assistantId = (Date.now() + 1).toString();
        const assistantMessage: Message = {
            id: assistantId,
            role: "assistant",
            content: "",
            timestamp: new Date().toLocaleTimeString("pt-BR", {
                hour: "2-digit",
                minute: "2-digit",
            }),
            isStreaming: true,
        };
        setMessages((prev) => [...prev, assistantMessage]);

        // Track conversation ID from stream
        let streamConversationId: string | undefined = currentConversationId;

        // Stream the response
        await sendChatMessageStream(
            {
                message: content,
                persona,
                conversationId: currentConversationId,
                repository: repositories,
            },
            // onChunk
            (chunk) => {
                // Check if this is a metadata event
                try {
                    const parsed = JSON.parse(chunk);
                    if (parsed.type === "metadata") {
                        if (parsed.conversation_id) {
                            streamConversationId = parsed.conversation_id;
                            setCurrentConversationId(parsed.conversation_id);
                        }
                        // Update message with sources from metadata
                        if (parsed.sources) {
                            setMessages((prev) =>
                                prev.map((msg) =>
                                    msg.id === assistantId
                                        ? {
                                            ...msg,
                                            sources: parsed.sources,
                                            activitiesCount: parsed.activities_count,
                                            confidenceScore: parsed.confidence_score
                                        }
                                        : msg
                                )
                            );
                        }
                        return; // Don't add metadata to message content
                    }
                } catch {
                    // Not JSON, it's a text chunk
                }

                setMessages((prev) =>
                    prev.map((msg) =>
                        msg.id === assistantId
                            ? { ...msg, content: msg.content + chunk }
                            : msg
                    )
                );
            },
            // onDone
            () => {
                setMessages((prev) =>
                    prev.map((msg) =>
                        msg.id === assistantId
                            ? { ...msg, isStreaming: false }
                            : msg
                    )
                );
                setIsLoading(false);

                // If we got a new conversation ID and we're on /chat (no ID), redirect
                if (streamConversationId && !conversationId) {
                    router.push(`/chat/${streamConversationId}`);
                }
            },
            // onError
            (err) => {
                setError(err.message);
                setMessages((prev) =>
                    prev.map((msg) =>
                        msg.id === assistantId
                            ? {
                                ...msg,
                                content: "❌ Erro ao gerar resposta. Tente novamente.",
                                isStreaming: false,
                            }
                            : msg
                    )
                );
                setIsLoading(false);
            }
        );
    }, [persona, conversationId, selectedRepos, router]);

    return (
        <div className="flex h-full flex-col bg-neutral-50 dark:bg-neutral-900">
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

                            {/* Persona Info */}
                            <div className="mt-4 flex items-center gap-2 text-xs text-neutral-500">
                                <Zap className="h-3 w-3" />
                                <span>Selecione o perfil abaixo para adaptar as respostas</span>
                            </div>

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
                                <div key={message.id}>
                                    <ChatMessage
                                        role={message.role}
                                        content={message.content}
                                        timestamp={message.timestamp}
                                        sources={message.sources}
                                        activitiesCount={message.activitiesCount}
                                        confidenceScore={message.confidenceScore}
                                    />
                                    {/* Streaming indicator */}
                                    {message.isStreaming && (
                                        <div className="ml-11 mt-1 flex items-center gap-1 text-xs text-neutral-400">
                                            <Sparkles className="h-3 w-3 animate-pulse" />
                                            <span>Gerando resposta...</span>
                                        </div>
                                    )}
                                </div>
                            ))}
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
                    {/* Controls Row */}
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                        <div className="flex flex-wrap gap-2">
                            <TeamSelector
                                selectedTeamId={selectedTeamId}
                                onTeamChange={handleTeamChange}
                                disabled={isLoading}
                                allowAll={true}
                            />
                            <PersonaSelector
                                selected={persona}
                                onChange={setPersona}
                                disabled={isLoading}
                            />
                            <RepositorySelector
                                selectedRepos={selectedRepos}
                                onChange={setSelectedRepos}
                                disabled={isLoading}
                            />
                        </div>

                        <div className="flex items-center gap-1 text-xs text-neutral-400">
                            <Search className="h-3 w-3" />
                            <span>RAG ativo</span>
                        </div>
                    </div>
                    <ChatInput onSend={handleSendMessage} disabled={isLoading} />
                </div>
            </footer>
        </div>
    );
}
