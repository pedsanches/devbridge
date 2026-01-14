"use client";

import { MessageSquare, Sparkles, Search, Zap, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect, useCallback, useOptimistic, startTransition } from "react";
import { useRouter } from "next/navigation";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput, ChatInputHandle } from "@/components/chat/ChatInput";
import { PersonaSelector } from "@/components/chat/PersonaSelector";
import { RepositorySelectorContent } from "@/components/chat/RepositorySelector";
import { TeamSelectorContent } from "@/components/teams";
import { ChatToolbar } from "@/components/chat/ChatToolbar";
import { PeriodSelectorContent } from "@/components/chat/PeriodSelector";
import { ChatContextHeader } from "@/components/chat/ChatContextHeader";
import { sendChatMessageStream, Persona, Team, getTeam } from "@/services/api";
import { useKeyboardShortcuts, KeyboardShortcutsHint } from "@/hooks/useKeyboardShortcuts";

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
    isStreaming?: boolean | undefined;
    sources?: Source[] | undefined;
    activitiesCount?: number | undefined;
    confidenceScore?: number | undefined;
    metadata?: {
        search_method?: "semantic" | "sql" | undefined;
        confidence_score?: number | undefined;
    } | undefined;
}

interface ChatInterfaceProps {
    conversationId?: string;
    initialMessages?: Message[];
}

