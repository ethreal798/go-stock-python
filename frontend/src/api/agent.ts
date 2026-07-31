import request from "./index";
import type {
  AgentActiveRunResponse,
  AgentAbortRunResponse,
  AgentDeleteThreadResponse,
  AgentRunCreateRequest,
  AgentRunResponse,
  ChatAvailableModel,
  ChatHistoryItem,
  ChatHistoryMessageItem,
  ChatSession,
  ChatStreamRequest,
} from "@/types/agent";

// 发送消息（非流式）
export const sendMessage = (data: {
  sessionId?: string;
  message: string;
  model?: string;
}) =>
  request.post<{ data: { sessionId: string; reply: string } }>(
    "/agent/chat",
    data,
  );

// 获取会话列表
export const getSessionList = () =>
  request.get<{ data: ChatSession[] }>("/agent/sessions");

// 获取历史聊天列表
export const getChatHistory = (params?: { count?: number; page?: number }) =>
  request.get<ChatHistoryItem[]>("/agent/threads", {
    params: {
      count: params?.count ?? 20,
      page: params?.page ?? 0,
    },
  });

export const getThreadMessages = (threadId: string) =>
  request.get<ChatHistoryMessageItem[]>(`/agent/threads/${threadId}/messages`);

// 获取会话详情
export const getSession = (sessionId: string) =>
  request.get<{ data: ChatSession }>(`/agent/sessions/${sessionId}`);

export const deleteThread = (threadId: string) =>
  request.delete<AgentDeleteThreadResponse>(`/agent/threads/${threadId}`);

// 清空会话消息
export const clearSession = (sessionId: string) =>
  request.post(`/agent/sessions/${sessionId}/clear`);

// 获取聊天可用模型列表
export const getAvailableChatModels = () =>
  request.get<ChatAvailableModel[]>("/agent/models");

// 获取SSE流式对话URL
export const getStreamChatUrl = () => "/api/v1/agent/chat";

// 构造流式聊天请求体
export const buildStreamChatPayload = (
  data: ChatStreamRequest,
): ChatStreamRequest => data;

export const createAgentRun = (data: AgentRunCreateRequest) =>
  request.post<AgentRunResponse>("/agent/runs", data);

export const getThreadActiveRun = (threadId: string) =>
  request.get<AgentActiveRunResponse>(`/agent/threads/${threadId}/active-run`);

// 创建新会话
export const createSession = (title?: string) =>
  request.post<{ data: ChatSession }>("/agent/sessions", { title });

export const abortRun = (runId: string) =>
  request.post<AgentAbortRunResponse>(`/agent/runs/${runId}/abort`);
