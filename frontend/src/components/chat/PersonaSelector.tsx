"use client";

import { Briefcase, Code, Layers } from "lucide-react";
import { Persona } from "@/services/api";

interface PersonaSelectorProps {
    selected: Persona;
    onChange: (persona: Persona) => void;
    disabled?: boolean;
}

const personas: { value: Persona; label: string; icon: React.ElementType; description: string }[] = [
    {
        value: "executive",
        label: "Executivo",
        icon: Briefcase,
        description: "ROI e estratégia",
    },
    {
        value: "product",
        label: "Produto",
        icon: Layers,
        description: "Features e roadmap",
    },
    {
        value: "technical",
        label: "Técnico",
        icon: Code,
        description: "Código e arquitetura",
    },
];

export function PersonaSelector({ selected, onChange, disabled }: PersonaSelectorProps) {
    return (
        <div className="flex gap-1 rounded-lg bg-neutral-100 p-1 dark:bg-neutral-800">
            {personas.map(({ value, label, icon: Icon }) => (
                <button
                    key={value}
                    onClick={() => onChange(value)}
                    disabled={disabled}
                    className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${selected === value
                            ? "bg-white text-primary shadow-sm dark:bg-neutral-700"
                            : "text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300"
                        } disabled:opacity-50`}
                    title={personas.find((p) => p.value === value)?.description}
                >
                    <Icon className="h-3.5 w-3.5" />
                    {label}
                </button>
            ))}
        </div>
    );
}
