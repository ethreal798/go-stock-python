import request from './index'
import type { ChatSession } from '@/types'

// 发送消息（非流式）
export const sendMessage = (data: {
  sessionId?: string
  message: string
  model?: string
}) => request.post<{ data: { sessionId: string; reply: string } }>('/agent/chat', data)

// 获取会话列表
export const getSessionList = () =>
  request.get<{ data: ChatSession[] }>('/agent/sessions')

// 获取会话详情
export const getSession = (sessionId: string) =>
  request.get<{ data: ChatSession }>(`/agent/sessions/${sessionId}`)

// 删除会话
export const deleteSession = (sessionId: string) =>
  request.delete(`/agent/sessions/${sessionId}`)

// 清空会话消息
export const clearSession = (sessionId: string) =>
  request.post(`/agent/sessions/${sessionId}/clear`)

// 获取支持的模型列表
export const getModels = () =>
  request.get<{ data: string[] }>('/agent/models')

// 获取SSE流式对话URL
export const getStreamChatUrl = () => '/api/agent/chat/stream'

// 创建新会话
export const createSession = (title?: string) =>
  request.post<{ data: ChatSession }>('/agent/sessions', { title })
