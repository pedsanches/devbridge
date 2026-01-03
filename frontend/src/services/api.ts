/**
 * API Client for DevBridge Backend.
 */

const API_BASE_URL = "http://localhost:8000/api/v1";

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
        ...options,
        headers: { "Content-Type": "application/json", ...options.headers },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
}

// Chat API
export interface ChatRequest {
    message: string;
    repository?: string;
    author?: string;
}

export interface ChatResponse {
    answer: string;
    activities_count: number;
    filters: { repository?: string; author?: string; days?: number };
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    return fetchAPI<ChatResponse>("/chat", {
        method: "POST",
        body: JSON.stringify(request),
    });
}

// Health API
export interface HealthResponse {
    status: string;
    version: string;
    environment: string;
}

export async function getHealth(): Promise<HealthResponse> {
    return fetchAPI<HealthResponse>("/health");
}
