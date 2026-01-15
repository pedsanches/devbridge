"use client";

import { useState, useEffect, useCallback } from "react";
import {
    FileText,
    Loader2,
    Trash2,
    RefreshCw,
    FolderOpen,
    Star,
    Calendar,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { frontendEnv } from "@/config/env";

const API_BASE_URL = frontendEnv.apiBaseUrl;

// ============================================================
// Types
// ============================================================

interface TemplateListItem {
    id: string;
    name: string;
    description: string | null;
    is_default: boolean;
    created_at: string;
}

interface TemplateListResponse {
    items: TemplateListItem[];
    total: number;
    page: number;
    page_size: number;
}

export interface FullTemplate {
    id: string;
    name: string;
    description: string | null;
    is_default: boolean;
    data_filters: {
        repositories?: string[];
        authors?: string[];
        activity_types?: string[];
        impact_levels?: string[];
        value_tags?: string[];
        labels?: string[];
    } | null;
    sections_config: {
        type: string;
        title: string;
        enabled: boolean;
        order: number;
        detail_level: "minimal" | "normal" | "detailed";
        custom_prompt?: string;
    }[];
    language_config: {
        language: "pt-BR" | "en-US" | "es";
        formality: number;
        jargon_level: number;
        verbosity: number;
        tone: "neutral" | "optimistic" | "cautious";
        format: "bullets" | "paragraphs" | "mixed";
    } | null;
    visual_config: {
        primary_color: string;
        secondary_color: string;
        font_family: "Inter" | "Roboto" | "Arial";
        show_charts: boolean;
        watermark?: "CONFIDENTIAL" | "DRAFT" | null;
        header_style: "minimal" | "full";
    } | null;
    created_at: string;
    updated_at: string;
}

// ============================================================
// Helper Functions
// ============================================================

function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    });
}

// ============================================================
// Template Card Component
// ============================================================

function TemplateCard({
    template,
    onLoad,
    onDelete,
    isLoading,
}: {
    template: TemplateListItem;
    onLoad: () => void;
    onDelete: () => void;
    isLoading: boolean;
}) {
    return (
        <div
            className="group rounded-xl border border-[var(--border)] p-4 transition-all hover:border-primary/50 glass hover-lift"
        >
            <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                        <FileText className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                            <span className="font-medium text-[var(--foreground)] truncate">
                                {template.name}
                            </span>
                            {template.is_default && (
                                <Badge variant="secondary" className="text-xs">
                                    <Star className="h-3 w-3 mr-1" />
                                    Padrão
                                </Badge>
                            )}
                        </div>
                        {template.description && (
                            <p className="text-sm text-[var(--muted-foreground)] mt-1 line-clamp-2">
                                {template.description}
                            </p>
                        )}
                        <div className="flex items-center gap-1 text-xs text-[var(--muted-foreground)] mt-2">
                            <Calendar className="h-3 w-3" />
                            <span>{formatDate(template.created_at)}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-2 mt-4">
                <Button
                    variant="default"
                    size="sm"
                    onClick={onLoad}
                    disabled={isLoading}
                    className="flex-1"
                >
                    {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                        <FolderOpen className="h-4 w-4 mr-2" />
                    )}
                    Carregar
                </Button>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onDelete}
                    className="text-red-500 hover:text-red-600 hover:bg-red-100 dark:hover:bg-red-900/20"
                >
                    <Trash2 className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}

// ============================================================
// Main Component
// ============================================================

interface TemplatesManagerProps {
    onLoadTemplate: (template: FullTemplate) => void;
}

export default function TemplatesManager({ onLoadTemplate }: TemplatesManagerProps) {
    const [templates, setTemplates] = useState<TemplateListItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [loadingTemplateId, setLoadingTemplateId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(false);

    const fetchTemplates = useCallback(async (pageNum = 1) => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(
                `${API_BASE_URL}/report-templates?page=${pageNum}&page_size=12`,
                { credentials: "include" }
            );
            if (!response.ok) throw new Error("Falha ao carregar templates");
            const data: TemplateListResponse = await response.json();
            setTemplates(pageNum === 1 ? data.items : [...templates, ...data.items]);
            setHasMore(data.items.length === 12);
            setPage(pageNum);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro desconhecido");
        } finally {
            setIsLoading(false);
        }
    }, [templates]);

    useEffect(() => {
        fetchTemplates();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleLoadTemplate = async (templateId: string) => {
        setLoadingTemplateId(templateId);
        try {
            const response = await fetch(
                `${API_BASE_URL}/report-templates/${templateId}`,
                { credentials: "include" }
            );
            if (!response.ok) throw new Error("Falha ao carregar template");
            const fullTemplate: FullTemplate = await response.json();
            onLoadTemplate(fullTemplate);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao carregar template");
        } finally {
            setLoadingTemplateId(null);
        }
    };

    const handleDeleteTemplate = async (templateId: string, templateName: string) => {
        if (!confirm(`Deseja realmente excluir o template "${templateName}"?`)) return;

        try {
            const response = await fetch(
                `${API_BASE_URL}/report-templates/${templateId}`,
                { method: "DELETE", credentials: "include" }
            );
            if (!response.ok) throw new Error("Falha ao excluir template");
            setTemplates(templates.filter((t) => t.id !== templateId));
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao excluir template");
        }
    };

    if (isLoading && templates.length === 0) {
        return (
            <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (templates.length === 0) {
        return (
            <Card className="glass">
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                    <FileText className="h-12 w-12 mb-4 opacity-30" />
                    <p className="text-[var(--muted-foreground)] mb-2">
                        Nenhum template salvo ainda.
                    </p>
                    <p className="text-sm text-[var(--muted-foreground)]">
                        Use o Builder para criar e salvar templates customizados.
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="font-medium text-[var(--foreground)]">
                    Meus Templates ({templates.length})
                </h3>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                        setTemplates([]);
                        fetchTemplates(1);
                    }}
                    disabled={isLoading}
                >
                    <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
                </Button>
            </div>

            {/* Error */}
            {error && (
                <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/10 dark:text-red-400">
                    {error}
                </div>
            )}

            {/* Grid */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {templates.map((template) => (
                    <TemplateCard
                        key={template.id}
                        template={template}
                        onLoad={() => handleLoadTemplate(template.id)}
                        onDelete={() => handleDeleteTemplate(template.id, template.name)}
                        isLoading={loadingTemplateId === template.id}
                    />
                ))}
            </div>

            {/* Load More */}
            {hasMore && (
                <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => fetchTemplates(page + 1)}
                    disabled={isLoading}
                >
                    {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        "Carregar mais"
                    )}
                </Button>
            )}
        </div>
    );
}
