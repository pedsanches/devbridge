/**
 * API Client for DevBridge Backend.
 */

import { frontendEnv } from "@/config/env";

const API_BASE_URL = frontendEnv.apiBaseUrl;

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
    role: "owner" | "admin" | "member" | "viewer";
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

// Organization API
export interface Organization {
    id: string;
    name: string;
    slug: string;
    role: "owner" | "admin" | "member" | "viewer";
}

export interface OrganizationsListResponse {
    organizations: Organization[];
    current_organization_id: string;
}

export async function getMyOrganizations(): Promise<OrganizationsListResponse> {
    return fetchAPI<OrganizationsListResponse>("/auth/organizations");
}

export async function switchOrganization(organizationId: string): Promise<User> {
    return fetchAPI<User>("/auth/switch-org", {
        method: "POST",
        body: JSON.stringify({ organization_id: organizationId }),
    });
}

export interface OrganizationDetail {
    id: string;
    name: string;
    slug: string;
    plan: string;
}

export interface CreateOrganizationResponse {
    organization: OrganizationDetail;
    switched: boolean;
    message: string;
}

export async function createOrganization(name: string, slug?: string): Promise<CreateOrganizationResponse> {
    return fetchAPI<CreateOrganizationResponse>("/organizations", {
        method: "POST",
        body: JSON.stringify({ name, slug }),
    });
}

// Invitation API
export interface InviteAcceptResponse {
    id: string;
    email: string;
    name: string | null;
    organization_id: string;
    organization_name: string;
    teams: string[];
}

export interface Invitation {
    id: string;
    email: string;
    organization_id: string;
    role: string;
    status: "pending" | "accepted" | "expired" | "revoked";
    expires_at: string;
    created_at: string;
    invited_by_email: string | null;
}

export interface InvitationsListResponse {
    items: Invitation[];
    total: number;
}

export async function acceptInvitation(token: string): Promise<InviteAcceptResponse> {
    return fetchAPI("/auth/invite/accept", {
        method: "POST",
        body: JSON.stringify({ token }),
    });
}

