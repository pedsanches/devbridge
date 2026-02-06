"use client";

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import {
    User,
    Organization,
    getCurrentUser,
    getMyOrganizations,
    switchOrganization as apiSwitchOrganization,
    createOrganization as apiCreateOrganization,
    logout as apiLogout,
} from "@/services/api";

interface AuthContextType {
    user: User | null;
    organizations: Organization[];
    currentOrganization: Organization | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    isAdmin: boolean;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
    switchOrganization: (orgId: string) => Promise<void>;
    createOrganization: (name: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const refreshUser = useCallback(async () => {
        try {
            const [userData, orgsData] = await Promise.all([
                getCurrentUser(),
                getMyOrganizations(),
            ]);
            setUser(userData);
            setOrganizations(orgsData.organizations);
        } catch {
            setUser(null);
            setOrganizations([]);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        refreshUser();
    }, [refreshUser]);

    const logout = async () => {
        try {
            await apiLogout();
        } finally {
            setUser(null);
            setOrganizations([]);
        }
    };

    const switchOrganization = async (orgId: string) => {
        try {
            const updatedUser = await apiSwitchOrganization(orgId);
            setUser(updatedUser);
            // Reload the page to refresh all data with the new org context
            window.location.reload();
        } catch (error) {
            console.error("Failed to switch organization:", error);
            throw error;
        }
    };

    const createOrganization = async (name: string) => {
        try {
            // API creates org and switches context automatically (sets cookie)
            await apiCreateOrganization(name);
            // Reload the page to refresh all data with the new org context
            window.location.reload();
        } catch (error) {
            console.error("Failed to create organization:", error);
            throw error;
        }
    };

    // Derive current organization from user's organization_id
    const currentOrganization = organizations.find((org) => org.id === user?.organization_id) || null;

    return (
        <AuthContext.Provider
            value={{
                user,
                organizations,
                currentOrganization,
                isLoading,
                isAuthenticated: !!user,
                isAdmin: user?.role === "admin" || user?.role === "owner",
                logout,
                refreshUser,
                switchOrganization,
                createOrganization,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
