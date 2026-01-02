/**
 * @devbridge/shared-types
 *
 * Shared TypeScript types for DevBridge frontend and backend communication.
 * These types should mirror the Pydantic schemas in the backend.
 */

// ============================================================
// Repository Types
// ============================================================

export interface Repository {
  id: string;
  url: string;
  name: string;
  owner: string;
  description?: string;
  defaultBranch: string;
  createdAt: string;
  updatedAt: string;
}

export interface RepositoryCreate {
  url: string;
  description?: string;
}

export interface RepositoryUpdate {
  description?: string;
  defaultBranch?: string;
}

// ============================================================
// Commit Types
// ============================================================

export interface Commit {
  sha: string;
  message: string;
  author: string;
  authorEmail: string;
  timestamp: string;
  filesChanged: number;
  additions: number;
  deletions: number;
}

export interface CommitDetail extends Commit {
  files: CommitFile[];
  parentShas: string[];
}

export interface CommitFile {
  filename: string;
  status: "added" | "modified" | "removed" | "renamed";
  additions: number;
  deletions: number;
  patch?: string;
}

// ============================================================
// Translation Types
// ============================================================

export interface BusinessTranslation {
  id: string;
  commitSha: string;
  title: string;
  technicalSummary: string;
  businessValue: string;
  risksMitigated: string[];
  alignedPillars: BusinessPillar[];
  metrics: ImpactMetric[];
  confidenceScore: number;
  createdAt: string;
}

export interface BusinessPillar {
  id: string;
  name: string;
  description?: string;
}

export interface ImpactMetric {
  id: string;
  name: string;
  value: number;
  unit: string;
  currency?: string;
}

// ============================================================
// Chat Types
// ============================================================

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  metadata?: ChatMessageMetadata;
}

export interface ChatMessageMetadata {
  sources?: CitationSource[];
  confidence?: number;
  processingTimeMs?: number;
}

export interface CitationSource {
  type: "commit" | "translation" | "document";
  id: string;
  title: string;
  url?: string;
}

export interface ChatRequest {
  message: string;
  repositoryId?: string;
  conversationId?: string;
}

export interface ChatResponse {
  message: ChatMessage;
  conversationId: string;
}

// ============================================================
// User Types
// ============================================================

export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
  role: UserRole;
  createdAt: string;
}

export type UserRole = "admin" | "member" | "viewer";

// ============================================================
// API Response Types
// ============================================================

export interface ApiResponse<T> {
  data: T;
  meta?: ApiMeta;
}

export interface ApiMeta {
  total?: number;
  page?: number;
  perPage?: number;
  hasMore?: boolean;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ============================================================
// Pagination Types
// ============================================================

export interface PaginationParams {
  page?: number;
  perPage?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
}

// Re-export all
export * from "./api";
