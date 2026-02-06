"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, Check, Building2, Plus } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { CreateOrganizationModal } from "./CreateOrganizationModal";

export function OrganizationSwitcher() {
    const { organizations, currentOrganization, switchOrganization, isLoading } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const [isSwitching, setIsSwitching] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Close on escape
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") setIsOpen(false);
        };
        document.addEventListener("keydown", handleEscape);
        return () => document.removeEventListener("keydown", handleEscape);
    }, []);

    const handleSwitch = async (orgId: string) => {
        if (orgId === currentOrganization?.id) {
            setIsOpen(false);
            return;
        }

        setIsSwitching(true);
        try {
            await switchOrganization(orgId);
            // Note: Page will reload after switchOrganization
        } catch (error) {
            console.error("Failed to switch organization:", error);
            setIsSwitching(false);
        }
    };

    const handleOpenCreateModal = () => {
        setIsOpen(false);
        setIsModalOpen(true);
    };

    // Always show switcher (even with 1 org to allow creating more)
    if (isLoading) {
        return null;
    }

    // If no current organization yet
    if (!currentOrganization) {
        return null;
    }

    // Single org: Show org name with option to create more
    const showDropdown = organizations.length >= 1;

    return (
        <>
            <div ref={dropdownRef} className="relative">
                {/* Trigger Button */}
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    disabled={isSwitching}
                    className={`
                        glass hover-lift active:scale-[0.98]
                        flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm
                        transition-all duration-300
                        ${isOpen ? "bg-white/10 ring-2 ring-primary/20" : ""}
                        ${isSwitching ? "opacity-50 cursor-wait" : "cursor-pointer"}
                    `}
                    aria-expanded={isOpen}
                    aria-haspopup="listbox"
                >
                    <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary/20 text-primary">
                        <Building2 className="h-3.5 w-3.5" />
                    </div>
                    <span className="truncate flex-1 text-left font-semibold text-foreground tracking-tight max-w-[140px]">
                        {currentOrganization.name}
                    </span>
                    <ChevronDown
                        className={`h-4 w-4 text-muted-foreground/70 transition-transform duration-300 ${isOpen ? "rotate-180" : ""
                            }`}
                    />
                </button>

                {/* Dropdown Menu */}
                {isOpen && showDropdown && (
                    <div
                        className="
                            glass-panel absolute left-0 top-full z-50 mt-2 w-full min-w-[240px]
                            rounded-xl p-1.5 shadow-2xl backdrop-blur-3xl
                            animate-scale-in origin-top
                        "
                        role="listbox"
                    >
                        <div className="max-h-[240px] overflow-y-auto sidebar-scroll px-1">
                            {organizations.map((org) => {
                                const isSelected = org.id === currentOrganization?.id;
                                return (
                                    <button
                                        key={org.id}
                                        onClick={() => handleSwitch(org.id)}
                                        disabled={isSwitching}
                                        role="option"
                                        aria-selected={isSelected}
                                        className={`
                                            flex w-full items-center gap-3 rounded-lg px-2.5 py-2.5 text-sm
                                            transition-all duration-200 group
                                            ${isSelected
                                                ? "bg-primary/15 text-primary"
                                                : "text-foreground hover:bg-white/5 dark:hover:bg-white/10"
                                            }
                                            ${isSwitching ? "cursor-wait" : "cursor-pointer"}
                                        `}
                                    >
                                        {/* Org Initial/Avatar */}
                                        <div
                                            className={`
                                                flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold transition-all
                                                ${isSelected
                                                    ? "bg-primary text-white shadow-lg shadow-primary/25 scale-105"
                                                    : "bg-muted text-muted-foreground group-hover:bg-muted/80"
                                                }
                                            `}
                                        >
                                            {org.name.charAt(0).toUpperCase()}
                                        </div>
                                        <div className="flex-1 text-left min-w-0">
                                            <p className="truncate font-medium leading-none mb-1">{org.name}</p>
                                            <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">
                                                {org.role}
                                            </p>
                                        </div>
                                        {isSelected && (
                                            <Check className="h-4 w-4 text-primary flex-shrink-0 animate-fade-in" />
                                        )}
                                    </button>
                                );
                            })}
                        </div>

                        {/* Separator */}
                        <div className="my-1.5 h-px bg-gradient-to-r from-transparent via-border to-transparent" />

                        {/* Create Organization Button */}
                        <button
                            onClick={handleOpenCreateModal}
                            className="
                                flex w-full items-center gap-3 rounded-lg px-2.5 py-2.5 text-sm
                                text-muted-foreground transition-all duration-200
                                hover:bg-white/5 hover:text-foreground group
                            "
                        >
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-dashed border-muted-foreground/40 group-hover:border-primary/50 group-hover:bg-primary/5 transition-colors">
                                <Plus className="h-4 w-4" />
                            </div>
                            <span className="font-medium">Create Organization</span>
                        </button>
                    </div>
                )}
            </div>

            {/* Create Organization Modal */}
            <CreateOrganizationModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
            />
        </>
    );
}
