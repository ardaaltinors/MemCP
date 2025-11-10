export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  api_key_created_at: string | null;
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_at: string;
}

export interface ApiKeyResponse {
  has_api_key: boolean;
  api_key?: string;
  created_at?: string;
  connection_url?: string;
}

export interface CreateApiKeyResponse {
  api_key: string;
  created_at: string;
}

export interface RevokeApiKeyResponse {
  message: string;
}

// Memory Graph API Types
export interface ApiMemoryNode {
  id: string;
  label: string;
  content: string;
  created_at: string;
  type: string;
  tags: string[];
}

export interface ApiMemoryEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
}

export interface MemoryGraphResponse {
  nodes: ApiMemoryNode[];
  edges: ApiMemoryEdge[];
  total_nodes: number;
  total_edges: number;
}

// UI-specific types for the graph component
export interface MemoryNode {
  id: string;
  title: string;
  content: string;
  type: 'memory' | 'concept' | 'fact' | 'connection' | 'insight';
  x: number;
  y: number;
  connections: string[];
  timestamp: string;
  strength: number;
  tags: string[];
}

export interface Connection {
  from: string;
  to: string;
  strength: number;
}

// Memory Management Types
export interface Memory {
  id: string;
  user_id: string;
  content: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateMemoryRequest {
  content: string;
  tags?: string[];
}

export interface UpdateMemoryRequest {
  content?: string;
  tags?: string[];
}

export interface DeleteMemoryResponse {
  message: string;
}

// Processed User Profile Type
export interface ProcessedUserProfile {
  id: number;
  user_id: string;
  metadata_json?: Record<string, any>;
  summary_text?: string;
  created_at: string;
  updated_at: string;
}

export interface DeletionStats {
  user_id: string;
  username: string;
  memories_deleted: number;
  vector_memories_deleted: number;
  oauth_accounts_deleted: number;
  user_messages_deleted: number;
  processed_profiles_deleted: number;
}

export interface DeleteAccountResponse {
  message: string;
  deletion_stats: DeletionStats;
} 