"use client";

import { useState, useRef, useEffect } from "react";
import { Building2, Loader2 } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog";
import { useAuth } from "@/hooks/use-auth";

interface CreateOrganizationModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function CreateOrganizationModal({ isOpen, onClose }: CreateOrganizationModalProps) {
    const { createOrganization } = useAuth();
    const [name, setName] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Focus input when modal opens
    useEffect(() => {
        if (isOpen) {
            // Small delay to ensure the modal is fully rendered
            const timer = setTimeout(() => {
                inputRef.current?.focus();
            }, 100);
            return () => clearTimeout(timer);
        }
    }, [isOpen]);

    // Reset state when modal closes
    useEffect(() => {
        if (!isOpen) {
            setName("");
            setError(null);
            setIsLoading(false);
        }
    }, [isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!name.trim()) {
            setError("Organization name is required");
            return;
        }

        if (name.trim().length < 2) {
            setError("Name must be at least 2 characters");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            await createOrganization(name.trim());
            // Note: Page will reload after createOrganization
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create organization");
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                            <Building2 className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <DialogTitle>Create Organization</DialogTitle>
                            <DialogDescription>
                                Create a new workspace for your team or project.
                            </DialogDescription>
                        </div>
                    </div>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <label
                            htmlFor="org-name"
                            className="text-sm font-medium text-foreground"
                        >
                            Organization Name
                        </label>
                        <input
                            ref={inputRef}
                            id="org-name"
                            type="text"
                            value={name}
                            onChange={(e) => {
                                setName(e.target.value);
                                setError(null);
                            }}
                            placeholder="e.g. Acme Inc, My Startup, Personal"
                            disabled={isLoading}
                            className={`
                                w-full rounded-lg border px-3 py-2.5 text-sm
                                bg-background text-foreground placeholder:text-muted-foreground
                                transition-colors duration-150
                                focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20
                                disabled:cursor-not-allowed disabled:opacity-50
                                ${error ? "border-red-500" : "border-border"}
                            `}
                        />
                        {error && (
                            <p className="text-sm text-red-500">{error}</p>
                        )}
                    </div>

                    <DialogFooter className="gap-2 sm:gap-0">
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={isLoading}
                            className="
                                rounded-lg px-4 py-2 text-sm font-medium
                                text-muted-foreground transition-colors
                                hover:bg-muted hover:text-foreground
                                disabled:cursor-not-allowed disabled:opacity-50
                            "
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading || !name.trim()}
                            className="
                                flex items-center justify-center gap-2 rounded-lg
                                bg-primary px-4 py-2 text-sm font-medium text-white
                                transition-colors hover:bg-primary/90
                                disabled:cursor-not-allowed disabled:opacity-50
                            "
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Creating...
                                </>
                            ) : (
                                "Create Organization"
                            )}
                        </button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
