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
  thread_id: string;
  conversation_id?: string;
  title: string;
  capability: "general";
  model_config_id: number;
  status: string;
  message_count: number;
  last_message_at: string;
  created_at: string;
  updated_at?: string;
  execution_engine?: string;
  model_name?: string;
}

export interface ChatHistoryMessageItem {
  message_id: string;
  run_id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  sequence?: number;
  status: string;
  model_config_id: number;
  model_name: string;
  citations: unknown[];
  tool_calls: unknown[];
  created_at: string;
  capability?: "general";
  capabilities?: string[];
  execution_engine?: string;
}

export interface ChatHistoryDetailResponse {
  conversation_id?: string;
  thread_id?: string;
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
  thread_id?: string | null;
  conversation_id?: string | null;
  capability: "general";
}

export interface AgentRunCreateRequest {
  message: string;
  model_config_id: number;
  capability: "general";
  client_request_id: string;
  thread_id: string | null;
}

export interface AgentRunResponse {
  run_id: string;
  thread_id: string;
  user_message_id: string;
  assistant_message_id: string;
  status: string;
  content: string;
  last_event_id: string | null;
  model_name: string;
  usage: unknown;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  stream_url: string;
}

export interface AgentActiveRunResponse {
  run_id: string;
  thread_id: string;
  user_message_id: string;
  assistant_message_id: string;
  status: string;
  content: string;
  last_event_id: string | null;
  model_name: string;
  usage: unknown;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface AgentAbortRunResponse {
  run_id: string;
  status: string;
}

export interface AgentDeleteThreadResponse {
  thread_id: string;
  deleted: boolean;
  active_run_id: string | null;
  run_status: string | null;
}
