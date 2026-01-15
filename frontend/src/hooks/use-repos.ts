import { useState, useEffect } from 'react';
import { useAuth } from './use-auth';
import { frontendEnv } from "@/config/env";

interface Repository {
    id: string;
    name: string;
    owner: string;
    platform: string;
    last_synced_at: string | null;
}

const API_BASE_URL = frontendEnv.apiBaseUrl;

export function useRepos() {
    const { isAuthenticated } = useAuth();
    const [repos, setRepos] = useState<Repository[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!isAuthenticated) {
            setIsLoading(false);
            return;
        }

        const fetchRepos = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/repos`, {
                    credentials: "include",
                });
                if (!response.ok) throw new Error("Failed to fetch repositories");
                const data = await response.json();
                // API returns PaginatedResponse with { data: [...], total, page, page_size, total_pages }
                setRepos(data.data || []);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Error loading repos");
            } finally {
                setIsLoading(false);
            }
        };

        fetchRepos();
    }, [isAuthenticated]);

    return { repos, isLoading, error };
}
