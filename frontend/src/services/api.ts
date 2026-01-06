/**
 * API Client for DevBridge Backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
        ...options,
        credentials: "include", // Send cookies
        headers: { "Content-Type": "application/json", ...options.headers },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
        return {} as T;
    }

    return response.json();
}

// Auth API
export interface User {
    id: string;
    email: string;
    name: string | null;
    organization_id: string;
}

export async function requestMagicLink(email: string): Promise<{ message: string; email: string }> {
    return fetchAPI("/auth/magic", {
        method: "POST",
        body: JSON.stringify({ email }),
    });
}

export async function verifyMagicLink(token: string): Promise<User> {
    return fetchAPI("/auth/verify", {
        method: "POST",
        body: JSON.stringify({ token }),
    });
}

export async function getCurrentUser(): Promise<User> {
    return fetchAPI("/auth/me");
}

export async function logout(): Promise<{ message: string }> {
    return fetchAPI("/auth/logout", { method: "POST" });
}

// Chat API
export type Persona = "executive" | "technical" | "product";

export interface ChatRequest {
    message: string;
    repository?: string | string[];
    author?: string;
    persona?: Persona;
    conversationId?: string;
}

export interface ChatMetadata {
    activities_count: number;
    search_method: "semantic" | "sql";
    confidence_score: number;
    persona_used: Persona;
}

export interface ChatResponse {
    answer: string;
    activities_count: number;
    filters: { repository?: string; author?: string; days?: number };
    metadata?: ChatMetadata;
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    return fetchAPI<ChatResponse>("/chat", {
        method: "POST",
        body: JSON.stringify(request),
    });
}

/**
 * Send a chat message with streaming response (SSE).
 * @param request - Chat request with message and optional persona
 * @param onChunk - Callback for each text chunk received
 * @param onDone - Callback when streaming is complete
 * @param onError - Callback on error
 */
export async function sendChatMessageStream(
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onDone: () => void,
    onError: (error: Error) => void
): Promise<void> {
    const url = `${API_BASE_URL}/chat/stream`;

    try {
        const response = await fetch(url, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "Unknown error" }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error("No response body");
        }

        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            const lines = text.split("\n");

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const data = line.slice(6);
                    if (data === "[DONE]") {
                        onDone();
                        return;
                    }
                    onChunk(data);
                }
            }
        }

        onDone();
    } catch (error) {
        onError(error instanceof Error ? error : new Error("Streaming error"));
    }
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

// Settings/Integrations API
export type IntegrationStatus = "connected" | "disconnected" | "error";

export interface GitHubIntegration {
    status: IntegrationStatus;
    connected_at: string | null;
    organization_name: string | null;
    repositories_count: number;
}

export interface SlackIntegration {
    status: IntegrationStatus;
    connected_at: string | null;
    channel_name: string | null;
}

export interface IntegrationsResponse {
    github: GitHubIntegration;
    slack: SlackIntegration;
}

export interface DataSource {
    id: string;
    name: string;
    url: string;
    is_active: boolean;
    activities_count: number;
    last_synced_at: string | null;
    indexing_status: "pending" | "indexing" | "indexed" | "error";
    vectors_count: number;
}

export interface DataSourcesResponse {
    sources: DataSource[];
    total: number;
    github_connected: boolean;
}

export async function getIntegrations(): Promise<IntegrationsResponse> {
    return fetchAPI<IntegrationsResponse>("/settings/integrations");
}

export async function syncRepository(repoName: string): Promise<{ status: string; commits_synced: number; prs_synced: number }> {
    return fetchAPI("/sync", {
        method: "POST",
        body: JSON.stringify({ repo_name: repoName, max_commits: 20, max_prs: 10 }),
    });
}

export async function connectGitHub(token: string): Promise<{ status: IntegrationStatus; organization_name: string | null; message: string }> {
    return fetchAPI("/settings/github/connect", {
        method: "POST",
        body: JSON.stringify({ token }),
    });
}

export async function disconnectGitHub(): Promise<void> {
    await fetchAPI("/settings/github/disconnect", { method: "POST" });
}

export async function getDataSources(): Promise<DataSourcesResponse> {
    return fetchAPI<DataSourcesResponse>("/settings/data-sources");
}

// Conversation API
export interface ConversationSummary {
    id: string;
    title: string;
    updated_at: string;
    message_count: number;
}

export interface ConversationsListResponse {
    conversations: ConversationSummary[];
    total: number;
    has_more: boolean;
}

export async function getConversations(
    limit: number = 20,
    offset: number = 0
): Promise<ConversationsListResponse> {
    return fetchAPI<ConversationsListResponse>(`/conversations?limit=${limit}&offset=${offset}`);
}

export async function createConversation(title?: string): Promise<ConversationSummary> {
    return fetchAPI<ConversationSummary>("/conversations", {
        method: "POST",
        body: JSON.stringify({ title }),
    });
}

export async function deleteConversation(id: string): Promise<void> {
    return fetchAPI(`/conversations/${id}`, { method: "DELETE" });
}

export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    created_at: string;
    message_metadata?: Record<string, unknown>;
}

export interface ConversationDetail extends ConversationSummary {
    messages: ChatMessage[];
}

export async function getConversation(id: string): Promise<ConversationDetail> {
    return fetchAPI<ConversationDetail>(`/conversations/${id}`);
}
