import request from "./index";
import type {
  ChatAvailableModel,
  ChatHistoryDetailResponse,
  ChatHistoryItem,
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
  request.get<ChatHistoryItem[]>("/agent/history", {
    params: {
      count: params?.count ?? 20,
      page: params?.page ?? 0,
    },
  });

// 获取指定会话的聊天详情
export const getChatHistoryDetail = (conversationId: string) =>
  request.get<ChatHistoryDetailResponse>(`/agent/history/${conversationId}`);

// 获取会话详情
export const getSession = (sessionId: string) =>
  request.get<{ data: ChatSession }>(`/agent/sessions/${sessionId}`);

// 删除会话
export const deleteSession = (sessionId: string) =>
  request.delete(`/agent/history/${sessionId}`);

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

// 创建新会话
export const createSession = (title?: string) =>
  request.post<{ data: ChatSession }>("/agent/sessions", { title });

export const abortConversation = (conversationId: string) =>
  request.post("/agent/abort", null, {
    params: { conversation_id: conversationId },
  });
