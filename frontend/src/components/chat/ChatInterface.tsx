"use client";

import { MessageSquare, Sparkles, Zap, ArrowDown } from "lucide-react";
import { useState, useRef, useEffect, useCallback, useOptimistic, startTransition } from "react";

const STREAM_FLUSH_INTERVAL_MS = 80;
const STREAM_MIN_CHARS_PER_FLUSH = 48;
const STREAM_MAX_DEBOUNCE_MS = 150;

function shouldFlushForMarkdown(text: string): boolean {
    if (text.includes("\n\n")) return true;
    if (/\n(?:-|\*|\+)\s/.test(text)) return true;
    if (/\n\d+\.\s/.test(text)) return true;
    if (/\n>\s/.test(text)) return true;
    if (/\n#{1,6}\s/.test(text)) return true;
    return false;
}
import { useRouter } from "next/navigation";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput, ChatInputHandle } from "@/components/chat/ChatInput";
import { PersonaSelector } from "@/components/chat/PersonaSelector";
import { RepositorySelectorContent } from "@/components/chat/RepositorySelector";
import { TeamSelectorContent } from "@/components/teams";
import { ChatToolbar } from "@/components/chat/ChatToolbar";
import { PeriodSelectorContent } from "@/components/chat/PeriodSelector";
import { ChatContextHeader } from "@/components/chat/ChatContextHeader";
import { sendChatMessageStream, Persona, Team, getTeam, FeedbackType } from "@/services/api";
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
    confidenceExplanation?: string | undefined;
    metadata?: {
        search_method?: "semantic" | "sql" | undefined;
        confidence_score?: number | undefined;
    } | undefined;
    // Lineage & Feedback
    generationId?: string | undefined;
    promptVersionId?: string | undefined;
    traceId?: string | undefined;
    feedbackSelection?: FeedbackType | null | undefined;
}

export interface ConversationContext {
    teamId?: string | null;
    persona?: Persona | null;
    days?: number | null;
    repositories?: string[] | null;
}

interface ChatInterfaceProps {
    conversationId?: string;
    initialMessages?: Message[];
    initialContext?: ConversationContext;
}

