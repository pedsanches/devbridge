"use client";

/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from "react";
import {
    ChevronLeft,
    ChevronRight,
    Database,
    Layout,
    Languages,
    Palette,
    Eye,
    Check,
} from "lucide-react";
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    DragEndEvent,
} from '@dnd-kit/core';
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    verticalListSortingStrategy,
    useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// ============================================================
// Types
// ============================================================

export interface DataFilters {
    repositories?: string[] | undefined;
    authors?: string[] | undefined;
    activityTypes?: ("COMMIT" | "PULL_REQUEST")[] | undefined;
    impactLevels?: ("LOW" | "MEDIUM" | "HIGH")[] | undefined;
    valueTags?: string[] | undefined;
    labels?: string[] | undefined;
}

export interface SectionConfig {
    type: string;
    title: string;
    enabled: boolean;
    order: number;
    detailLevel: "minimal" | "normal" | "detailed";
    customPrompt?: string | undefined;
}

export interface LanguageConfig {
    language: "pt-BR" | "en-US" | "es";
    formality: number;
    jargonLevel: number;
    verbosity: number;
    tone: "neutral" | "optimistic" | "cautious";
    format: "bullets" | "paragraphs" | "mixed";
}

export interface VisualConfig {
    primaryColor: string;
    secondaryColor: string;
    fontFamily: "Inter" | "Roboto" | "Arial";
    logoUrl?: string | undefined;
    showCharts: boolean;
    watermark?: "CONFIDENTIAL" | "DRAFT" | null | undefined;
    headerStyle: "minimal" | "full";
}

export interface ReportBuilderConfig {
    name: string;
    description: string;
    periodStart: Date;
    periodEnd: Date;
    dataFilters: DataFilters;
    sections: SectionConfig[];
    languageConfig: LanguageConfig;
    visualConfig: VisualConfig;
}

// ============================================================
// Default Values
// ============================================================

const DEFAULT_SECTIONS: SectionConfig[] = [
    { type: "summary", title: "Resumo Executivo", order: 0, enabled: true, detailLevel: "normal" },
    { type: "metrics", title: "Métricas e KPIs", order: 1, enabled: true, detailLevel: "normal" },
    { type: "highlights", title: "Destaques", order: 2, enabled: true, detailLevel: "normal" },
    { type: "risks", title: "Riscos e Atenções", order: 3, enabled: true, detailLevel: "normal" },
    { type: "technical", title: "Detalhes Técnicos", order: 4, enabled: false, detailLevel: "normal" },
    { type: "timeline", title: "Linha do Tempo", order: 5, enabled: false, detailLevel: "normal" },
    { type: "contributors", title: "Contribuidores", order: 6, enabled: false, detailLevel: "normal" },
];

const DEFAULT_LANGUAGE_CONFIG: LanguageConfig = {
    language: "pt-BR",
    formality: 3,
    jargonLevel: 2,
    verbosity: 3,
    tone: "neutral",
    format: "bullets",
};

const DEFAULT_VISUAL_CONFIG: VisualConfig = {
    primaryColor: "#3B82F6",
    secondaryColor: "#1E40AF",
    fontFamily: "Inter",
    showCharts: true,
    watermark: null,
    headerStyle: "full",
};

// ============================================================
// Step Indicator Component
// ============================================================

interface StepIndicatorProps {
    steps: { id: string; label: string; icon: React.ElementType }[];
    currentStep: number;
    onStepClick?: (index: number) => void;
}