export async function createInvitation(data: {
    email: string;
    team_ids?: string[];
    role?: string;
}): Promise<Invitation> {
    return fetchAPI("/invitations", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export async function getInvitations(): Promise<InvitationsListResponse> {
    return fetchAPI<InvitationsListResponse>("/invitations");
}

export async function revokeInvitation(id: string): Promise<void> {
    return fetchAPI(`/invitations/${id}`, { method: "DELETE" });
}

export async function resendInvitation(id: string): Promise<Invitation> {
    return fetchAPI<Invitation>(`/invitations/${id}/resend`, { method: "POST" });
}

// Chat API
export type Persona = "executive" | "technical" | "product";

export interface ChatRequest {
    message: string;
    repository?: string | string[] | undefined;
    author?: string | undefined;
    persona?: Persona | undefined;
    conversationId?: string | undefined;
    days?: number | undefined;
    teamId?: string | undefined;
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
 * @param onEvent - Callback for each streaming event received
 * @param onDone - Callback when streaming is complete (after type=done)
 * @param onError - Callback on error
 */
export type ChatStreamEvent =
    | { type: "metadata"; conversation_id?: string; sources?: unknown; activities_count?: number; confidence_score?: number; confidence_explanation?: string; generation_id?: string; prompt_version_id?: string; trace_id?: string }
    | { type: "delta"; text: string }
    | { type: "done"; message_id?: string };

export async function sendChatMessageStream(
    request: ChatRequest,
    onEvent: (event: ChatStreamEvent) => void,
    onDone: (messageId?: string) => void,
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
        let buffer = "";

        const processLine = (rawLine: string) => {
            const line = rawLine.replace(/\r$/, "");
            if (!line.startsWith("data: ")) return;

            const data = line.slice(6);
            if (!data) return;

            try {
                const parsed = JSON.parse(data) as ChatStreamEvent;
                onEvent(parsed);
                if (parsed.type === "done") {
                    onDone(parsed.message_id);
                    return "done" as const;
                }
                return undefined;
            } catch {
                // Backward compatibility / defensive fallback: treat as raw text.
                if (data === "[DONE]") {
                    onDone();
                    return "done" as const;
                }
                onEvent({ type: "delta", text: data });
                return undefined;
            }
        };

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Split by \n, keep last partial line in buffer.
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";

            for (const line of lines) {
                const status = processLine(line);
                if (status === "done") return;
            }
        }

        // Process any remaining buffered line (if it is complete enough).
        if (buffer.length > 0) {
            processLine(buffer);
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

export interface RefreshRepositoriesResponse {
    status: string;
    repositories_discovered: number;
    message: string;
}

export async function refreshGitHubRepositories(): Promise<RefreshRepositoriesResponse> {
    return fetchAPI<RefreshRepositoriesResponse>("/settings/github/refresh", {
        method: "POST",
    });
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
    preview?: string; // Preview of last assistant message
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
    // Context fields
    team_id?: string | null;
    persona?: string | null;
    days?: number | null;
    repositories?: string[] | null;
}

export async function getConversation(id: string): Promise<ConversationDetail> {
    return fetchAPI<ConversationDetail>(`/conversations/${id}`);
}

// Teams API
export interface Team {
    id: string;
    name: string;
    slug: string;
    description: string | null;
    color: string | null;
    is_default: boolean;
    github_team_slug: string | null;
    repositories_count: number;
    created_at: string;
    updated_at: string;
}

export interface RepositorySummary {
    id: string;
    name: string;
    url: string;
    is_active: boolean;
    activities_count: number;
}

export interface TeamDetail extends Team {
    repositories: RepositorySummary[];
}

export interface TeamListResponse {
    items: Team[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

export interface TeamCreateRequest {
    name: string;
    description?: string;
    color?: string;
    repository_ids?: string[];
    github_team_slug?: string;
}

export interface TeamUpdateRequest {
    name?: string;
    description?: string;
    color?: string;
    is_default?: boolean;
    github_team_slug?: string;
}

export async function getTeams(page: number = 1, pageSize: number = 20): Promise<TeamListResponse> {
    return fetchAPI<TeamListResponse>(`/teams?page=${page}&page_size=${pageSize}`);
}

export async function getTeam(id: string): Promise<TeamDetail> {
    return fetchAPI<TeamDetail>(`/teams/${id}`);
}

export async function createTeam(data: TeamCreateRequest): Promise<Team> {
    return fetchAPI<Team>("/teams", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export async function updateTeam(id: string, data: TeamUpdateRequest): Promise<Team> {
    return fetchAPI<Team>(`/teams/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
    });
}

export async function deleteTeam(id: string): Promise<void> {
    return fetchAPI(`/teams/${id}`, { method: "DELETE" });
}

export async function getDefaultTeam(): Promise<Team | null> {
    return fetchAPI<Team | null>("/teams/default");
}

export async function ensureDefaultTeam(): Promise<Team> {
    return fetchAPI<Team>("/teams/default", { method: "POST" });
}

export async function setDefaultTeam(teamId: string): Promise<Team> {
    return fetchAPI<Team>("/teams/default", {
        method: "PUT",
        body: JSON.stringify({ team_id: teamId }),
    });
}

export async function addRepositoriesToTeam(teamId: string, repositoryIds: string[]): Promise<{ added: number; message: string }> {
    return fetchAPI(`/teams/${teamId}/repositories`, {
        method: "POST",
        body: JSON.stringify({ repository_ids: repositoryIds }),
    });
}

export async function removeRepositoriesFromTeam(teamId: string, repositoryIds: string[]): Promise<{ removed: number; message: string }> {
    return fetchAPI(`/teams/${teamId}/repositories`, {
        method: "DELETE",
        body: JSON.stringify({ repository_ids: repositoryIds }),
    });
}

export interface TeamSyncResult {
    synced_teams: number;
    created_teams: number;
    updated_teams: number;
    total_repos_linked: number;
    message: string;
}

export async function syncGitHubTeams(): Promise<TeamSyncResult> {
    return fetchAPI("/teams/sync", {
        method: "POST",
    });
}

// ============================================================
// Metrics API
// ============================================================

export interface DoraMetric {
    value: number | string;
    formatted: string;
    change: number | null;
    trend: "up" | "down" | "stable" | null;
    status: "elite" | "high" | "medium" | "low";
}

export interface DoraMetricsResponse {
    deployment_frequency: DoraMetric;
    lead_time: DoraMetric;
    change_failure_rate: DoraMetric;
    mttr: DoraMetric;
    overall_level: "elite" | "high" | "medium" | "low";
    period_start: string;
    period_end: string;
}

export async function getDoraMetrics(days: number = 30, teamId?: string): Promise<DoraMetricsResponse> {
    const params = new URLSearchParams({ days: days.toString() });
    if (teamId) {
        params.append("team_id", teamId);
    }
    return fetchAPI<DoraMetricsResponse>(`/metrics/dora?${params.toString()}`);
}

// ============================================================
// Feedback API
// ============================================================

export type FeedbackType = "thumbs_up" | "thumbs_down";

export interface FeedbackCreate {
    feedback_type: FeedbackType;
    message_id: string; // Idempotency scope
    conversation_id: string;
    generation_id: string;
    prompt_version_id: string;
    trace_id?: string | undefined;
    persona?: Persona | undefined;
    metadata?: Record<string, unknown> | undefined;
}

export interface FeedbackResponse {
    feedback_id: string;
    created: boolean;
    message: string;
}

export interface FeedbackForConversationItem {
    message_id: string;
    feedback_type: FeedbackType;
    created_at: string;
}

export interface FeedbackForConversationResponse {
    conversation_id: string;
    items: FeedbackForConversationItem[];
}

export async function submitFeedback(feedback: FeedbackCreate): Promise<FeedbackResponse> {
    return fetchAPI<FeedbackResponse>("/feedback", {
        method: "POST",
        body: JSON.stringify(feedback),
    });
}

export async function getFeedbackForConversation(
    conversationId: string
): Promise<FeedbackForConversationResponse> {
    return fetchAPI<FeedbackForConversationResponse>(`/feedback/conversation/${conversationId}`);
}

export async function logResponseDisplayed(data: {
    generation_id: string;
    message_id: string;
    trace_id?: string | undefined;
}): Promise<void> {
    const params = new URLSearchParams({
        generation_id: data.generation_id,
        message_id: data.message_id,
    });
    if (data.trace_id) params.set("trace_id", data.trace_id);

    // Backend expects query params (not JSON body)
    return fetchAPI(`/feedback/events/displayed?${params.toString()}`, {
        method: "POST",
    });
}
