export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  loading?: boolean;
  error?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
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
