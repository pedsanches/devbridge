"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
    FileText,
    Download,
    Loader2,
    ChevronDown,
    Calendar,
    Building2,
    History,
    Plus,
    Trash2,
    RefreshCw,
    CheckCircle,
    Save,
    Sparkles,
    FolderOpen,
    Users,
} from "lucide-react";

import ReportBuilder, { ReportBuilderConfig } from "@/components/reports/ReportBuilder";
import TemplatesManager, { FullTemplate } from "@/components/reports/TemplatesManager";
import { TeamSelector } from "@/components/teams";

import { useAuth } from "@/hooks/use-auth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Team } from "@/services/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ============================================================
// Types
// ============================================================

interface ReportType {
    id: string;
    name: string;
    audience: string;
    description: string;
    icon: string;
}

const REPORT_TYPES: ReportType[] = [
    {
        id: "weekly_summary",
        name: "Resumo Semanal",
        audience: "Product Manager",
        description: "Foco em entregas, progresso nas metas, e próximos passos.",
        icon: "📊",
    },
    {
        id: "technical_report",
        name: "Relatório Técnico",
        audience: "CTO / Tech Lead",
        description: "Decisões técnicas, qualidade de código, dívida técnica.",
        icon: "⚙️",
    },
    {
        id: "executive_summary",
        name: "Resumo Executivo",
        audience: "CEO / C-Level",
        description: "Máximo 5 bullets, linguagem de negócio, foco em ROI.",
        icon: "📈",
    },
];

interface ReportSection {
    title: string;
    content: string;
    metrics?: { name: string; value: string | number; change?: string; trend?: string }[];
}

interface ReportMetric {
    name: string;
    value: string | number;
    change?: string;
    trend?: string;
}

interface ReportResponse {
    title: string;
    subtitle: string;
    generated_at: string;
    period_description: string;
    report_type: string;
    sections: ReportSection[];
    summary_metrics?: ReportMetric[];
    confidence_score: number;
    sources_count: number;
}

interface SavedReport {
    id: string;
    report_type: string;
    title: string;
    team_id: string | null;
    team_name: string | null;
    period_description: string;
    generated_at: string;
    sources_count: number;
    confidence_score: number;
}

interface ReportListResponse {
    items: SavedReport[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

// ============================================================
// Helper Functions
// ============================================================

function getReportTypeInfo(typeId: string): ReportType | undefined {
    return REPORT_TYPES.find((t) => t.id === typeId);
}

function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

// ============================================================
// Components
// ============================================================

function TabButton({
    active,
    onClick,
    icon: Icon,
    label,
}: {
    active: boolean;
    onClick: () => void;
    icon: React.ElementType;
    label: string;
}) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${active
                ? "bg-primary text-white shadow-md"
                : "text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
        >
            <Icon className="h-4 w-4" />
            {label}
        </button>
    );
}

function ReportHistoryCard({
    report,
    isSelected,
    onSelect,
    onDelete,
}: {
    report: SavedReport;
    isSelected: boolean;
    onSelect: () => void;
    onDelete: () => void;
}) {
    const typeInfo = getReportTypeInfo(report.report_type);

    return (
        <div
            onClick={onSelect}
            className={`group cursor-pointer rounded-xl border p-4 transition-all hover-lift ${isSelected
                ? "border-primary bg-primary/5 ring-1 ring-primary"
                : "border-[var(--border)] hover:border-primary/50 glass"
                }`}
        >
            <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                    <span className="text-2xl flex-shrink-0">{typeInfo?.icon || "📄"}</span>
                    <div className="min-w-0 flex-1">
                        <div className="font-medium text-[var(--foreground)] truncate">
                            {report.title}
                        </div>
                        <div className="text-xs text-[var(--muted-foreground)] mt-0.5">
                            {typeInfo?.audience || "Relatório"}
                        </div>
                        <div className="text-xs text-[var(--muted-foreground)] mt-1">
                            {report.period_description}
                        </div>
                    </div>
                </div>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onDelete();
                    }}
                    className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100 dark:hover:bg-red-900/20 text-red-500"
                >
                    <Trash2 className="h-4 w-4" />
                </button>
            </div>
            <div className="flex items-center gap-3 mt-3 text-xs text-[var(--muted-foreground)]">
                <span>{formatDate(report.generated_at)}</span>
                <span>•</span>
                <span>{report.sources_count} fontes</span>
                {report.team_name && (
                    <>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                            <Users className="h-3 w-3" />
                            {report.team_name}
                        </span>
                    </>
                )}
                <Badge variant={report.confidence_score >= 0.7 ? "default" : "secondary"} className="ml-auto">
                    {Math.round(report.confidence_score * 100)}%
                </Badge>
            </div>
        </div>
    );
}