export function ChatInterface({ conversationId, initialMessages, initialContext }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>(initialMessages || []);

    const streamingBufferRef = useRef<string>("");
    const streamingMetadataQueueRef = useRef<string[]>([]);
    const flushTimerRef = useRef<number | null>(null);
    const lastFlushAtRef = useRef<number>(0);
    const [optimisticMessages, addOptimisticMessage] = useOptimistic(
        messages,
        (state, newMessage: Message) => {
            if (state.some((m) => m.id === newMessage.id)) {
                return state;
            }
            return [...state, newMessage];
        }
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

    const scrollContainerRef = useRef<HTMLElement | null>(null);
    const shouldAutoScrollRef = useRef(true);

    const [activeSelector, setActiveSelector] = useState<"persona" | "team" | "repo" | "period" | null>(null);
    const [teamName, setTeamName] = useState<string>();
    const [pendingSuggestion, setPendingSuggestion] = useState<string | null>(null);

    const [showScrollToBottom, setShowScrollToBottom] = useState(false);

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

    const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
        if (!shouldAutoScrollRef.current) return;
        messagesEndRef.current?.scrollIntoView({ behavior });
    };

    useEffect(() => {
        const hasStreaming = optimisticMessages.some((m) => m.isStreaming);
        scrollToBottom(hasStreaming ? "auto" : "smooth");
    }, [messages, optimisticMessages]);

    useEffect(() => {
        const container = scrollContainerRef.current;
        if (!container) return;

        const onScroll = () => {
            const thresholdPx = 80;
            const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
            const shouldAutoScroll = distanceFromBottom < thresholdPx;
            shouldAutoScrollRef.current = shouldAutoScroll;
            setShowScrollToBottom(!shouldAutoScroll);
        };

        // initialize once
        onScroll();
        container.addEventListener("scroll", onScroll, { passive: true });
        return () => container.removeEventListener("scroll", onScroll);
    }, []);

    // Apply saved conversation context when loading an existing conversation
    useEffect(() => {
        if (initialContext) {
            if (initialContext.teamId) setSelectedTeamId(initialContext.teamId);
            if (initialContext.persona) setPersona(initialContext.persona as Persona);
            if (initialContext.days) setDays(initialContext.days);
            if (initialContext.repositories && initialContext.repositories.length > 0) {
                setSelectedRepos(initialContext.repositories);
            }
        }
    }, [initialContext]);

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
        const baseId = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;

        const userMessage: Message = {
            id: `${baseId}-user`,
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

        // Also commit to the base messages state to avoid duplicates when optimistic
        // state and server-driven state updates interleave.
        setMessages((prev) => {
            const exists = prev.some((m) => m.id === userMessage.id);
            return exists ? prev : [...prev, userMessage];
        });
        setIsLoading(true);

        // Prepare permanent state update (will happen when stream starts)
        const assistantId = `${baseId}-assistant`;
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

        // Commit the assistant placeholder immediately (so the UI updates even if the server
        // takes a while to send the first SSE chunk).
        setMessages((prev) => {
            const userExists = prev.some((m) => m.id === userMessage.id);
            const assistantExists = prev.some((m) => m.id === assistantMessage.id);

            if (!userExists && !assistantExists) return [...prev, userMessage, assistantMessage];
            if (!userExists) return [...prev, userMessage];
            if (!assistantExists) return [...prev, assistantMessage];
            return prev;
        });

        // Stream the response
        await sendChatMessageStream(
            {
                message: content,
                persona,
                conversationId: currentConversationId,
                repository: repositories,
                days,
                teamId: selectedTeamId ?? undefined,
            },
            // onEvent
            (event) => {
                // First event: commit messages to state once.
                setMessages((prev) => {
                    const messageExists = prev.some((m) => m.id === userMessage.id);
                    if (!messageExists) return [...prev, userMessage, assistantMessage];
                    return prev;
                });

                // Queue data for the next flush.
                if (event.type === "metadata") {
                    const metadataChunk = JSON.stringify(event);
                    streamingMetadataQueueRef.current.push(metadataChunk);

                    if (event.conversation_id) {
                        streamConversationId = event.conversation_id;
                        setCurrentConversationId(event.conversation_id);
                    }
                }

                if (event.type === "delta") {
                    streamingBufferRef.current += event.text;
                }


                // Smooth flushing: avoid too many tiny updates AND avoid giant delayed jumps.
                // We flush when either:
                // - we have enough text (min chars) AND the interval has elapsed, OR
                // - we've waited too long since last flush (max debounce), OR
                // - we got metadata (flush soon to show sources/count early).
                const now = Date.now();
                const timeSinceLastFlush = now - lastFlushAtRef.current;
                const shouldFlushSoon =
                    shouldFlushForMarkdown(streamingBufferRef.current) ||
                    streamingBufferRef.current.length >= STREAM_MIN_CHARS_PER_FLUSH ||
                    timeSinceLastFlush >= STREAM_MAX_DEBOUNCE_MS ||
                    streamingMetadataQueueRef.current.length > 0;

                if (shouldFlushSoon && flushTimerRef.current == null) {
                    const delay = Math.max(0, STREAM_FLUSH_INTERVAL_MS - timeSinceLastFlush);

                    flushTimerRef.current = window.setTimeout(() => {
                        flushTimerRef.current = null;
                        lastFlushAtRef.current = Date.now();

                        const pendingText = streamingBufferRef.current;
                        streamingBufferRef.current = "";

                        const pendingMetadata = streamingMetadataQueueRef.current;
                        streamingMetadataQueueRef.current = [];

                        setMessages((prev) =>
                            prev.map((msg) => {
                                if (msg.id !== assistantId) return msg;

                                let nextMsg: Message = msg;

                                if (pendingText.length > 0) {
                                    nextMsg = { ...nextMsg, content: nextMsg.content + pendingText };
                                }

                                for (const metadataChunk of pendingMetadata) {
                                    try {
                                        const metadata = JSON.parse(metadataChunk) as {
                                            type?: unknown;
                                            sources?: Source[];
                                            activities_count?: number;
                                            confidence_score?: number;
                                            confidence_explanation?: string;
                                            generation_id?: string;
                                            prompt_version_id?: string;
                                            trace_id?: string;
                                        };

                                        if (metadata.type === "metadata") {
                                            nextMsg = {
                                                ...nextMsg,
                                                sources: metadata.sources,
                                                activitiesCount: metadata.activities_count,
                                                confidenceScore: metadata.confidence_score,
                                                confidenceExplanation: metadata.confidence_explanation,
                                                generationId: metadata.generation_id,
                                                promptVersionId: metadata.prompt_version_id,
                                                traceId: metadata.trace_id,
                                            };
                                        }
                                    } catch {
                                        // ignore
                                    }
                                }

                                return nextMsg;
                            })
                        );
                    }, delay);
                }
            },
            // onDone - receives server-generated message_id for feedback persistence
            (serverMessageId?: string) => {
                // Force a final flush (so Streamdown gets the complete markdown).
                if (flushTimerRef.current != null) {
                    window.clearTimeout(flushTimerRef.current);
                    flushTimerRef.current = null;
                }
                lastFlushAtRef.current = Date.now();

                const pendingText = streamingBufferRef.current;
                streamingBufferRef.current = "";

                const pendingMetadata = streamingMetadataQueueRef.current;
                streamingMetadataQueueRef.current = [];

                setMessages((prev) => {
                    const messageExists = prev.some((m) => m.id === userMessage.id);
                    let next = prev;
                    if (!messageExists) {
                        next = [...prev, userMessage, { ...assistantMessage, isStreaming: false }];
                    }

                    return next.map((msg) => {
                        if (msg.id !== assistantId) return msg;

                        let nextMsg: Message = msg;
                        if (pendingText.length > 0) {
                            nextMsg = { ...nextMsg, content: nextMsg.content + pendingText };
                        }

                        for (const metadataChunk of pendingMetadata) {
                            try {
                                const metadata = JSON.parse(metadataChunk) as {
                                    type?: unknown;
                                    sources?: Source[];
                                    activities_count?: number;
                                    confidence_score?: number;
                                    confidence_explanation?: string;
                                    generation_id?: string;
                                    prompt_version_id?: string;
                                    trace_id?: string;
                                };

                                if (metadata.type === "metadata") {
                                    nextMsg = {
                                        ...nextMsg,
                                        sources: metadata.sources,
                                        activitiesCount: metadata.activities_count,
                                        confidenceScore: metadata.confidence_score,
                                        confidenceExplanation: metadata.confidence_explanation,
                                        generationId: metadata.generation_id,
                                        promptVersionId: metadata.prompt_version_id,
                                        traceId: metadata.trace_id,
                                    };
                                }
                            } catch {
                                // ignore
                            }
                        }

                        // Use server-generated message ID if available (critical for feedback persistence)
                        const finalId = serverMessageId ?? msg.id;
                        return { ...nextMsg, id: finalId, isStreaming: false };
                    });
                });

                setIsLoading(false);
                setPendingSuggestion(null);

                if (streamConversationId && !conversationId) {
                    // Avoid "flash" at the end of the first streamed message by replacing
                    // instead of pushing a new entry (which can re-mount the page).
                    router.replace(`/chat/${streamConversationId}`);
                }
            },
            // onError
            (err: unknown) => {
                if (flushTimerRef.current != null) {
                    window.clearTimeout(flushTimerRef.current);
                    flushTimerRef.current = null;
                }
                streamingBufferRef.current = "";
                streamingMetadataQueueRef.current = [];

                const message = err instanceof Error ? err.message : "Erro desconhecido";
                setError(message);

                setMessages((prev) => {
                    const messageExists = prev.some((m) => m.id === userMessage.id);
                    const errorAssistantMsg: Message = {
                        ...assistantMessage,
                        content: "❌ Erro ao gerar resposta. Tente novamente.",
                        isStreaming: false,
                    };

                    if (!messageExists) return [...prev, userMessage, errorAssistantMsg];

                    return prev.map((msg) => (msg.id === assistantId ? errorAssistantMsg : msg));
                });

                setIsLoading(false);
                setPendingSuggestion(null);
            }
        );
    }, [addOptimisticMessage, persona, currentConversationId, conversationId, selectedRepos, router, days, selectedTeamId]);

    return (
        <div className="flex h-full flex-col bg-[var(--background)]">
            {/* Messages Area */}
            <main
                ref={(el) => {
                    scrollContainerRef.current = el;
                }}
                className="flex-1 overflow-y-auto"
                role="log"
                aria-live="polite"
                aria-busy={isLoading}
                aria-label="Histórico de mensagens"
            >
                <ChatContextHeader teamName={teamName} days={days} />
                <div className="container mx-auto max-w-3xl px-4 py-6 relative">
                    {showScrollToBottom && (
                        <div className="pointer-events-none sticky bottom-4 z-10 flex justify-center">
                            <button
                                type="button"
                                onClick={() => {
                                    shouldAutoScrollRef.current = true;
                                    setShowScrollToBottom(false);
                                    scrollToBottom("auto");
                                }}
                                className="pointer-events-auto inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--card)]/90 px-3 py-2 text-xs text-[var(--foreground)] shadow-md backdrop-blur transition hover:bg-[var(--muted)]"
                            >
                                <ArrowDown className="h-3.5 w-3.5" />
                                Voltar ao fim
                            </button>
                        </div>
                    )}
                    {messages.length === 0 && optimisticMessages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-16 text-center">
                            <div className="mb-4 rounded-full bg-primary/10 p-4">
                                <MessageSquare className="h-12 w-12 text-primary" />
                            </div>
                            <h2 className="mb-2 text-xl font-semibold">
                                Silêncio nos logs...
                            </h2>
                            <p className="max-w-md text-secondary">
                                Não detectamos código movido neste período.
                                Que tal checar os filtros de repositório?
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
                                        onClick={() => {
                                            setPendingSuggestion(suggestion);
                                            handleSendMessage(suggestion);
                                        }}
                                        disabled={!!pendingSuggestion}
                                        className={`
                                            rounded-full border px-4 py-2 text-sm transition-all flex items-center gap-2
                                            ${pendingSuggestion === suggestion
                                                ? "bg-primary text-white border-primary animate-pulse"
                                                : pendingSuggestion
                                                    ? "opacity-50 cursor-not-allowed border-[var(--border)] bg-[var(--card)]"
                                                    : "border-[var(--border)] bg-[var(--card)] hover:border-primary hover:text-primary"
                                            }
                                        `}
                                    >
                                        {pendingSuggestion === suggestion && (
                                            <Sparkles className="h-3 w-3 animate-spin" />
                                        )}
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4 animate-stagger" role="list">
                            {optimisticMessages.map((message) => {
                                // Skip empty streaming assistant messages to show "Thinking..." instead
                                if (message.role === 'assistant' && message.isStreaming && !message.content) {
                                    return null;
                                }
                                return (
                                    <div key={message.id}>
                                        <ChatMessage
                                            id={message.id}
                                            role={message.role}
                                            content={message.content}
                                            timestamp={message.timestamp}
                                            sources={message.sources}
                                            activitiesCount={message.activitiesCount}
                                            confidenceScore={message.confidenceScore}
                                            confidenceExplanation={message.confidenceExplanation}
                                            isStreaming={!!message.isStreaming}
                                            generationId={message.generationId}
                                            promptVersionId={message.promptVersionId}
                                            traceId={message.traceId}
                                            conversationId={currentConversationId}
                                            persona={persona}
                                            feedbackSelection={message.feedbackSelection}
                                            onFeedbackSelectionChange={(selection) => {
                                                setMessages((prev) =>
                                                    prev.map((m) =>
                                                        m.id === message.id ? { ...m, feedbackSelection: selection } : m
                                                    )
                                                );
                                            }}
                                        />

                                        {/* Streaming indicator */}
                                        {message.isStreaming && message.content && (
                                            <div className="ml-11 mt-1 flex items-center gap-1 text-xs text-[var(--muted-foreground)]">
                                                <Sparkles className="h-3 w-3 animate-pulse" />
                                                <span>Gerando resposta...</span>
                                            </div>
                                        )}
                                    </div>
                                )
                            })}

                            {/* Thinking indicator - shows when loading started but no assistant message yet (or it's empty/hidden) */}
                            {isLoading && !optimisticMessages.some(m => m.role === 'assistant' && m.isStreaming && m.content) && (
                                <div className="flex gap-3 justify-start">
                                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-white">
                                        <Sparkles className="h-4 w-4 animate-pulse" />
                                    </div>
                                    <div className="rounded-2xl px-4 py-3 bg-neutral-100 dark:bg-neutral-800">
                                        <div className="flex items-center gap-2">
                                            <div className="flex gap-1">
                                                <div className="h-2 w-2 rounded-full bg-neutral-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                                                <div className="h-2 w-2 rounded-full bg-neutral-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                                                <div className="h-2 w-2 rounded-full bg-neutral-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                                            </div>
                                            <span className="text-sm text-neutral-500">Pensando...</span>
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
                        <div className="mt-2 flex items-center justify-between text-xs text-neutral-400 px-1">
                            <span>As respostas baseiam-se em logs técnicos e não acessam dados financeiros.</span>
                            <KeyboardShortcutsHint />
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}
