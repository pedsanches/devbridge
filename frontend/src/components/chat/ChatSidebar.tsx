"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, usePathname, useRouter } from "next/navigation";
import { Plus, MessageSquare, ChevronLeft, ChevronRight, Trash, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";
import { getConversations, deleteConversation, ConversationSummary } from "@/services/api";

export function ChatSidebar() {
    const [conversations, setConversations] = useState<ConversationSummary[]>([]);
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const params = useParams();
    const pathname = usePathname();
    const router = useRouter();
    const activeId = params?.chatId as string;

    const fetchConversations = async () => {
        try {
            setIsLoading(true);
            const data = await getConversations(50, 0);
            setConversations(data.conversations);
        } catch (error) {
            console.error("Failed to fetch conversations", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchConversations();
    }, [activeId, pathname]); // Refresh when changing chat or pathname to ensure new conversations appear

    const handleDelete = async (e: React.MouseEvent, id: string) => {
        e.preventDefault();
        e.stopPropagation();
        if (!confirm("Tem certeza que deseja apagar esta conversa?")) return;

        try {
            await deleteConversation(id);
            setConversations(conversations.filter((c) => c.id !== id));
            if (activeId === id) {
                router.push("/chat");
            }
        } catch (error) {
            console.error("Failed to delete conversation", error);
        }
    };

    const groupConversationsByDate = (convs: ConversationSummary[]) => {
        const today = new Date();
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const lastWeek = new Date();
        lastWeek.setDate(lastWeek.getDate() - 7);

        const groups: Record<string, ConversationSummary[]> = {
            "Hoje": [],
            "Ontem": [],
            "Últimos 7 dias": [],
            "Mais antigos": [],
        };

        convs.forEach((c) => {
            const date = new Date(c.updated_at);
            if (date.toDateString() === today.toDateString()) {
                groups["Hoje"]?.push(c);
            } else if (date.toDateString() === yesterday.toDateString()) {
                groups["Ontem"]?.push(c);
            } else if (date > lastWeek) {
                groups["Últimos 7 dias"]?.push(c);
            } else {
                groups["Mais antigos"]?.push(c);
            }
        });

        return groups;
    };

    const grouped = groupConversationsByDate(conversations);

    return (
        <aside
            className={cn(
                "relative flex h-full flex-col border-r border-neutral-200 bg-neutral-50 transition-all duration-300 dark:border-neutral-800 dark:bg-neutral-900",
                isCollapsed ? "w-16" : "w-72"
            )}
        >
            <div className="flex items-center justify-between p-4">
                {!isCollapsed && (
                    <Link
                        href="/chat"
                        className="flex flex-1 items-center gap-2 rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm font-medium shadow-sm transition-colors hover:bg-neutral-50 hover:text-primary dark:border-neutral-700 dark:bg-neutral-800 dark:hover:bg-neutral-700"
                    >
                        <Plus className="h-4 w-4" />
                        Nova conversa
                    </Link>
                )}
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className={cn(
                        "flex h-8 w-8 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-200 dark:text-neutral-400 dark:hover:bg-neutral-800",
                        isCollapsed && "mx-auto"
                    )}
                >
                    {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
                </button>
            </div>

            {isCollapsed ? (
                // Collapsed View
                <div className="flex flex-1 flex-col items-center gap-4 overflow-y-auto py-2">
                    <Link
                        href="/chat"
                        className={cn(
                            "flex h-10 w-10 items-center justify-center rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-800",
                            pathname === "/chat" && !activeId && "bg-neutral-200 text-primary dark:bg-neutral-800"
                        )}
                        title="Nova conversa"
                    >
                        <Plus className="h-5 w-5" />
                    </Link>
                    {conversations.map((c) => (
                        <Link
                            key={c.id}
                            href={`/chat/${c.id}`}
                            className={cn(
                                "flex h-10 w-10 items-center justify-center rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-800",
                                activeId === c.id && "bg-neutral-200 text-primary dark:bg-neutral-800"
                            )}
                            title={c.title}
                        >
                            <MessageSquare className="h-4 w-4" />
                        </Link>
                    ))}
                </div>
            ) : (
                // Expanded View
                <div className="flex-1 overflow-y-auto px-3 py-2">
                    {Object.entries(grouped).map(([label, items]) => (
                        items.length > 0 && (
                            <div key={label} className="mb-6">
                                <h3 className="mb-2 px-2 text-xs font-semibold uppercase text-neutral-500 dark:text-neutral-400">
                                    {label}
                                </h3>
                                <div className="space-y-1">
                                    {items.map((c) => (
                                        <div key={c.id} className="group relative">
                                            <Link
                                                href={`/chat/${c.id}`}
                                                className={cn(
                                                    "flex items-start gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors hover:bg-neutral-200 dark:hover:bg-neutral-800",
                                                    activeId === c.id
                                                        ? "bg-neutral-200 dark:bg-neutral-800"
                                                        : "text-neutral-600 dark:text-neutral-300"
                                                )}
                                            >
                                                <MessageSquare className={cn(
                                                    "h-4 w-4 shrink-0 mt-0.5",
                                                    activeId === c.id && "text-primary"
                                                )} />
                                                <div className="flex-1 min-w-0">
                                                    <span className={cn(
                                                        "block truncate",
                                                        activeId === c.id && "font-medium text-primary"
                                                    )}>
                                                        {c.title || "Nova conversa"}
                                                    </span>
                                                    {c.preview && (
                                                        <span className="block truncate text-xs text-neutral-400 dark:text-neutral-500 mt-0.5">
                                                            {c.preview}
                                                        </span>
                                                    )}
                                                </div>
                                            </Link>
                                            <button
                                                onClick={(e) => handleDelete(e, c.id)}
                                                className="absolute right-2 top-2.5 hidden rounded-md p-1 hover:bg-neutral-300 group-hover:block dark:hover:bg-neutral-700"
                                                aria-label="Apagar conversa"
                                            >
                                                <Trash className="h-3 w-3 text-neutral-500" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )
                    ))}

                    {conversations.length === 0 && !isLoading && (
                        <div className="flex flex-col items-center justify-center gap-2 py-8 text-center text-neutral-500">
                            <Calendar className="h-8 w-8 opacity-20" />
                            <p className="text-xs">Nenhuma conversa recente</p>
                        </div>
                    )}
                </div>
            )}
        </aside>
    );
}
