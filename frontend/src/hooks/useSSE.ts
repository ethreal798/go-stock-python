import { useEffect, useRef, useCallback, useState } from 'react'

interface UseSSEOptions {
  onMessage?: (data: string) => void
  onDone?: () => void
  onError?: (error: Event) => void
}

interface UseSSEReturn {
  loading: boolean
  connect: (url: string, body: unknown) => void
  abort: () => void
}

export const useSSE = (options: UseSSEOptions = {}): UseSSEReturn => {
  const { onMessage, onDone, onError } = options
  const abortControllerRef = useRef<AbortController | null>(null)
  const [loading, setLoading] = useState(false)

  const abort = useCallback(() => {
    abortControllerRef.current?.abort()
    setLoading(false)
  }, [])

  const connect = useCallback(
    async (url: string, body: unknown) => {
      // 先中止上一次请求
      abortControllerRef.current?.abort()
      const controller = new AbortController()
      abortControllerRef.current = controller
      setLoading(true)

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('Response body is not readable')
        }

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (data === '[DONE]') {
                onDone?.()
                setLoading(false)
                return
              }
              if (data) {
                onMessage?.(data)
              }
            }
          }
        }

        onDone?.()
        setLoading(false)
      } catch (error) {
        if ((error as Error).name === 'AbortError') {
          // 用户主动中止
          return
        }
        onError?.(error as Event)
        setLoading(false)
      }
    },
    [onMessage, onDone, onError],
  )

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort()
    }
  }, [])

  return { loading, connect, abort }
}
