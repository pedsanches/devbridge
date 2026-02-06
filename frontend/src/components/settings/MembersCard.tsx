"use client";

import { useState } from "react";
import { Users, Mail, Clock, Check, X, RotateCw, UserPlus, Loader2 } from "lucide-react";
import { Invitation, createInvitation, getInvitations, revokeInvitation, resendInvitation } from "@/services/api";
import useSWR, { mutate } from "swr";
import { useAuth } from "@/hooks/use-auth";

interface InviteModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (email: string, role: string) => Promise<void>;
    isLoading: boolean;
}

function InviteModal({ isOpen, onClose, onSubmit, isLoading }: InviteModalProps) {
    const [email, setEmail] = useState("");
    const [role, setRole] = useState("member");

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await onSubmit(email, role);
        setEmail("");
        setRole("member");
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-neutral-800">
                <h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-white">
                    Convidar Membro
                </h2>
                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
                            Email
                        </label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            placeholder="usuario@empresa.com"
                            className="w-full rounded-lg border border-neutral-200 bg-white px-3 py-2 text-neutral-900 placeholder:text-neutral-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-neutral-700 dark:bg-neutral-900 dark:text-white"
                        />
                    </div>
                    <div className="mb-6">
                        <label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
                            Papel
                        </label>
                        <select
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                            className="w-full rounded-lg border border-neutral-200 bg-white px-3 py-2 text-neutral-900 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-neutral-700 dark:bg-neutral-900 dark:text-white"
                        >
                            <option value="member">Membro</option>
                            <option value="admin">Admin</option>
                        </select>
                    </div>
                    <div className="flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="rounded-lg border border-neutral-200 px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-700"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading || !email}
                            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-hover disabled:opacity-50"
                        >
                            {isLoading ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <Mail className="h-4 w-4" />
                            )}
                            Enviar Convite
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

const statusConfig = {
    pending: { icon: Clock, color: "text-amber-500 bg-amber-50 dark:bg-amber-950", label: "Pendente" },
    accepted: { icon: Check, color: "text-green-500 bg-green-50 dark:bg-green-950", label: "Aceito" },
    expired: { icon: X, color: "text-neutral-400 bg-neutral-50 dark:bg-neutral-800", label: "Expirado" },
    revoked: { icon: X, color: "text-red-500 bg-red-50 dark:bg-red-950", label: "Revogado" },
};

export function MembersCard() {
    const { isAdmin } = useAuth();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    const { data, isLoading, error } = useSWR("/invitations", getInvitations);

    const handleInvite = async (email: string, role: string) => {
        setIsSubmitting(true);
        try {
            await createInvitation({ email, role });
            mutate("/invitations");
            setIsModalOpen(false);
        } catch (err) {
            console.error("Failed to create invitation:", err);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleRevoke = async (id: string) => {
        setActionLoading(id);
        try {
            await revokeInvitation(id);
            mutate("/invitations");
        } catch (err) {
            console.error("Failed to revoke invitation:", err);
        } finally {
            setActionLoading(null);
        }
    };

    const handleResend = async (id: string) => {
        setActionLoading(id);
        try {
            await resendInvitation(id);
            mutate("/invitations");
        } catch (err) {
            console.error("Failed to resend invitation:", err);
        } finally {
            setActionLoading(null);
        }
    };

    return (
        <div className="rounded-xl border border-neutral-200 bg-white shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
            <div className="flex items-center justify-between border-b border-neutral-100 p-6 dark:border-neutral-800">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                        <Users className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-neutral-900 dark:text-white">Membros & Convites</h3>
                        <p className="text-sm text-neutral-500">Gerencie quem tem acesso</p>
                    </div>
                </div>
                {isAdmin && (
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-hover"
                    >
                        <UserPlus className="h-4 w-4" />
                        Convidar
                    </button>
                )}
            </div>

            <div className="p-6">
                {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
                    </div>
                ) : error ? (
                    <p className="text-center text-sm text-red-500">Erro ao carregar convites</p>
                ) : data?.items.length === 0 ? (
                    <p className="text-center text-sm text-neutral-500">Nenhum convite pendente</p>
                ) : (
                    <div className="space-y-3">
                        {data?.items.map((invite: Invitation) => {
                            const status = statusConfig[invite.status];
                            const StatusIcon = status.icon;
                            const isPending = invite.status === "pending";

                            return (
                                <div
                                    key={invite.id}
                                    className="flex items-center justify-between rounded-lg border border-neutral-100 p-4 dark:border-neutral-800"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`flex h-8 w-8 items-center justify-center rounded-full ${status.color}`}>
                                            <StatusIcon className="h-4 w-4" />
                                        </div>
                                        <div>
                                            <p className="font-medium text-neutral-900 dark:text-white">
                                                {invite.email}
                                            </p>
                                            <p className="text-xs text-neutral-500">
                                                {invite.role === "admin" ? "Admin" : "Membro"} • {status.label}
                                            </p>
                                        </div>
                                    </div>

                                    {isPending && isAdmin && (
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handleResend(invite.id)}
                                                disabled={actionLoading === invite.id}
                                                className="rounded-lg p-2 text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                                                title="Reenviar"
                                            >
                                                {actionLoading === invite.id ? (
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                ) : (
                                                    <RotateCw className="h-4 w-4" />
                                                )}
                                            </button>
                                            <button
                                                onClick={() => handleRevoke(invite.id)}
                                                disabled={actionLoading === invite.id}
                                                className="rounded-lg p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-950"
                                                title="Revogar"
                                            >
                                                <X className="h-4 w-4" />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            <InviteModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleInvite}
                isLoading={isSubmitting}
            />
        </div>
    );
}
