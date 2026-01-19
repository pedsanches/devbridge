import React from 'react';
import { Badge } from "@/components/ui/badge";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { GitPullRequest, GitCommit, FileText, AlertCircle, ExternalLink, MessageSquare } from "lucide-react";

// ============================================================================
// 1. Data Contracts (Matching Backend)
// ============================================================================

export enum ReferenceType {
    PULL_REQUEST = "pull_request",
    ISSUE = "issue",
    COMMIT = "commit",
    DOC = "doc",
    SLACK = "slack"
}

export interface ReportSource {
    ref_id: string;      // "R1"
    external_id?: string; // "PR #123"
    title: string;
    repository?: string;
    type: ReferenceType | string; // Support string for future types
    url?: string;
    description?: string;
    author?: {
        name: string;
        avatarUrl?: string;
    } | string; // Support simple string author
    status?: "open" | "merged" | "closed";
}

// ============================================================================
// 2. SmartReference Component
// ============================================================================

interface SmartReferenceProps {
    id: string; // The "R1" string
    source?: ReportSource;
}

const TYPE_ICONS: Record<string, React.ElementType> = {
    [ReferenceType.PULL_REQUEST]: GitPullRequest,
    [ReferenceType.ISSUE]: AlertCircle,
    [ReferenceType.COMMIT]: GitCommit,
    [ReferenceType.DOC]: FileText,
    [ReferenceType.SLACK]: MessageSquare,
};

const TYPE_COLORS: Record<string, string> = {
    [ReferenceType.PULL_REQUEST]: "text-purple-500 border-purple-200 dark:border-purple-800",
    [ReferenceType.ISSUE]: "text-green-500 border-green-200 dark:border-green-800",
    [ReferenceType.COMMIT]: "text-blue-500 border-blue-200 dark:border-blue-800",
    [ReferenceType.DOC]: "text-orange-500 border-orange-200 dark:border-orange-800",
    [ReferenceType.SLACK]: "text-pink-500 border-pink-200 dark:border-pink-800",
};

export const SmartReference: React.FC<SmartReferenceProps> = ({ id, source }) => {
    // ------------------------------------------------------------------------
    // FALLBACK STATE: No metadata found for this Ref ID
    // ------------------------------------------------------------------------
    if (!source) {
        return (
            <span className="text-muted-foreground/60 decoration-dotted underline decoration-red-400/50 cursor-help text-xs" title={`Reference ${id} not found`}>
                [{id}]
            </span>
        );
    }

    const typeKey = String(source.type);
    const Icon = TYPE_ICONS[typeKey] || FileText;
    const typeColorClass = TYPE_COLORS[typeKey] || "text-gray-500 border-gray-200";

    const authorName = typeof source.author === 'object' ? source.author?.name : source.author;
    const authorAvatar = typeof source.author === 'object' ? source.author?.avatarUrl : undefined;

    // ------------------------------------------------------------------------
    // MAIN RENDER
    // ------------------------------------------------------------------------
    return (
        <HoverCard openDelay={200} closeDelay={100}>
            <HoverCardTrigger asChild>
                <button
                    className="inline-flex items-center justify-center rounded bg-primary/5 hover:bg-primary/10 text-primary transition-colors cursor-pointer select-text mx-0.5 px-1 py-0.5 -translate-y-[1px]"
                    aria-label={`Reference ${id}: ${source.title}`}
                    onClick={(e) => {
                        // Click interaction: Open URL if exists
                        if (source.url) {
                            e.preventDefault();
                            e.stopPropagation();
                            window.open(source.url, '_blank');
                        }
                    }}
                >
                    <span className="text-[10px] font-bold leading-none tracking-tight">[{id}]</span>
                </button>
            </HoverCardTrigger>

            <HoverCardContent className="w-80 p-0 overflow-hidden shadow-xl border-border/50" align="start" sideOffset={8}>
                {/* HEADER */}
                <div className="bg-muted/50 p-3 border-b flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Badge variant="outline" className={`gap-1.5 bg-background h-6 ${typeColorClass} shadow-sm`}>
                            <Icon className="w-3 h-3" />
                            <span className="text-[10px] font-bold tracking-wider">{typeKey.replace(/_/g, ' ').toUpperCase()}</span>
                        </Badge>
                        <span className="text-xs font-mono text-muted-foreground/80 font-medium">
                            {source.external_id || id}
                        </span>
                    </div>
                </div>

                {/* BODY */}
                <div className="p-4 space-y-3 bg-card">
                    <div>
                        <h4 className="font-semibold text-sm leading-snug text-foreground/90">
                            {source.title}
                        </h4>
                        {source.repository && (
                            <p className="text-xs text-muted-foreground/70 mt-1.5 font-mono flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/30" />
                                {source.repository}
                            </p>
                        )}
                    </div>

                    {/* RELEVANCE/DESCRIPTION (Optional) */}
                    {source.description && (
                        <div className="text-xs text-muted-foreground bg-muted/30 p-2.5 rounded-md border border-border/50 italic">
                            "{source.description}"
                        </div>
                    )}

                    {/* AUTHOR & STATUS ROW */}
                    <div className="flex items-center justify-between pt-1">
                        {authorName && (
                            <div className="flex items-center gap-2">
                                <Avatar className="w-5 h-5 border border-border">
                                    <AvatarImage src={authorAvatar} />
                                    <AvatarFallback className="text-[9px] bg-muted text-muted-foreground">
                                        {authorName[0]?.toUpperCase()}
                                    </AvatarFallback>
                                </Avatar>
                                <span className="text-xs text-muted-foreground font-medium">{authorName}</span>
                            </div>
                        )}

                        {source.status && (
                            <Badge variant={source.status === 'merged' ? 'default' : 'secondary'} className="text-[10px] h-5 px-2 capitalize bg-primary/10 text-primary hover:bg-primary/20 border-primary/20">
                                {source.status}
                            </Badge>
                        )}
                    </div>
                </div>

                {/* FOOTER */}
                <div className="p-2 bg-muted/40 border-t flex justify-end">
                    {source.url ? (
                        <Button variant="ghost" size="sm" className="h-7 text-xs gap-1.5 hover:bg-primary/5 hover:text-primary" asChild>
                            <a href={source.url} target="_blank" rel="noopener noreferrer">
                                Open Source <ExternalLink className="w-3 h-3" />
                            </a>
                        </Button>
                    ) : (
                        <span className="text-[10px] text-muted-foreground px-2 py-1 italic">
                            No external link available
                        </span>
                    )}
                </div>
            </HoverCardContent>
        </HoverCard>
    );
};