function ReportPreview({
    report,
    onExport,
    onExportPDF,
    isExportingPDF = false,
}: {
    report: ReportResponse | null;
    onExport?: (() => void) | undefined;
    onExportPDF?: (() => void) | undefined;
    isExportingPDF?: boolean | undefined;
}) {
    if (!report) {
        return (
            <div className="flex h-[400px] flex-col items-center justify-center text-center text-[var(--muted-foreground)]">
                <Building2 className="mb-4 h-12 w-12 opacity-30" />
                <p>Selecione um relatório para visualizar.</p>
            </div>
        );
    }

    return (
        <div className="prose prose-sm dark:prose-invert max-w-none">
            <div className="flex items-start justify-between mb-4">
                <div>
                    <h2 className="text-xl font-semibold mb-1">{report.title}</h2>
                    <p className="text-[var(--muted-foreground)] text-sm">{report.subtitle}</p>
                </div>
                <div className="flex gap-2">
                    {onExport && (
                        <button
                            onClick={onExport}
                            className="flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm transition-colors hover:bg-[var(--muted)]"
                        >
                            <Download className="h-4 w-4" />
                            Markdown
                        </button>
                    )}
                    {onExportPDF && (
                        <button
                            onClick={onExportPDF}
                            disabled={isExportingPDF}
                            className="flex items-center gap-2 rounded-lg bg-primary text-white px-3 py-1.5 text-sm transition-colors hover:bg-primary/90 disabled:opacity-50"
                        >
                            {isExportingPDF ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <FileText className="h-4 w-4" />
                            )}
                            PDF
                        </button>
                    )}
                </div>
            </div>

            {/* Summary Metrics */}
            {report.summary_metrics && report.summary_metrics.length > 0 && (
                <div className="my-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
                    {report.summary_metrics.map((m, i) => (
                        <div
                            key={i}
                            className="rounded-lg border border-[var(--border)] p-3 text-center glass"
                        >
                            <div className="text-2xl font-bold text-[var(--foreground)]">
                                {m.value}
                            </div>
                            <div className="text-xs text-[var(--muted-foreground)]">
                                {m.name}
                            </div>
                            {m.change && (
                                <div
                                    className={`mt-1 text-xs ${m.trend === "up"
                                        ? "text-green-600"
                                        : m.trend === "down"
                                            ? "text-red-600"
                                            : "text-gray-500"
                                        }`}
                                >
                                    {m.change}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Sections */}
            {report.sections.map((section, i) => (
                <div key={i} className="mb-6">
                    <h3 className="mb-2 text-lg font-medium text-[var(--foreground)]">
                        {section.title}
                    </h3>
                    <div className="whitespace-pre-wrap text-[var(--foreground)]">
                        {section.content}
                    </div>
                </div>
            ))}

            {/* Footer */}
            <div className="mt-8 border-t border-[var(--border)] pt-4 text-xs text-[var(--muted-foreground)]">
                <p>
                    Gerado em {new Date(report.generated_at).toLocaleString("pt-BR")} |{" "}
                    {report.sources_count} atividades analisadas |{" "}
                    Confiança: {Math.round(report.confidence_score * 100)}%
                </p>
            </div>
        </div>
    );
}

// ============================================================
// Main Page Component
// ============================================================


function mapConfigToApi(config: ReportBuilderConfig) {
    return {
        name: config.name || `Template ${new Date().toLocaleDateString()}`,
        description: config.description || "Template customizado",
        is_default: false,
        data_filters: config.dataFilters ? {
            repositories: config.dataFilters.repositories,
            authors: config.dataFilters.authors,
            activity_types: config.dataFilters.activityTypes,
            impact_levels: config.dataFilters.impactLevels,
            value_tags: config.dataFilters.valueTags,
            labels: config.dataFilters.labels,
        } : null,
        sections_config: config.sections.map(s => ({
            type: s.type,
            title: s.title,
            enabled: s.enabled,
            order: s.order,
            detail_level: s.detailLevel,
            custom_prompt: s.customPrompt,
        })),
        language_config: config.languageConfig ? {
            language: config.languageConfig.language,
            formality: config.languageConfig.formality,
            jargon_level: config.languageConfig.jargonLevel,
            verbosity: config.languageConfig.verbosity,
            tone: config.languageConfig.tone,
            format: config.languageConfig.format,
        } : null,
        visual_config: config.visualConfig ? {
            primary_color: config.visualConfig.primaryColor,
            secondary_color: config.visualConfig.secondaryColor,
            font_family: config.visualConfig.fontFamily,
            show_charts: config.visualConfig.showCharts,
            watermark: config.visualConfig.watermark,
            header_style: config.visualConfig.headerStyle,
        } : null
    };
}

export default function ReportsPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuth();
    const router = useRouter();

    // Tab state
    const [activeTab, setActiveTab] = useState<"generate" | "history" | "templates" | "custom">("generate");

    // Loaded template state (for Builder)
    const [loadedTemplate, setLoadedTemplate] = useState<FullTemplate | null>(null);

    // Generate tab state
    const [selectedType, setSelectedType] = useState<string>("weekly_summary");
    const [periodDays, setPeriodDays] = useState<number>(7);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedReport, setGeneratedReport] = useState<ReportResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);

    // History tab state
    const [historyReports, setHistoryReports] = useState<SavedReport[]>([]);
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);
    const [selectedHistoryReport, setSelectedHistoryReport] = useState<SavedReport | null>(null);
    const [selectedReportDetails, setSelectedReportDetails] = useState<ReportResponse | null>(null);
    const [historyPage, setHistoryPage] = useState(1);
    const [hasMoreHistory, setHasMoreHistory] = useState(false);
    const [isExportingPDF, setIsExportingPDF] = useState(false);

    // Redirect if not authenticated
    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push("/login");
        }
    }, [authLoading, isAuthenticated, router]);

    // Fetch history when tab changes
    const fetchHistory = useCallback(async (page = 1) => {
        setIsLoadingHistory(true);
        try {
            const response = await fetch(
                `${API_BASE_URL}/reports/history?page=${page}&page_size=10`,
                { credentials: "include" }
            );
            if (!response.ok) throw new Error("Failed to fetch history");
            const data: ReportListResponse = await response.json();
            setHistoryReports(page === 1 ? data.items : [...historyReports, ...data.items]);
            setHasMoreHistory(data.has_more);
            setHistoryPage(page);
        } catch (err) {
            console.error("Error fetching history:", err);
        } finally {
            setIsLoadingHistory(false);
        }
    }, [historyReports]);

    useEffect(() => {
        if (activeTab === "history" && historyReports.length === 0) {
            fetchHistory();
        }
    }, [activeTab, historyReports.length, fetchHistory]);

    // Fetch selected report details
    useEffect(() => {
        if (selectedHistoryReport) {
            (async () => {
                try {
                    const response = await fetch(
                        `${API_BASE_URL}/reports/${selectedHistoryReport.id}`,
                        { credentials: "include" }
                    );
                    if (!response.ok) throw new Error("Failed to fetch report");
                    const data = await response.json();
                    // Transform to ReportResponse format
                    setSelectedReportDetails({
                        title: data.title,
                        subtitle: data.subtitle,
                        generated_at: data.generated_at,
                        period_description: data.period_description,
                        report_type: data.report_type,
                        sections: data.sections,
                        summary_metrics: data.summary_metrics,
                        confidence_score: data.confidence_score,
                        sources_count: data.sources_count,
                    });
                } catch (err) {
                    console.error("Error fetching report details:", err);
                }
            })();
        }
    }, [selectedHistoryReport]);

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const handleTeamChange = (teamId: string | null, _team: Team | null) => {
        setSelectedTeamId(teamId);
    };

    const handleGenerateReport = async () => {
        // Require team selection
        if (!selectedTeamId) {
            setError("Selecione um time para gerar o relatório");
            return;
        }

        setIsGenerating(true);
        setError(null);
        setSaveSuccess(false);

        const now = new Date();
        const start = new Date(now);
        start.setDate(start.getDate() - periodDays);

        try {
            const response = await fetch(`${API_BASE_URL}/reports`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({
                    report_type: selectedType,
                    period: {
                        start: start.toISOString(),
                        end: now.toISOString(),
                    },
                    repositories: null,
                }),
            });

            if (!response.ok) {
                throw new Error("Falha ao gerar relatório");
            }

            const data: ReportResponse = await response.json();
            setGeneratedReport(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro desconhecido");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSaveReport = async () => {
        if (!generatedReport) return;

        setIsSaving(true);
        try {
            const now = new Date();
            const start = new Date(now);
            start.setDate(start.getDate() - periodDays);

            const response = await fetch(`${API_BASE_URL}/reports/save`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({
                    title: generatedReport.title,
                    subtitle: generatedReport.subtitle,
                    report_type: generatedReport.report_type,
                    team_id: selectedTeamId,
                    period_start: start.toISOString(),
                    period_end: now.toISOString(),
                    period_description: generatedReport.period_description,
                    sections: generatedReport.sections,
                    summary_metrics: generatedReport.summary_metrics,
                    sources_count: generatedReport.sources_count,
                    confidence_score: generatedReport.confidence_score,
                    generated_at: generatedReport.generated_at,
                }),
            });

            if (!response.ok) {
                throw new Error("Falha ao salvar relatório");
            }

            setSaveSuccess(true);
            // Refresh history
            setHistoryReports([]);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao salvar");
        } finally {
            setIsSaving(false);
        }
    };

    const handleDeleteReport = async (reportId: string) => {
        if (!confirm("Deseja realmente excluir este relatório?")) return;

        try {
            const response = await fetch(`${API_BASE_URL}/reports/${reportId}`, {
                method: "DELETE",
                credentials: "include",
            });

            if (!response.ok) {
                throw new Error("Falha ao excluir relatório");
            }

            setHistoryReports(historyReports.filter((r) => r.id !== reportId));
            if (selectedHistoryReport?.id === reportId) {
                setSelectedHistoryReport(null);
                setSelectedReportDetails(null);
            }
        } catch (err) {
            console.error("Error deleting report:", err);
        }
    };

    const handleExportPDF = async (reportId: string, title: string) => {
        setIsExportingPDF(true);
        try {
            const response = await fetch(
                `${API_BASE_URL}/reports/export/pdf?report_id=${reportId}`,
                { method: "POST", credentials: "include" }
            );

            if (!response.ok) {
                throw new Error("Falha ao exportar PDF");
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${title.replace(/\s+/g, "_")}.pdf`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Error exporting PDF:", err);
            setError(err instanceof Error ? err.message : "Erro ao exportar PDF");
        } finally {
            setIsExportingPDF(false);
        }
    };

    const handleExportMarkdown = (report: ReportResponse) => {
        let markdown = `# ${report.title}\n\n`;
        markdown += `**${report.subtitle}**\n\n`;
        markdown += `_Gerado em: ${new Date(report.generated_at).toLocaleString("pt-BR")}_\n\n`;
        markdown += `---\n\n`;

        if (report.summary_metrics && report.summary_metrics.length > 0) {
            markdown += `## Métricas\n\n`;
            for (const m of report.summary_metrics) {
                markdown += `- **${m.name}**: ${m.value}${m.change ? ` (${m.change})` : ""}\n`;
            }
            markdown += `\n`;
        }

        for (const section of report.sections) {
            markdown += `## ${section.title}\n\n`;
            markdown += `${section.content}\n\n`;
        }

        markdown += `---\n\n`;
        markdown += `_Fontes: ${report.sources_count} atividades | Confiança: ${Math.round(report.confidence_score * 100)}%_\n`;

        const blob = new Blob([markdown], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${report.title.replace(/\s+/g, "_")}.md`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const [templateSuccess, setTemplateSuccess] = useState<string | null>(null);

    const handleSaveTemplate = async (config: ReportBuilderConfig) => {
        setIsSaving(true);
        setError(null);
        setTemplateSuccess(null);
        try {
            const response = await fetch(`${API_BASE_URL}/report-templates`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify(mapConfigToApi(config)),
            });

            if (!response.ok) throw new Error("Falha ao salvar template");

            setTemplateSuccess("Template salvo com sucesso!");
            setTimeout(() => setTemplateSuccess(null), 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao salvar template");
        } finally {
            setIsSaving(false);
        }
    };

    const handleGenerateCustom = async (config: ReportBuilderConfig) => {
        setIsGenerating(true);
        setError(null);
        try {
            // 1. Prepare Payload
            const apiConfig = mapConfigToApi(config);
            // Ensure dates are ISO strings for backend Pydantic
            const payload = {
                period_start: config.periodStart,
                period_end: config.periodEnd,
                data_filters: apiConfig.data_filters,
                sections_config: apiConfig.sections_config,
                language_config: apiConfig.language_config,
                visual_config: apiConfig.visual_config
            };

            // 2. Generate Report (LLM)
            const genResponse = await fetch(`${API_BASE_URL}/reports/custom`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify(payload),
            });

            if (!genResponse.ok) {
                const err = await genResponse.json();
                throw new Error(err.detail || "Falha na geração da análise");
            }

            const reportData = await genResponse.json();
            const reportId = reportData.id;

            // 3. Export PDF
            const pdfResponse = await fetch(`${API_BASE_URL}/reports/export/pdf?report_id=${reportId}`, {
                method: "POST",
                credentials: "include",
            });

            if (!pdfResponse.ok) throw new Error("Falha ao gerar arquivo PDF");

            const blob = await pdfResponse.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${config.name || "Relatorio_Customizado"}.pdf`;
            a.click();
            URL.revokeObjectURL(url);

            // Switch to history to show it saved
            setActiveTab("history");

        } catch (err) {
            console.error(err);
            setError(err instanceof Error ? err.message : "Erro ao gerar relatório");
        } finally {
            setIsGenerating(false);
        }
    };

    if (authLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return (
        <div className="flex min-h-screen flex-col bg-[var(--background)]">
            <main className="flex-1 py-8">
                <div className="container mx-auto max-w-6xl px-4">
                    {/* Header */}
                    <div className="mb-6">
                        <h1 className="flex items-center gap-3 text-2xl font-semibold tracking-tight text-[var(--foreground)]">
                            <FileText className="h-6 w-6" />
                            Relatórios
                        </h1>
                        <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                            Gere relatórios estruturados ou acesse o histórico de relatórios salvos
                        </p>
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-2 mb-6 p-1 bg-[var(--muted)] rounded-xl w-fit">
                        <TabButton
                            active={activeTab === "generate"}
                            onClick={() => setActiveTab("generate")}
                            icon={Plus}
                            label="Gerar Novo"
                        />
                        <TabButton
                            active={activeTab === "history"}
                            onClick={() => setActiveTab("history")}
                            icon={History}
                            label="Histórico"
                        />
                        <TabButton
                            active={activeTab === "templates"}
                            onClick={() => setActiveTab("templates")}
                            icon={FolderOpen}
                            label="Templates"
                        />
                        <TabButton
                            active={activeTab === "custom"}
                            onClick={() => setActiveTab("custom")}
                            icon={Sparkles}
                            label="Builder (Beta)"
                        />
                    </div>

                    {/* Generate Tab Content */}
                    {activeTab === "generate" && (
                        <div className="space-y-6">
                            {/* Configuration Bar */}
                            <Card className="glass-panel">
                                <CardContent className="p-4">
                                    <div className="flex flex-wrap items-end gap-4">
                                        {/* Report Type */}
                                        <div className="flex-1 min-w-[200px]">
                                            <label className="text-sm font-medium text-[var(--foreground)] mb-2 block">
                                                Tipo de Relatório
                                            </label>
                                            <div className="flex gap-2">
                                                {REPORT_TYPES.map((type) => (
                                                    <button
                                                        key={type.id}
                                                        onClick={() => setSelectedType(type.id)}
                                                        className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-all ${selectedType === type.id
                                                            ? "border-primary bg-primary/10 text-primary"
                                                            : "border-[var(--border)] hover:border-primary/50"
                                                            }`}
                                                    >
                                                        <span>{type.icon}</span>
                                                        <span className="hidden sm:inline">{type.name}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Team Selector - REQUIRED */}
                                        <div className="min-w-[200px]">
                                            <label className="text-sm font-medium text-[var(--foreground)] mb-2 block">
                                                Time <span className="text-red-500">*</span>
                                            </label>
                                            <TeamSelector
                                                selectedTeamId={selectedTeamId}
                                                onTeamChange={handleTeamChange}
                                                disabled={isGenerating}
                                                allowAll={false}
                                            />
                                        </div>

                                        {/* Period Selector */}
                                        <div className="w-[180px]">
                                            <label className="text-sm font-medium text-[var(--foreground)] mb-2 block">
                                                Período
                                            </label>
                                            <div className="relative">
                                                <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
                                                <select
                                                    value={periodDays}
                                                    onChange={(e) => setPeriodDays(Number(e.target.value))}
                                                    className="w-full appearance-none rounded-lg border border-[var(--border)] bg-[var(--background)] py-2 pl-10 pr-10 text-sm text-[var(--foreground)] transition-colors hover:border-primary/50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                                                >
                                                    <option value={7}>Últimos 7 dias</option>
                                                    <option value={14}>Últimas 2 semanas</option>
                                                    <option value={30}>Último mês</option>
                                                    <option value={90}>Último trimestre</option>
                                                </select>
                                                <ChevronDown className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
                                            </div>
                                        </div>

                                        {/* Generate Button */}
                                        <Button
                                            onClick={handleGenerateReport}
                                            disabled={isGenerating}
                                            className="min-w-[140px]"
                                        >
                                            {isGenerating ? (
                                                <span className="flex items-center gap-2">
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                    Gerando...
                                                </span>
                                            ) : (
                                                <span className="flex items-center gap-2">
                                                    <RefreshCw className="h-4 w-4" />
                                                    Gerar Relatório
                                                </span>
                                            )}
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Error */}
                            {error && (
                                <div className="rounded-lg bg-red-50 p-4 text-red-600 dark:bg-red-900/10 dark:text-red-400">
                                    {error}
                                </div>
                            )}

                            {/* Report Preview */}
                            <Card className="min-h-[500px]">
                                <CardHeader className="flex flex-row items-center justify-between">
                                    <div>
                                        <CardTitle className="text-lg">Preview</CardTitle>
                                        <CardDescription>
                                            {generatedReport
                                                ? generatedReport.period_description
                                                : "Selecione as opções e gere o relatório"}
                                        </CardDescription>
                                    </div>
                                    {generatedReport && (
                                        <div className="flex gap-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleExportMarkdown(generatedReport)}
                                            >
                                                <Download className="h-4 w-4 mr-2" />
                                                Exportar MD
                                            </Button>
                                            <Button
                                                size="sm"
                                                onClick={handleSaveReport}
                                                disabled={isSaving || saveSuccess}
                                            >
                                                {isSaving ? (
                                                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                                ) : saveSuccess ? (
                                                    <CheckCircle className="h-4 w-4 mr-2" />
                                                ) : (
                                                    <Save className="h-4 w-4 mr-2" />
                                                )}
                                                {saveSuccess ? "Salvo!" : "Salvar"}
                                            </Button>
                                        </div>
                                    )}
                                </CardHeader>
                                <CardContent>
                                    {isGenerating ? (
                                        <div className="flex h-[400px] flex-col items-center justify-center">
                                            <Loader2 className="mb-4 h-8 w-8 animate-spin text-primary" />
                                            <p className="text-[var(--muted-foreground)]">
                                                Analisando atividades...
                                            </p>
                                        </div>
                                    ) : generatedReport ? (
                                        <ReportPreview report={generatedReport} />
                                    ) : (
                                        <div className="flex h-[400px] flex-col items-center justify-center text-center text-[var(--muted-foreground)]">
                                            <Building2 className="mb-4 h-12 w-12 opacity-30" />
                                            <p>Nenhum relatório gerado ainda.</p>
                                            <p className="text-sm">
                                                Configure as opções acima e clique em &quot;Gerar Relatório&quot;.
                                            </p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {/* Custom Builder Tab Content */}
                    {activeTab === "custom" && (
                        <div className="max-w-4xl mx-auto space-y-4">
                            {templateSuccess && (
                                <div className="rounded-lg bg-green-50 p-4 text-green-600 dark:bg-green-900/10 dark:text-green-400 flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
                                    <CheckCircle className="h-5 w-5" />
                                    {templateSuccess}
                                </div>
                            )}

                            <ReportBuilder
                                onGenerate={handleGenerateCustom}
                                onSaveTemplate={handleSaveTemplate}
                                isGenerating={isGenerating}
                                initialTemplate={loadedTemplate}
                            />
                        </div>
                    )}

                    {/* Templates Tab Content */}
                    {activeTab === "templates" && (
                        <div className="max-w-4xl mx-auto">
                            <TemplatesManager
                                onLoadTemplate={(template) => {
                                    setLoadedTemplate(template);
                                    setActiveTab("custom");
                                }}
                            />
                        </div>
                    )}

                    {/* History Tab Content */}
                    {activeTab === "history" && (
                        <div className="grid gap-6 lg:grid-cols-3">
                            {/* History List */}
                            <div className="space-y-3 lg:col-span-1">
                                <div className="flex items-center justify-between">
                                    <h3 className="font-medium text-[var(--foreground)]">
                                        Relatórios Salvos
                                    </h3>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => {
                                            setHistoryReports([]);
                                            fetchHistory(1);
                                        }}
                                        disabled={isLoadingHistory}
                                    >
                                        <RefreshCw className={`h-4 w-4 ${isLoadingHistory ? "animate-spin" : ""}`} />
                                    </Button>
                                </div>

                                {isLoadingHistory && historyReports.length === 0 ? (
                                    <div className="flex justify-center py-8">
                                        <Loader2 className="h-6 w-6 animate-spin text-primary" />
                                    </div>
                                ) : historyReports.length === 0 ? (
                                    <Card className="glass">
                                        <CardContent className="flex flex-col items-center justify-center py-8 text-center">
                                            <History className="h-10 w-10 mb-3 opacity-30" />
                                            <p className="text-[var(--muted-foreground)]">
                                                Nenhum relatório salvo ainda.
                                            </p>
                                            <Button
                                                variant="link"
                                                onClick={() => setActiveTab("generate")}
                                                className="mt-2"
                                            >
                                                Gerar seu primeiro relatório
                                            </Button>
                                        </CardContent>
                                    </Card>
                                ) : (
                                    <>
                                        <div className="space-y-3">
                                            {historyReports.map((report) => (
                                                <ReportHistoryCard
                                                    key={report.id}
                                                    report={report}
                                                    isSelected={selectedHistoryReport?.id === report.id}
                                                    onSelect={() => setSelectedHistoryReport(report)}
                                                    onDelete={() => handleDeleteReport(report.id)}
                                                />
                                            ))}
                                        </div>
                                        {hasMoreHistory && (
                                            <Button
                                                variant="outline"
                                                className="w-full mt-3"
                                                onClick={() => fetchHistory(historyPage + 1)}
                                                disabled={isLoadingHistory}
                                            >
                                                {isLoadingHistory ? (
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                ) : (
                                                    "Carregar mais"
                                                )}
                                            </Button>
                                        )}
                                    </>
                                )}
                            </div>

                            {/* Report Detail */}
                            <div className="lg:col-span-2">
                                <Card className="min-h-[500px]">
                                    <CardHeader>
                                        <CardTitle className="text-lg">Detalhes do Relatório</CardTitle>
                                        <CardDescription>
                                            {selectedHistoryReport
                                                ? selectedHistoryReport.period_description
                                                : "Selecione um relatório para visualizar"}
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <ReportPreview
                                            report={selectedReportDetails}
                                            onExport={
                                                selectedReportDetails
                                                    ? () => handleExportMarkdown(selectedReportDetails)
                                                    : undefined
                                            }
                                            onExportPDF={
                                                selectedHistoryReport && selectedReportDetails
                                                    ? () => handleExportPDF(selectedHistoryReport.id, selectedReportDetails.title)
                                                    : undefined
                                            }
                                            isExportingPDF={isExportingPDF}
                                        />
                                    </CardContent>
                                </Card>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
