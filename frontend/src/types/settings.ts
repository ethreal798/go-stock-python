export type AIProvider = "openai" | "deepseek" | "bailian";

export interface AIModelProfile {
  id: string;
  provider: AIProvider;
  displayName: string;
  apiKey: string;
  baseUrl: string;
  model: string;
  maxTokens: number;
  temperature: number;
  enabled: boolean;
}

export interface AIConfig {
  provider: AIProvider;
  models: AIModelProfile[];
}

export interface NotifyConfig {
  dingdingEnabled: boolean;
  dingdingToken?: string;
  dingdingSecret?: string;
  emailEnabled: boolean;
  emailSmtp?: string;
  emailFrom?: string;
  emailTo?: string;
}

export interface DataSourceConfig {
  tushareToken?: string;
  iwencaiEnabled: boolean;
}

export interface AppSettings {
  ai: AIConfig;
  notify: NotifyConfig;
  dataSource: DataSourceConfig;
  theme: "light" | "dark";
  language: string;
}

export interface AIModelConfigCreateRequest {
  name: string;
  provider: string;
  base_url: string;
  model: string;
  max_output_tokens: number;
  temperature: number;
  timeout_seconds: number;
  enabled: boolean;
  extra_config?: Record<string, unknown>;
  api_key: string;
}

export interface AIModelConfigResponse {
  id: number;
  name: string;
  provider: string;
  base_url: string;
  model: string;
  api_key_configured: boolean;
  api_key_hint?: string;
  max_output_tokens: number;
  temperature: number;
  timeout_seconds: number;
  enabled: boolean;
  extra_config?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type AIModelConfigUpdateRequest = Partial<AIModelConfigCreateRequest>;

export interface AIModelConfigEnabledUpdateRequest {
  enabled: boolean;
}

export interface AIModelConfigTestRequest extends AIModelConfigCreateRequest {
  message?: string;
}

export interface AIModelConfigTestResponse {
  success: boolean;
  message: string;
  latency_ms: number | null;
  model: string | null;
  usage: Record<string, unknown> | null;
}

export type AIModelConfigListResponse = AIModelConfigResponse[];

export type AIModelConfigDetailResponse = AIModelConfigResponse;
