"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, FileText, GitCommit, GitPullRequest, CircleDot, Shield } from "lucide-react";

interface Source {
    title: string;
    repository: string;
    type: string;
    author?: string | null;
    url?: string | null;
}

interface SourcesIndicatorProps {
    sources: Source[];
    activitiesCount: number;
    confidenceScore?: number | undefined;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
    commit: <GitCommit className="h-3.5 w-3.5" />,
    pr: <GitPullRequest className="h-3.5 w-3.5" />,
    pull_request: <GitPullRequest className="h-3.5 w-3.5" />,
    issue: <CircleDot className="h-3.5 w-3.5" />,
    default: <FileText className="h-3.5 w-3.5" />,
};

function getConfidenceLabel(score: number): { label: string; color: string } {
    if (score >= 0.7) return { label: "High confidence", color: "text-green-600 dark:text-green-400" };
    if (score >= 0.5) return { label: "Medium confidence", color: "text-yellow-600 dark:text-yellow-400" };
    return { label: "Low confidence", color: "text-orange-600 dark:text-orange-400" };
}

export function SourcesIndicator({ sources, activitiesCount, confidenceScore }: SourcesIndicatorProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    if (sources.length === 0) {
        return null;
    }

    const confidence = confidenceScore !== undefined ? getConfidenceLabel(confidenceScore) : null;

    return (
        <div className="mt-2 text-xs">
            <div className="flex items-center gap-3">
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center gap-1 text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 transition-colors"
                >
                    <FileText className="h-3.5 w-3.5" />
                    <span>Based on {activitiesCount} source{activitiesCount !== 1 ? "s" : ""}</span>
                    {isExpanded ? (
                        <ChevronUp className="h-3.5 w-3.5" />
                    ) : (
                        <ChevronDown className="h-3.5 w-3.5" />
                    )}
                </button>
                {confidence && (
                    <span className={`flex items-center gap-1 ${confidence.color}`}>
                        <Shield className="h-3 w-3" />
                        {confidence.label}
                    </span>
                )}
            </div>

            {isExpanded && (
                <ul className="mt-2 space-y-1.5 pl-4 border-l-2 border-neutral-200 dark:border-neutral-700">
                    {sources.map((source, idx) => {
                        const icon = TYPE_ICONS[source.type.toLowerCase()] || TYPE_ICONS.default;
                        return (
                            <li key={idx} className="flex items-start gap-2 text-neutral-600 dark:text-neutral-300">
                                <span className="mt-0.5 text-neutral-400">{icon}</span>
                                <div className="flex-1 min-w-0">
                                    {source.url ? (
                                        <a
                                            href={source.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="hover:underline text-primary truncate block"
                                        >
                                            {source.title}
                                        </a>
                                    ) : (
                                        <span className="truncate block">{source.title}</span>
                                    )}
                                    <span className="text-neutral-400 text-[10px]">
                                        {source.repository}
                                        {source.author && ` • ${source.author}`}
                                    </span>
                                </div>
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
}
