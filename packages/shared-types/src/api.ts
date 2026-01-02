/**
 * API-specific types for DevBridge
 *
 * These types define the shape of API requests and responses.
 */

// ============================================================
// HTTP Types
// ============================================================

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface ApiRequestConfig {
    method: HttpMethod;
    headers?: Record<string, string>;
    body?: unknown;
    params?: Record<string, string | number | boolean>;
}

// ============================================================
// Webhook Types
// ============================================================

export interface GitHubWebhookPayload {
    action?: string;
    repository: {
        id: number;
        name: string;
        full_name: string;
        html_url: string;
    };
    sender: {
        login: string;
        avatar_url: string;
    };
}

export interface PushWebhookPayload extends GitHubWebhookPayload {
    ref: string;
    before: string;
    after: string;
    commits: WebhookCommit[];
    head_commit: WebhookCommit | null;
    pusher: {
        name: string;
        email: string;
    };
}

export interface WebhookCommit {
    id: string;
    message: string;
    timestamp: string;
    author: {
        name: string;
        email: string;
        username?: string;
    };
    added: string[];
    removed: string[];
    modified: string[];
}

export interface PullRequestWebhookPayload extends GitHubWebhookPayload {
    action: "opened" | "closed" | "reopened" | "synchronize" | "edited";
    number: number;
    pull_request: {
        id: number;
        number: number;
        title: string;
        body: string | null;
        state: "open" | "closed";
        merged: boolean;
        head: {
            ref: string;
            sha: string;
        };
        base: {
            ref: string;
            sha: string;
        };
    };
}

// ============================================================
// Health Check Types
// ============================================================

export interface HealthStatus {
    status: "healthy" | "degraded" | "unhealthy";
    version: string;
    timestamp: string;
    services: ServiceHealth[];
}

export interface ServiceHealth {
    name: string;
    status: "up" | "down" | "degraded";
    latencyMs?: number;
    message?: string;
}

// ============================================================
// Authentication Types
// ============================================================

export interface AuthTokens {
    accessToken: string;
    refreshToken: string;
    expiresIn: number;
    tokenType: "Bearer";
}

export interface LoginRequest {
    code: string; // OAuth code from GitHub
    redirectUri: string;
}

export interface RefreshTokenRequest {
    refreshToken: string;
}

// ============================================================
// Search Types
// ============================================================

export interface SearchQuery {
    query: string;
    filters?: SearchFilters;
    pagination?: {
        page: number;
        perPage: number;
    };
}

export interface SearchFilters {
    repositoryId?: string;
    dateFrom?: string;
    dateTo?: string;
    pillars?: string[];
    authors?: string[];
}

export interface SearchResult<T> {
    items: T[];
    total: number;
    query: string;
    processingTimeMs: number;
}

// ============================================================
// Notification Types
// ============================================================

export interface SlackNotification {
    channel: string;
    text: string;
    blocks?: SlackBlock[];
}

export interface SlackBlock {
    type: "section" | "divider" | "header" | "context";
    text?: {
        type: "plain_text" | "mrkdwn";
        text: string;
    };
    fields?: Array<{
        type: "plain_text" | "mrkdwn";
        text: string;
    }>;
}
