export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  loading?: boolean;
  aborted?: boolean;
  error?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

export interface ChatHistoryItem {
  conversation_id: string;
  title: string;
  capability: "general";
  execution_engine: string;
  model_config_id: number;
  model_name: string;
  message_count: number;
  last_message_at: string;
  created_at: string;
  updated_at: string;
}

export interface ChatHistoryMessageItem {
  message_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  status: string;
  capability: "general";
  capabilities: string[];
  execution_engine: string;
  model_config_id: number;
  model_name: string;
  citations: unknown[];
  tool_calls: unknown[];
  created_at: string;
}

export interface ChatHistoryDetailResponse {
  conversation_id: string;
  messages: ChatHistoryMessageItem[];
  created_at: string | null;
  updated_at: string | null;
}

export interface ChatAvailableModel {
  model_config_id: number;
  name: string;
  provider: string;
  base_url: string;
  model_name: string;
  api_key_configured: boolean;
  max_output_tokens: number;
  temperature: number;
}

export interface ChatStreamRequest {
  message: string;
  model_config_id: number;
  conversation_id: string | null;
  capability: "general";
}