function StepIndicator({ steps, currentStep, onStepClick }: StepIndicatorProps) {
    return (
        <div className="flex items-center justify-center gap-2 mb-8">
            {steps.map((step, index) => {
                const Icon = step.icon;
                const isActive = index === currentStep;
                const isCompleted = index < currentStep;

                return (
                    <div key={step.id} className="flex items-center">
                        <button
                            onClick={() => onStepClick?.(index)}
                            disabled={index > currentStep}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${isActive
                                ? "bg-primary text-white shadow-lg"
                                : isCompleted
                                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                                    : "bg-[var(--muted)] text-[var(--muted-foreground)]"
                                } ${index <= currentStep ? "cursor-pointer hover:opacity-80" : "cursor-not-allowed opacity-50"}`}
                        >
                            {isCompleted ? (
                                <Check className="h-4 w-4" />
                            ) : (
                                <Icon className="h-4 w-4" />
                            )}
                            <span className="hidden md:inline text-sm font-medium">{step.label}</span>
                        </button>
                        {index < steps.length - 1 && (
                            <div className={`w-8 h-0.5 mx-2 ${isCompleted ? "bg-green-400" : "bg-[var(--border)]"
                                }`} />
                        )}
                    </div>
                );
            })}
        </div>
    );
}

// ============================================================
// Step Components
// ============================================================

interface StepProps {
    config: ReportBuilderConfig;
    onChange: (updates: Partial<ReportBuilderConfig>) => void;
}

// Step 1: Data Selection
function DataStep({ config, onChange }: StepProps) {
    return (
        <div className="space-y-6">
            {/* Period Selection */}
            <div className="grid gap-4 md:grid-cols-2">
                <div>
                    <label className="block text-sm font-medium mb-2">Data Início</label>
                    <input
                        type="date"
                        value={config.periodStart.toISOString().split('T')[0]}
                        onChange={(e) => onChange({ periodStart: new Date(e.target.value) })}
                        className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium mb-2">Data Fim</label>
                    <input
                        type="date"
                        value={config.periodEnd.toISOString().split('T')[0]}
                        onChange={(e) => onChange({ periodEnd: new Date(e.target.value) })}
                        className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]"
                    />
                </div>
            </div>

            {/* Activity Types */}
            <div>
                <label className="block text-sm font-medium mb-2">Tipos de Atividade</label>
                <div className="flex gap-3">
                    {[
                        { id: "COMMIT", label: "Commits" },
                        { id: "PULL_REQUEST", label: "Pull Requests" },
                    ].map((type) => {
                        const isSelected = config.dataFilters.activityTypes?.includes(type.id as any) ?? true;
                        return (
                            <button
                                key={type.id}
                                onClick={() => {
                                    const current = config.dataFilters.activityTypes || ["COMMIT", "PULL_REQUEST"];
                                    const updated = isSelected
                                        ? current.filter(t => t !== type.id)
                                        : [...current, type.id];
                                    onChange({
                                        dataFilters: {
                                            ...config.dataFilters,
                                            activityTypes: updated as any,
                                        },
                                    });
                                }}
                                className={`px-4 py-2 rounded-lg border transition-all ${isSelected
                                    ? "border-primary bg-primary/10 text-primary"
                                    : "border-[var(--border)] text-[var(--muted-foreground)]"
                                    }`}
                            >
                                {type.label}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Impact Levels */}
            <div>
                <label className="block text-sm font-medium mb-2">Níveis de Impacto</label>
                <div className="flex gap-3">
                    {[
                        { id: "LOW", label: "🟢 Baixo", color: "green" },
                        { id: "MEDIUM", label: "🟡 Médio", color: "yellow" },
                        { id: "HIGH", label: "🔴 Alto", color: "red" },
                    ].map((level) => {
                        const isSelected = config.dataFilters.impactLevels?.includes(level.id as any) ?? true;
                        return (
                            <button
                                key={level.id}
                                onClick={() => {
                                    const current = config.dataFilters.impactLevels || ["LOW", "MEDIUM", "HIGH"];
                                    const updated = isSelected
                                        ? current.filter(l => l !== level.id)
                                        : [...current, level.id];
                                    onChange({
                                        dataFilters: {
                                            ...config.dataFilters,
                                            impactLevels: updated as any,
                                        },
                                    });
                                }}
                                className={`px-4 py-2 rounded-lg border transition-all ${isSelected
                                    ? "border-primary bg-primary/10 text-primary"
                                    : "border-[var(--border)] text-[var(--muted-foreground)]"
                                    }`}
                            >
                                {level.label}
                            </button>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

// Step 2: Sections Configuration (with drag-and-drop)
interface SortableSectionProps {
    section: SectionConfig;
    index: number;
    onToggle: () => void;
    onDetailChange: (level: "minimal" | "normal" | "detailed") => void;
}

function SortableSectionItem({ section, onToggle, onDetailChange }: SortableSectionProps) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
    } = useSortable({ id: section.type });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${section.enabled
                ? "border-primary/50 bg-primary/5"
                : "border-[var(--border)] bg-[var(--muted)]/30 opacity-60"
                }`}
        >
            {/* Drag Handle */}
            <div
                {...attributes}
                {...listeners}
                className="cursor-grab text-[var(--muted-foreground)] p-2 hover:text-[var(--foreground)] touch-none"
            >
                ⋮⋮
            </div>

            {/* Enable Toggle */}
            <button
                onClick={onToggle}
                className={`w-6 h-6 rounded-md border-2 flex items-center justify-center transition-all ${section.enabled
                    ? "border-primary bg-primary text-white"
                    : "border-[var(--border)]"
                    }`}
            >
                {section.enabled && <Check className="h-4 w-4" />}
            </button>

            {/* Section Info */}
            <div className="flex-1">
                <div className="font-medium">{section.title}</div>
                <div className="text-xs text-[var(--muted-foreground)]">
                    Tipo: {section.type}
                </div>
            </div>

            {/* Detail Level */}
            {section.enabled && (
                <div className="flex gap-1" onPointerDown={e => e.stopPropagation()}>
                    {(["minimal", "normal", "detailed"] as const).map((level) => (
                        <button
                            key={level}
                            onClick={() => onDetailChange(level)}
                            className={`px-2 py-1 text-xs rounded transition-all ${section.detailLevel === level
                                ? "bg-primary text-white"
                                : "bg-[var(--muted)] text-[var(--muted-foreground)]"
                                }`}
                        >
                            {level === "minimal" ? "Mínimo" : level === "normal" ? "Normal" : "Detalhado"}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

function SectionsStep({ config, onChange }: StepProps) {
    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (active.id !== over?.id) {
            const oldIndex = config.sections.findIndex((s) => s.type === active.id);
            const newIndex = config.sections.findIndex((s) => s.type === over?.id);
            onChange({ sections: arrayMove(config.sections, oldIndex, newIndex) });
        }
    };

    const toggleSection = (index: number) => {
        const updated = [...config.sections];
        const section = updated[index];
        if (section) {
            updated[index] = { ...section, enabled: !section.enabled };
            onChange({ sections: updated });
        }
    };

    const setDetailLevel = (index: number, level: "minimal" | "normal" | "detailed") => {
        const updated = [...config.sections];
        const section = updated[index];
        if (section) {
            updated[index] = { ...section, detailLevel: level };
            onChange({ sections: updated });
        }
    };

    return (
        <div className="space-y-4">
            <p className="text-sm text-[var(--muted-foreground)] mb-4">
                Arraste para reordenar as seções e configure o nível de detalhe.
            </p>

            <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
            >
                <SortableContext
                    items={config.sections.map(s => s.type)}
                    strategy={verticalListSortingStrategy}
                >
                    <div className="space-y-4">
                        {config.sections.map((section, index) => (
                            <SortableSectionItem
                                key={section.type}
                                section={section}
                                index={index}
                                onToggle={() => toggleSection(index)}
                                onDetailChange={(level) => setDetailLevel(index, level)}
                            />
                        ))}
                    </div>
                </SortableContext>
            </DndContext>
        </div>
    );
}

// Step 3: Language Configuration
function LanguageStep({ config, onChange }: StepProps) {
    const updateLanguage = (updates: Partial<LanguageConfig>) => {
        onChange({ languageConfig: { ...config.languageConfig, ...updates } });
    };

    return (
        <div className="space-y-6">
            {/* Language Selection */}
            <div>
                <label className="block text-sm font-medium mb-2">Idioma</label>
                <div className="flex gap-3">
                    {[
                        { id: "pt-BR", label: "🇧🇷 Português" },
                        { id: "en-US", label: "🇺🇸 English" },
                        { id: "es", label: "🇪🇸 Español" },
                    ].map((lang) => (
                        <button
                            key={lang.id}
                            onClick={() => updateLanguage({ language: lang.id as any })}
                            className={`px-4 py-2 rounded-lg border transition-all ${config.languageConfig.language === lang.id
                                ? "border-primary bg-primary/10 text-primary"
                                : "border-[var(--border)]"
                                }`}
                        >
                            {lang.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Sliders */}
            {[
                { key: "formality", label: "Formalidade", leftLabel: "Casual", rightLabel: "Formal" },
                { key: "jargonLevel", label: "Jargão Técnico", leftLabel: "Nenhum", rightLabel: "Completo" },
                { key: "verbosity", label: "Extensão", leftLabel: "Conciso", rightLabel: "Detalhado" },
            ].map((slider) => (
                <div key={slider.key}>
                    <label className="block text-sm font-medium mb-2">{slider.label}</label>
                    <div className="flex items-center gap-4">
                        <span className="text-xs text-[var(--muted-foreground)] w-16">{slider.leftLabel}</span>
                        <input
                            type="range"
                            min="1"
                            max="5"
                            value={(config.languageConfig as any)[slider.key]}
                            onChange={(e) => updateLanguage({ [slider.key]: parseInt(e.target.value) } as any)}
                            className="flex-1 accent-primary"
                        />
                        <span className="text-xs text-[var(--muted-foreground)] w-16 text-right">{slider.rightLabel}</span>
                    </div>
                </div>
            ))}

            {/* Tone */}
            <div>
                <label className="block text-sm font-medium mb-2">Tom</label>
                <div className="flex gap-3">
                    {[
                        { id: "neutral", label: "Neutro" },
                        { id: "optimistic", label: "Otimista" },
                        { id: "cautious", label: "Cauteloso" },
                    ].map((tone) => (
                        <button
                            key={tone.id}
                            onClick={() => updateLanguage({ tone: tone.id as any })}
                            className={`px-4 py-2 rounded-lg border transition-all ${config.languageConfig.tone === tone.id
                                ? "border-primary bg-primary/10 text-primary"
                                : "border-[var(--border)]"
                                }`}
                        >
                            {tone.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Format */}
            <div>
                <label className="block text-sm font-medium mb-2">Formato</label>
                <div className="flex gap-3">
                    {[
                        { id: "bullets", label: "• Bullets" },
                        { id: "paragraphs", label: "¶ Parágrafos" },
                        { id: "mixed", label: "Misto" },
                    ].map((format) => (
                        <button
                            key={format.id}
                            onClick={() => updateLanguage({ format: format.id as any })}
                            className={`px-4 py-2 rounded-lg border transition-all ${config.languageConfig.format === format.id
                                ? "border-primary bg-primary/10 text-primary"
                                : "border-[var(--border)]"
                                }`}
                        >
                            {format.label}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

// Step 4: Visual Configuration
function VisualStep({ config, onChange }: StepProps) {
    const updateVisual = (updates: Partial<VisualConfig>) => {
        onChange({ visualConfig: { ...config.visualConfig, ...updates } });
    };

    return (
        <div className="space-y-6">
            {/* Colors */}
            <div className="grid gap-4 md:grid-cols-2">
                <div>
                    <label className="block text-sm font-medium mb-2">Cor Primária</label>
                    <div className="flex items-center gap-3">
                        <input
                            type="color"
                            value={config.visualConfig.primaryColor}
                            onChange={(e) => updateVisual({ primaryColor: e.target.value })}
                            className="w-12 h-10 rounded cursor-pointer"
                        />
                        <input
                            type="text"
                            value={config.visualConfig.primaryColor}
                            onChange={(e) => updateVisual({ primaryColor: e.target.value })}
                            className="flex-1 px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--background)]"
                        />
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium mb-2">Cor Secundária</label>
                    <div className="flex items-center gap-3">
                        <input
                            type="color"
                            value={config.visualConfig.secondaryColor}
                            onChange={(e) => updateVisual({ secondaryColor: e.target.value })}
                            className="w-12 h-10 rounded cursor-pointer"
                        />
                        <input
                            type="text"
                            value={config.visualConfig.secondaryColor}
                            onChange={(e) => updateVisual({ secondaryColor: e.target.value })}
                            className="flex-1 px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--background)]"
                        />
                    </div>
                </div>
            </div>

            {/* Font Family */}
            <div>
                <label className="block text-sm font-medium mb-2">Fonte</label>
                <div className="flex gap-3">
                    {(["Inter", "Roboto", "Arial"] as const).map((font) => (
                        <button
                            key={font}
                            onClick={() => updateVisual({ fontFamily: font })}
                            className={`px-4 py-2 rounded-lg border transition-all ${config.visualConfig.fontFamily === font
                                ? "border-primary bg-primary/10 text-primary"
                                : "border-[var(--border)]"
                                }`}
                            style={{ fontFamily: font }}
                        >
                            {font}
                        </button>
                    ))}
                </div>
            </div>

            {/* Options */}
            <div className="flex gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                    <input
                        type="checkbox"
                        checked={config.visualConfig.showCharts}
                        onChange={(e) => updateVisual({ showCharts: e.target.checked })}
                        className="w-5 h-5 rounded accent-primary"
                    />
                    <span className="text-sm">Incluir gráficos de métricas</span>
                </label>
            </div>

            {/* Watermark */}
            <div>
                <label className="block text-sm font-medium mb-2">Marca d&apos;água</label>
                <div className="flex gap-3">
                    {[
                        { id: null, label: "Nenhuma" },
                        { id: "DRAFT", label: "DRAFT" },
                        { id: "CONFIDENTIAL", label: "CONFIDENTIAL" },
                    ].map((wm) => (
                        <button
                            key={wm.id || "none"}
                            onClick={() => updateVisual({ watermark: wm.id as any })}
                            className={`px-4 py-2 rounded-lg border transition-all ${config.visualConfig.watermark === wm.id
                                ? "border-primary bg-primary/10 text-primary"
                                : "border-[var(--border)]"
                                }`}
                        >
                            {wm.label}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

// Step 5: Preview
function PreviewStep({ config }: StepProps) {
    const enabledSections = config.sections.filter(s => s.enabled);

    return (
        <div className="space-y-6">
            {/* Preview Card */}
            <div
                className="rounded-xl border border-[var(--border)] p-6"
                style={{
                    borderTopColor: config.visualConfig.primaryColor,
                    borderTopWidth: "4px",
                }}
            >
                <h2
                    className="text-xl font-bold mb-2"
                    style={{ color: config.visualConfig.secondaryColor, fontFamily: config.visualConfig.fontFamily }}
                >
                    Relatório de Desenvolvimento
                </h2>
                <p className="text-sm text-[var(--muted-foreground)] mb-4">
                    Período: {config.periodStart.toLocaleDateString("pt-BR")} - {config.periodEnd.toLocaleDateString("pt-BR")}
                </p>

                {/* Sections Preview */}
                <div className="space-y-4">
                    {enabledSections.slice(0, 3).map((section) => (
                        <div key={section.type} className="border-l-2 border-[var(--border)] pl-4">
                            <h3
                                className="font-medium"
                                style={{ color: config.visualConfig.primaryColor }}
                            >
                                {section.title}
                            </h3>
                            <p className="text-sm text-[var(--muted-foreground)]">
                                {section.detailLevel === "minimal" && "Conteúdo resumido..."}
                                {section.detailLevel === "normal" && "Conteúdo com nível normal de detalhe..."}
                                {section.detailLevel === "detailed" && "Conteúdo completo e detalhado com análise profunda..."}
                            </p>
                        </div>
                    ))}
                    {enabledSections.length > 3 && (
                        <p className="text-sm text-[var(--muted-foreground)]">
                            +{enabledSections.length - 3} seções adicionais
                        </p>
                    )}
                </div>
            </div>

            {/* Configuration Summary */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-base">Resumo da Configuração</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between">
                        <span className="text-[var(--muted-foreground)]">Idioma</span>
                        <span>{config.languageConfig.language}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-[var(--muted-foreground)]">Tom</span>
                        <span>{config.languageConfig.tone}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-[var(--muted-foreground)]">Seções</span>
                        <span>{enabledSections.length} habilitadas</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-[var(--muted-foreground)]">Gráficos</span>
                        <span>{config.visualConfig.showCharts ? "Sim" : "Não"}</span>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

// ============================================================
// Main Report Builder Component
// ============================================================

interface ReportBuilderProps {
    onGenerate: (config: ReportBuilderConfig) => Promise<void>;
    onSaveTemplate?: (config: ReportBuilderConfig) => Promise<void>;
    isGenerating?: boolean;
    initialTemplate?: {
        name: string;
        description: string | null;
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
    } | null;
}

export function ReportBuilder({ onGenerate, onSaveTemplate, isGenerating, initialTemplate }: ReportBuilderProps) {
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    const [currentStep, setCurrentStep] = useState(0);
    const [loadedTemplateName, setLoadedTemplateName] = useState<string | null>(null);
    const [config, setConfig] = useState<ReportBuilderConfig>({
        name: "",
        description: "",
        periodStart: weekAgo,
        periodEnd: now,
        dataFilters: {
            activityTypes: ["COMMIT", "PULL_REQUEST"],
            impactLevels: ["LOW", "MEDIUM", "HIGH"],
        },
        sections: DEFAULT_SECTIONS,
        languageConfig: DEFAULT_LANGUAGE_CONFIG,
        visualConfig: DEFAULT_VISUAL_CONFIG,
    });

    // Effect to load template when initialTemplate changes
    useEffect(() => {
        if (initialTemplate) {
            setConfig({
                name: initialTemplate.name,
                description: initialTemplate.description || "",
                periodStart: weekAgo,
                periodEnd: now,
                dataFilters: {
                    repositories: initialTemplate.data_filters?.repositories,
                    authors: initialTemplate.data_filters?.authors,
                    activityTypes: (initialTemplate.data_filters?.activity_types as ("COMMIT" | "PULL_REQUEST")[]) || ["COMMIT", "PULL_REQUEST"],
                    impactLevels: (initialTemplate.data_filters?.impact_levels as ("LOW" | "MEDIUM" | "HIGH")[]) || ["LOW", "MEDIUM", "HIGH"],
                    valueTags: initialTemplate.data_filters?.value_tags,
                    labels: initialTemplate.data_filters?.labels,
                },
                sections: initialTemplate.sections_config.map(s => ({
                    type: s.type,
                    title: s.title,
                    enabled: s.enabled,
                    order: s.order,
                    detailLevel: s.detail_level,
                    customPrompt: s.custom_prompt,
                })),
                languageConfig: initialTemplate.language_config ? {
                    language: initialTemplate.language_config.language,
                    formality: initialTemplate.language_config.formality,
                    jargonLevel: initialTemplate.language_config.jargon_level,
                    verbosity: initialTemplate.language_config.verbosity,
                    tone: initialTemplate.language_config.tone,
                    format: initialTemplate.language_config.format,
                } : DEFAULT_LANGUAGE_CONFIG,
                visualConfig: initialTemplate.visual_config ? {
                    primaryColor: initialTemplate.visual_config.primary_color,
                    secondaryColor: initialTemplate.visual_config.secondary_color,
                    fontFamily: initialTemplate.visual_config.font_family,
                    showCharts: initialTemplate.visual_config.show_charts,
                    watermark: initialTemplate.visual_config.watermark,
                    headerStyle: initialTemplate.visual_config.header_style,
                } : DEFAULT_VISUAL_CONFIG,
            });
            setLoadedTemplateName(initialTemplate.name);
            setCurrentStep(0);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [initialTemplate]);

    const steps = [
        { id: "data", label: "Dados", icon: Database },
        { id: "sections", label: "Seções", icon: Layout },
        { id: "language", label: "Linguagem", icon: Languages },
        { id: "visual", label: "Visual", icon: Palette },
        { id: "preview", label: "Preview", icon: Eye },
    ];

    const handleChange = (updates: Partial<ReportBuilderConfig>) => {
        setConfig(prev => ({ ...prev, ...updates }));
    };

    const handleNext = () => {
        if (currentStep < steps.length - 1) {
            setCurrentStep(currentStep + 1);
        }
    };

    const handleBack = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1);
        }
    };

    const handleGenerate = async () => {
        await onGenerate(config);
    };

    const renderStep = () => {
        const stepProps = { config, onChange: handleChange };
        switch (currentStep) {
            case 0: return <DataStep {...stepProps} />;
            case 1: return <SectionsStep {...stepProps} />;
            case 2: return <LanguageStep {...stepProps} />;
            case 3: return <VisualStep {...stepProps} />;
            case 4: return <PreviewStep {...stepProps} />;
            default: return null;
        }
    };

    // Save Template Modal State
    const [showSaveModal, setShowSaveModal] = useState(false);
    const [templateName, setTemplateName] = useState("");
    const [templateDescription, setTemplateDescription] = useState("");

    const handleOpenSaveModal = () => {
        setTemplateName(config.name || "");
        setTemplateDescription(config.description || "");
        setShowSaveModal(true);
    };

    const handleConfirmSave = async () => {
        if (!onSaveTemplate) return;

        const finalConfig = {
            ...config,
            name: templateName,
            description: templateDescription,
        };

        await onSaveTemplate(finalConfig);
        setShowSaveModal(false);
    };

    const isLastStep = currentStep === steps.length - 1;

    return (
        <div className="space-y-6 relative">
            {/* Loaded Template Banner */}
            {loadedTemplateName && (
                <div className="rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3 flex items-center justify-between">
                    <span className="text-sm text-blue-700 dark:text-blue-300">
                        📁 Template carregado: <strong>{loadedTemplateName}</strong>
                    </span>
                    <button
                        onClick={() => setLoadedTemplateName(null)}
                        className="text-blue-500 hover:text-blue-700 text-sm"
                    >
                        ✕
                    </button>
                </div>
            )}

            {/* Step Indicator */}
            <StepIndicator
                steps={steps}
                currentStep={currentStep}
                onStepClick={setCurrentStep}
            />

            {/* Step Content */}
            <Card className="min-h-[400px]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        {(() => { const step = steps[currentStep]; if (!step) return null; const Icon = step.icon; return <Icon className="h-5 w-5" />; })()}
                        {steps[currentStep]?.label ?? "Configuração"}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {renderStep()}
                </CardContent>
            </Card>

            {/* Navigation */}
            <div className="flex justify-between">
                <Button
                    variant="outline"
                    onClick={handleBack}
                    disabled={currentStep === 0}
                >
                    <ChevronLeft className="h-4 w-4 mr-2" />
                    Voltar
                </Button>

                <div className="flex gap-3">
                    {onSaveTemplate && isLastStep && (
                        <Button variant="outline" onClick={handleOpenSaveModal}>
                            Salvar como Template
                        </Button>
                    )}

                    {!isLastStep ? (
                        <Button onClick={handleNext}>
                            Próximo
                            <ChevronRight className="h-4 w-4 ml-2" />
                        </Button>
                    ) : (
                        <Button onClick={handleGenerate} disabled={isGenerating}>
                            {isGenerating ? "Gerando..." : "Gerar Relatório"}
                        </Button>
                    )}
                </div>
            </div>

            {/* Save Template Modal */}
            {showSaveModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="w-full max-w-md bg-[var(--background)] rounded-xl border border-[var(--border)] shadow-2xl p-6 space-y-6">
                        <div className="space-y-2">
                            <h3 className="text-lg font-semibold">Salvar Template</h3>
                            <p className="text-sm text-[var(--muted-foreground)]">
                                Dê um nome e descrição para reutilizar essa configuração depois.
                            </p>
                        </div>

                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Nome do Template</label>
                                <input
                                    type="text"
                                    value={templateName}
                                    onChange={(e) => setTemplateName(e.target.value)}
                                    placeholder="Ex: Resumo Semanal do Produto"
                                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--background)] focus:outline-none focus:ring-2 focus:ring-primary/50"
                                    autoFocus
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Descrição (Opcional)</label>
                                <textarea
                                    value={templateDescription}
                                    onChange={(e) => setTemplateDescription(e.target.value)}
                                    placeholder="Ex: Foco em métricas de entrega e riscos..."
                                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--background)] focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[80px]"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 justify-end pt-2">
                            <Button variant="outline" onClick={() => setShowSaveModal(false)}>
                                Cancelar
                            </Button>
                            <Button onClick={handleConfirmSave} disabled={!templateName.trim()}>
                                Salvar
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ReportBuilder;