export function ChatInterface({ conversationId, initialMessages }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>(initialMessages || []);
    const [optimisticMessages, addOptimisticMessage] = useOptimistic(
        messages,
        (state, newMessage: Message) => [...state, newMessage]
    );
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [persona, setPersona] = useState<Persona>("product");
    const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
    const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
    const [days, setDays] = useState<number>(30);
    const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(conversationId);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const chatInputRef = useRef<ChatInputHandle>(null);
    const router = useRouter();

    const [activeSelector, setActiveSelector] = useState<"persona" | "team" | "repo" | "period" | null>(null);
    const [teamName, setTeamName] = useState<string>();

    // Keyboard shortcuts
    useKeyboardShortcuts({
        onFocusInput: () => chatInputRef.current?.focus(),
        onClearInput: () => chatInputRef.current?.clear(),
        onToggleSidebar: () => {
            // Optional: toggle sidebar via layout/context
        },
    });

    const toggleSelector = (selector: "persona" | "team" | "repo" | "period") => {
        setActiveSelector(prev => prev === selector ? null : selector);
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, optimisticMessages]);

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
    const handleTeamChange = (teamId: string | null, team: Team | null) => {
        setSelectedTeamId(teamId);
        setTeamName(team?.name);
        setActiveSelector(null); // Close on selection
    };
    // If team selected, load its repositories as default filter
    useEffect(() => {
        const loadTeamRepos = async () => {
            if (selectedTeamId) {
                try {
                    const teamDetail = await getTeam(selectedTeamId);
                    const repoNames = teamDetail.repositories.map(r => r.name);
                    setSelectedRepos(repoNames);
                } catch (err) {
                    console.error("Failed to load team repos:", err);
                }
            } else {
                setSelectedRepos([]);
            }
        };
        loadTeamRepos();
    }, [selectedTeamId]);


    const handleSendMessage = useCallback(async (content: string) => {
        setError(null);

        // Parse @mentions for repository filtering
        const mentionRegex = /@([\w\-]+)/g;
        const matches = [...content.matchAll(mentionRegex)];
        let repositories: string[] | undefined = undefined;

        const mentionedRepos = matches
            .map((match) => match[1])
            .filter((repo): repo is string => repo !== undefined);

        // Combine mentions and selected filters (unique values)
        if (mentionedRepos.length > 0 || selectedRepos.length > 0) {
            repositories = Array.from(new Set([...selectedRepos, ...mentionedRepos]));
        }

        // Add user message optimistically
        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content,
            timestamp: new Date().toLocaleTimeString("pt-BR", {
                hour: "2-digit",
                minute: "2-digit",
            }),
            confidenceScore: 1, // Optimistic
        };
        startTransition(() => {
            addOptimisticMessage(userMessage);
        });
        setIsLoading(true);

        // Prepare permanent state update (will happen when stream starts)
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

        // Track conversation ID from stream
        let streamConversationId: string | undefined = currentConversationId;

        // Stream the response
        await sendChatMessageStream(
            {
                message: content,
                persona,
                conversationId: currentConversationId,
                repository: repositories,
                days,
            },
            // onChunk
            (chunk) => {
                // Determine if this is the first chunk (to commit messages to state)
                setMessages((prev) => {
                    const messageExists = prev.some(m => m.id === userMessage.id);
                    if (!messageExists) {
                        return [...prev, userMessage, assistantMessage];
                    }

                    // Standard update logic for chunks
                    // Check if this is a metadata event
                    try {
                        const parsed = JSON.parse(chunk);
                        if (parsed.type === "metadata") {
                            // ... metadata handling ...
                            const newState = prev.map((msg) =>
                                msg.id === assistantId
                                    ? {
                                        ...msg,
                                        sources: parsed.sources,
                                        activitiesCount: parsed.activities_count,
                                        confidenceScore: parsed.confidence_score
                                    }
                                    : msg
                            );
                            return newState;
                        }
                    } catch { /* ... */ }

                    return prev.map((msg) =>
                        msg.id === assistantId
                            ? { ...msg, content: msg.content + chunk }
                            : msg
                    );
                });

                // ... Metadata side effects (conversationId) ...
                try {
                    const parsed = JSON.parse(chunk);
                    if (parsed.type === "metadata" && parsed.conversation_id) {
                        streamConversationId = parsed.conversation_id;
                        setCurrentConversationId(parsed.conversation_id);
                    }
                } catch { }
            },
            // onDone
            () => {
                // Ensure messages are committed if onChunk didn't fire (empty response cases?)
                setMessages(prev => {
                    const messageExists = prev.some(m => m.id === userMessage.id);
                    if (!messageExists) {
                        return [...prev, userMessage, { ...assistantMessage, isStreaming: false }];
                    }
                    return prev.map((msg) =>
                        msg.id === assistantId
                            ? { ...msg, isStreaming: false }
                            : msg
                    );
                });
                setIsLoading(false);

                // If we got a new conversation ID and we're on /chat (no ID), redirect
                if (streamConversationId && !conversationId) {
                    router.push(`/chat/${streamConversationId}`);
                }
            },
            // onError
            (err: any) => {
                setError(err.message);
                // Ensure messages are committed (with error state)
                setMessages(prev => {
                    const messageExists = prev.some(m => m.id === userMessage.id);
                    const errorAssistantMsg = {
                        ...assistantMessage,
                        content: "❌ Erro ao gerar resposta. Tente novamente.",
                        isStreaming: false,
                    };

                    if (!messageExists) {
                        return [...prev, userMessage, errorAssistantMsg];
                    }

                    return prev.map((msg) =>
                        msg.id === assistantId
                            ? errorAssistantMsg
                            : msg
                    );
                });
                setIsLoading(false);
            }
        );
    }, [persona, currentConversationId, conversationId, selectedRepos, router, days]);

    return (
        <div className="flex h-full flex-col bg-[var(--background)]">
            {/* Messages Area */}
            <main
                className="flex-1 overflow-y-auto"
                role="log"
                aria-live="polite"
                aria-busy={isLoading}
                aria-label="Histórico de mensagens"
            >
                <ChatContextHeader teamName={teamName} days={days} />
                <div className="container mx-auto max-w-3xl px-4 py-6">
                    {messages.length === 0 && optimisticMessages.length === 0 ? (
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
                                        className="rounded-full border border-[var(--border)] bg-[var(--card)] px-4 py-2 text-sm transition-colors hover:border-primary hover:text-primary"
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4 animate-stagger" role="list">
                            {optimisticMessages.map((message) => (
                                <div key={message.id}>
                                    <ChatMessage
                                        role={message.role}
                                        content={message.content}
                                        timestamp={message.timestamp}
                                        sources={message.sources}
                                        activitiesCount={message.activitiesCount}
                                        confidenceScore={message.confidenceScore}
                                        isStreaming={!!message.isStreaming}
                                    />
                                    {/* Streaming indicator */}
                                    {message.isStreaming && (
                                        <div className="ml-11 mt-1 flex items-center gap-1 text-xs text-[var(--muted-foreground)]">
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
            <footer className="sticky bottom-0 border-t border-[var(--border)] bg-[var(--card)]/80 backdrop-blur pb-6 pt-2">
                <div className="container mx-auto max-w-3xl relative">
                    {/* Popover Selection Area */}
                    {activeSelector && (
                        <div className="absolute bottom-full left-4 mb-2 z-20 w-72 rounded-xl border border-[var(--border)] bg-[var(--card)] shadow-xl animate-in fade-in slide-in-from-bottom-2">
                            {activeSelector === "persona" && (
                                <div className="p-2">
                                    <PersonaSelector
                                        selected={persona}
                                        onChange={(p) => { setPersona(p); setActiveSelector(null); }}
                                    />
                                </div>
                            )}
                            {activeSelector === "team" && (
                                <TeamSelectorContent
                                    selectedTeamId={selectedTeamId}
                                    onTeamChange={handleTeamChange}
                                    allowAll
                                />
                            )}
                            {activeSelector === "repo" && (
                                <RepositorySelectorContent
                                    selectedRepos={selectedRepos}
                                    onChange={(repos) => { setSelectedRepos(repos); setActiveSelector(null); }}
                                />
                            )}
                            {activeSelector === "period" && (
                                <PeriodSelectorContent
                                    days={days}
                                    onChange={(d) => { setDays(d); setActiveSelector(null); }}
                                />
                            )}
                        </div>
                    )}

                    {/* Controls Row */}
                    <div className="mb-2">
                        <ChatToolbar
                            persona={persona}
                            selectedRepos={selectedRepos}
                            days={days}
                            selectedTeamId={selectedTeamId}
                            teamName={teamName}
                            onOpenPersonaSelector={() => toggleSelector("persona")}
                            onOpenRepoSelector={() => toggleSelector("repo")}
                            onOpenTeamSelector={() => toggleSelector("team")}
                            onOpenPeriodSelector={() => toggleSelector("period")}
                        />
                    </div>

                    <div className="px-4">
                        <ChatInput ref={chatInputRef} onSend={handleSendMessage} disabled={isLoading} />
                        <div className="mt-2 flex justify-end">
                            <KeyboardShortcutsHint />
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}
