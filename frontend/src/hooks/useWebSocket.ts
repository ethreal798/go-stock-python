import { useEffect, useRef, useCallback, useState } from 'react'
import type { WSMessage } from '@/types'

type MessageHandler = (data: WSMessage) => void

interface UseWebSocketOptions {
  url?: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
}

interface UseWebSocketReturn {
  connected: boolean
  subscribe: (channel: string, handler: MessageHandler) => () => void
  send: (message: unknown) => void
  disconnect: () => void
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    url = `ws://${window.location.host}/ws`,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onOpen,
    onClose,
    onError,
  } = options

  const wsRef = useRef<WebSocket | null>(null)
  const handlersRef = useRef<Map<string, Set<MessageHandler>>>(new Map())
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const mountedRef = useRef(true)

  const [connected, setConnected] = useState(false)

  const connect = useCallback(() => {
    if (!mountedRef.current) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return
        setConnected(true)
        reconnectAttemptsRef.current = 0
        onOpen?.()
      }

      ws.onclose = () => {
        if (!mountedRef.current) return
        setConnected(false)
        onClose?.()

        // 自动重连
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          reconnectTimerRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }

      ws.onerror = (error) => {
        onError?.(error)
      }

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data as string)
          const channelHandlers = handlersRef.current.get(msg.channel)
          if (channelHandlers) {
            channelHandlers.forEach((handler) => handler(msg))
          }
          // 全局通配符订阅
          const allHandlers = handlersRef.current.get('*')
          if (allHandlers) {
            allHandlers.forEach((handler) => handler(msg))
          }
        } catch {
          // ignore parse error
        }
      }
    } catch {
      // ignore connection error
    }
  }, [url, reconnectInterval, maxReconnectAttempts, onOpen, onClose, onError])

  useEffect(() => {
    mountedRef.current = true
    connect()

    return () => {
      mountedRef.current = false
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
      }
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [connect])

  const subscribe = useCallback((channel: string, handler: MessageHandler) => {
    if (!handlersRef.current.has(channel)) {
      handlersRef.current.set(channel, new Set())
    }
    handlersRef.current.get(channel)!.add(handler)

    // 返回取消订阅函数
    return () => {
      handlersRef.current.get(channel)?.delete(handler)
    }
  }, [])

  const send = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  const disconnect = useCallback(() => {
    mountedRef.current = false
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
    }
    wsRef.current?.close()
    wsRef.current = null
    setConnected(false)
  }, [])

  return { connected, subscribe, send, disconnect }
}
