import React, { useCallback, useEffect, useRef, useState } from "react";
import { message } from "antd";
import { useSSE } from "@/hooks/useSSE";
import { useAuthStore } from "@/stores/authStore";
import {
  abortRun,
  createAgentRun,
  deleteThread,
  getAvailableChatModels,
  getChatHistory,
  getThreadActiveRun,
  getThreadMessages,
} from "@/api/agent";
import type {
  ChatAvailableModel,
  ChatHistoryItem,
  ChatHistoryMessageItem,
  ChatMessage,
} from "@/types/agent";
import { generateClientRequestId } from "@/utils/clientRequestId";
import AgentChatHeader from "./components/AgentChatHeader";
import AgentComposer from "./components/AgentComposer";
import AgentMessageList from "./components/AgentMessageList";
import AgentSidebar from "./components/AgentSidebar";

const AgentPage: React.FC = () => {
  const isGuestMode = useAuthStore((state) => state.isGuestMode);
  const [sessions, setSessions] = useState<ChatHistoryItem[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatHistoryItem | null>(
    null,
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [availableModels, setAvailableModels] = useState<ChatAvailableModel[]>(
    [],
  );
  const [selectedModelConfigId, setSelectedModelConfigId] = useState<
    string | null
  >(null);
  const [selectedModelName, setSelectedModelName] = useState("");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const activeThreadIdRef = useRef<string | null>(null);
  const activeRunIdRef = useRef<string | null>(null);
  const lastEventIdRef = useRef<string | null>(null);
  const restoredThreadRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchSessions = useCallback((page = 0, count = 20) => {
    return getChatHistory({ page, count })
      .then((res) => {
        const list = (res.data ?? []) as ChatHistoryItem[];
        setSessions(list);
        return list;
      })
      .catch(() => [] as ChatHistoryItem[]);
  }, []);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const mapHistoryMessages = useCallback((items: ChatHistoryMessageItem[]) => {
    return items.map((m) => ({
      id: m.message_id,
      role: m.role,
      content: m.content,
      timestamp: Number.isFinite(Date.parse(m.created_at))
        ? Date.parse(m.created_at)
        : Date.now(),
    })) as ChatMessage[];
  }, []);

  const getSessionThreadId = useCallback((session: ChatHistoryItem | null) => {
    return session?.thread_id ?? session?.conversation_id ?? null;
  }, []);

  const getPersistedActiveThreadId = useCallback(() => {
    try {
      return sessionStorage.getItem("agent:active_thread_id");
    } catch {
      return null;
    }
  }, []);

  const persistActiveThreadId = useCallback((threadId: string | null) => {
    try {
      if (threadId) {
        sessionStorage.setItem("agent:active_thread_id", threadId);
      } else {
        sessionStorage.removeItem("agent:active_thread_id");
      }
    } catch {
      return;
    }
  }, []);

  const buildRunStreamUrl = useCallback(
    (streamUrl: string, afterEventId: string | null) => {
      const url = new URL(streamUrl, window.location.origin);
      url.searchParams.set("after_event_id", afterEventId ?? "");
      return url.pathname + url.search;
    },
    [],
  );

  const buildRunStreamUrlByRunId = useCallback(
    (runId: string, afterEventId: string | null) => {
      return buildRunStreamUrl(
        `/api/v1/agent/runs/${runId}/stream`,
        afterEventId,
      );
    },
    [buildRunStreamUrl],
  );

  const getPersistedLastEventId = useCallback((runId: string) => {
    try {
      return sessionStorage.getItem(`agent:last_event_id:${runId}`);
    } catch {
      return null;
    }
  }, []);

  const persistLastEventId = useCallback((runId: string, eventId: string) => {
    try {
      sessionStorage.setItem(`agent:last_event_id:${runId}`, eventId);
    } catch {
      return;
    }
  }, []);

  const clearPersistedLastEventId = useCallback((runId: string) => {
    try {
      sessionStorage.removeItem(`agent:last_event_id:${runId}`);
    } catch {
      return;
    }
  }, []);

  const finalizeAssistantMessage = useCallback(
    (patch: Partial<ChatMessage> = {}) => {
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (!last || last.role !== "assistant" || !last.loading) {
          return prev;
        }

        return [
          ...prev.slice(0, -1),
          {
            ...last,
            loading: false,
            ...patch,
          },
        ];
      });
    },
    [],
  );

  const {
    loading: sseLoading,
    connect: sseConnect,
    abort: sseAbort,
  } = useSSE({
    onMessage: ({ event, data, id }) => {
      if (id) {
        lastEventIdRef.current = id;
        if (activeRunIdRef.current) {
          persistLastEventId(activeRunIdRef.current, id);
        }
      }

      if (event === "snapshot") {
        try {
          const parsed = JSON.parse(data) as {
            run_id?: string;
            thread_id?: string;
            message_id?: string;
            content?: string;
            status?: string;
            last_event_id?: string | null;
          };

          if (parsed.run_id) {
            activeRunIdRef.current = parsed.run_id;
          }
          if (parsed.thread_id) {
            activeThreadIdRef.current = parsed.thread_id;
          }
          if (parsed.last_event_id) {
            lastEventIdRef.current = parsed.last_event_id;
            if (activeRunIdRef.current) {
              persistLastEventId(activeRunIdRef.current, parsed.last_event_id);
            }
          }
          if (parsed.message_id) {
            const messageId = parsed.message_id;
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (!last || last.role !== "assistant") {
                return prev;
              }

              return [
                ...prev.slice(0, -1),
                {
                  ...last,
                  id: messageId,
                  content: parsed.content ?? last.content,
                  loading: parsed.status === "running" ? last.loading : false,
                },
              ];
            });
          }
        } catch {
          return;
        }
        return;
      }

      if (event === "metadata") {
        try {
          const parsed = JSON.parse(data) as {
            thread_id?: string;
            conversation_id?: string;
            run_id?: string;
            last_event_id?: string;
          };

          const threadId = parsed.thread_id ?? parsed.conversation_id;
          if (threadId) {
            activeThreadIdRef.current = threadId;
          }
          if (parsed.run_id) {
            activeRunIdRef.current = parsed.run_id;
          }
          if (parsed.last_event_id) {
            lastEventIdRef.current = parsed.last_event_id;
            if (activeRunIdRef.current) {
              persistLastEventId(activeRunIdRef.current, parsed.last_event_id);
            }
          }
        } catch {
          return;
        }
      }

      if (event === "done") {
        try {
          const parsed = JSON.parse(data) as { run_id?: string };
          if (parsed.run_id) {
            activeRunIdRef.current = parsed.run_id;
          }
        } catch {
          return;
        }
        return;
      }

      try {
        const parsed = JSON.parse(data) as { content?: string; delta?: string };
        const delta = parsed.content ?? parsed.delta ?? "";
        if (!delta) {
          return;
        }
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (!last || last.role !== "assistant") {
            return prev;
          }
          return [
            ...prev.slice(0, -1),
            { ...last, content: last.content + delta },
          ];
        });
      } catch {
        if (event !== "delta") {
          return;
        }
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (!last || last.role !== "assistant") {
            return prev;
          }
          return [
            ...prev.slice(0, -1),
            { ...last, content: last.content + data },
          ];
        });
      }
    },
    onDone: () => {
      setMessages((prev) =>
        prev.map((m) =>
          m.loading ? { ...m, loading: false, aborted: false } : m,
        ),
      );
      if (activeRunIdRef.current) {
        clearPersistedLastEventId(activeRunIdRef.current);
      }
      fetchSessions().then((list) => {
        if (!currentSession && list.length > 0) {
          setCurrentSession(list[0]);
          return;
        }
        if (currentSession) {
          const currentThreadId = getSessionThreadId(currentSession);
          const matched = list.find(
            (item) =>
              (item.thread_id ?? item.conversation_id ?? null) ===
              currentThreadId,
          );
          if (matched) {
            setCurrentSession(matched);
          }
        }
      });
      scrollToBottom();
    },
    onError: () => {
      setMessages((prev) =>
        prev.map((m) =>
          m.loading
            ? {
                ...m,
                loading: false,
                aborted: false,
                error: true,
                content: "请求失败，请重试",
              }
            : m,
        ),
      );
    },
  });

  const subscribeRun = useCallback(
    (runId: string, afterEventId: string | null) => {
      const url = buildRunStreamUrlByRunId(runId, afterEventId);
      sseConnect(url, undefined, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
    },
    [buildRunStreamUrlByRunId, sseConnect],
  );

  const handleAbort = useCallback(async () => {
    const runId = activeRunIdRef.current;
    finalizeAssistantMessage({ aborted: true, error: false });
    sseAbort();
    if (!runId) {
      return;
    }
    try {
      await abortRun(runId);
      clearPersistedLastEventId(runId);
    } catch {
      message.error("取消对话失败");
    }
  }, [clearPersistedLastEventId, finalizeAssistantMessage, sseAbort]);

  const loadConversation = useCallback(
    async (threadId: string) => {
      if (sseLoading) {
        sseAbort();
      }
      activeThreadIdRef.current = threadId;
      persistActiveThreadId(threadId);
      activeRunIdRef.current = null;
      lastEventIdRef.current = null;
      setMessages([]);
      setHistoryLoading(true);

      try {
        const res = await getThreadMessages(threadId);
        const list = ((
          res.data as unknown as { data?: ChatHistoryMessageItem[] }
        )?.data ??
          res.data ??
          []) as ChatHistoryMessageItem[];
        setMessages(mapHistoryMessages(list));

        try {
          const activeRunRes = await getThreadActiveRun(threadId);
          const activeRun =
            (activeRunRes.data as unknown as { data?: unknown })?.data ??
            activeRunRes.data;
          if (!activeRun) {
            return;
          }

          const parsed = activeRun as {
            run_id?: string;
            thread_id?: string;
            assistant_message_id?: string;
            status?: string;
            content?: string;
            last_event_id?: string | null;
          };
          const runId = parsed.run_id;
          const status = parsed.status ?? "";
          const shouldSubscribe = status === "pending" || status === "running";

          if (runId && shouldSubscribe) {
            activeRunIdRef.current = runId;
            activeThreadIdRef.current = parsed.thread_id ?? threadId;
            lastEventIdRef.current = parsed.last_event_id ?? null;

            if (parsed.assistant_message_id) {
              const assistantMessageId = parsed.assistant_message_id;
              setMessages((prev) => {
                const exists = prev.some((m) => m.id === assistantMessageId);
                if (exists) {
                  return prev.map((m) =>
                    m.id === assistantMessageId
                      ? {
                          ...m,
                          loading: true,
                          content: parsed.content ?? m.content,
                        }
                      : m,
                  );
                }
                return [
                  ...prev,
                  {
                    id: assistantMessageId,
                    role: "assistant",
                    content: parsed.content ?? "",
                    timestamp: Date.now(),
                    loading: true,
                  },
                ];
              });
            }

            const persistedLast = getPersistedLastEventId(runId);
            const afterEventId = persistedLast ?? parsed.last_event_id ?? "";
            subscribeRun(runId, afterEventId);
          }
        } catch {
          // ignore
        }
      } catch {
        message.error("获取聊天记录失败");
        setMessages([]);
      } finally {
        setHistoryLoading(false);
      }
    },
    [
      getPersistedLastEventId,
      mapHistoryMessages,
      persistActiveThreadId,
      sseLoading,
      sseAbort,
      subscribeRun,
    ],
  );

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  useEffect(() => {
    if (restoredThreadRef.current) {
      return;
    }
    if (currentSession) {
      restoredThreadRef.current = true;
      return;
    }
    if (sessions.length === 0) {
      return;
    }

    restoredThreadRef.current = true;
    const persistedThreadId = getPersistedActiveThreadId();
    if (!persistedThreadId) {
      return;
    }

    const matched = sessions.find(
      (session) =>
        (session.thread_id ?? session.conversation_id) === persistedThreadId,
    );
    if (matched) {
      setCurrentSession(matched);
      loadConversation(persistedThreadId);
    }
  }, [currentSession, getPersistedActiveThreadId, loadConversation, sessions]);

  useEffect(() => {
    getAvailableChatModels()
      .then((res) => {
        const list = ((res.data as { data?: ChatAvailableModel[] })?.data ??
          res.data ??
          []) as ChatAvailableModel[];
        setAvailableModels(list);
        const first = list[0];
        if (first) {
          setSelectedModelConfigId(String(first.model_config_id));
          setSelectedModelName(first.model_name);
        } else {
          setSelectedModelConfigId(null);
          setSelectedModelName("");
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async () => {
    const content = inputValue.trim();
    if (!content || sseLoading) {
      return;
    }
    if (!selectedModelConfigId) {
      message.warning("请先选择可用模型");
      return;
    }

    setInputValue("");
    const clientRequestId = generateClientRequestId();
    const tempUserMessageId = `user-${clientRequestId}`;
    const tempAssistantMessageId = `assistant-${clientRequestId}`;

    const userMsg: ChatMessage = {
      id: tempUserMessageId,
      role: "user",
      content,
      timestamp: Date.now(),
    };
    const assistantMsg: ChatMessage = {
      id: tempAssistantMessageId,
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      loading: true,
    };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    const threadId =
      getSessionThreadId(currentSession) ?? activeThreadIdRef.current;

    try {
      const res = await createAgentRun({
        message: content,
        model_config_id: Number(selectedModelConfigId),
        capability: "general",
        client_request_id: clientRequestId,
        thread_id: threadId,
      });
      const run = (res.data as unknown as { data?: unknown })?.data ?? res.data;
      const parsed = run as {
        run_id: string;
        thread_id: string;
        user_message_id: string;
        assistant_message_id: string;
        content: string;
        last_event_id: string | null;
      };

      activeRunIdRef.current = parsed.run_id;
      activeThreadIdRef.current = parsed.thread_id;
      persistActiveThreadId(parsed.thread_id);
      lastEventIdRef.current = parsed.last_event_id;

      if (parsed.last_event_id) {
        persistLastEventId(parsed.run_id, parsed.last_event_id);
      } else {
        clearPersistedLastEventId(parsed.run_id);
      }

      setMessages((prev) =>
        prev.map((m) => {
          if (m.id === tempUserMessageId) {
            return { ...m, id: parsed.user_message_id };
          }
          if (m.id === tempAssistantMessageId) {
            return {
              ...m,
              id: parsed.assistant_message_id,
              content: parsed.content ?? "",
            };
          }
          return m;
        }),
      );

      const persistedLast = getPersistedLastEventId(parsed.run_id);
      const afterEventId = persistedLast ?? parsed.last_event_id ?? "";
      subscribeRun(parsed.run_id, afterEventId);
    } catch {
      finalizeAssistantMessage({
        loading: false,
        aborted: false,
        error: true,
        content: "请求失败，请重试",
      });
    }
  };

  const handleNewSession = () => {
    setCurrentSession(null);
    setMessages([]);
    setInputValue("");
    activeThreadIdRef.current = null;
    activeRunIdRef.current = null;
    lastEventIdRef.current = null;
    persistActiveThreadId(null);
  };

  const handleDeleteSession = async (threadId: string) => {
    try {
      await deleteThread(threadId);
      setSessions((prev) =>
        prev.filter(
          (session) =>
            (session.thread_id ?? session.conversation_id) !== threadId,
        ),
      );

      if (getSessionThreadId(currentSession) === threadId) {
        sseAbort();
        setCurrentSession(null);
        setMessages([]);
        activeThreadIdRef.current = null;
        persistActiveThreadId(null);
        if (activeRunIdRef.current) {
          clearPersistedLastEventId(activeRunIdRef.current);
        }
        activeRunIdRef.current = null;
        lastEventIdRef.current = null;
      }

      message.success("会话已删除");
    } catch {
      message.error("删除会话失败");
    }
  };

  const handleSelectSession = useCallback(
    (session: ChatHistoryItem) => {
      const threadId = session.thread_id ?? session.conversation_id ?? "";
      if (!threadId) {
        return;
      }
      setCurrentSession(session);
      loadConversation(threadId);
    },
    [loadConversation],
  );

  const handleModelChange = useCallback(
    (modelConfigId: string) => {
      const picked = availableModels.find(
        (model) => String(model.model_config_id) === modelConfigId,
      );
      setSelectedModelConfigId(modelConfigId);
      setSelectedModelName(picked?.model_name ?? "");
    },
    [availableModels],
  );

  return (
    <div
      style={{
        display: "flex",
        height: "calc(100vh - 80px)",
        background: "#fff",
        border: "1px solid #f0f0f0",
        borderRadius: 8,
        overflow: "hidden",
      }}
    >
      <AgentSidebar
        collapsed={sidebarCollapsed}
        currentSession={currentSession}
        isGuestMode={isGuestMode}
        sessions={sessions}
        onDeleteSession={handleDeleteSession}
        onNewSession={handleNewSession}
        onSelectSession={handleSelectSession}
      />

      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <AgentChatHeader
          sidebarCollapsed={sidebarCollapsed}
          onToggleSidebar={() => setSidebarCollapsed((prev) => !prev)}
        />
        <AgentMessageList
          historyLoading={historyLoading}
          messages={messages}
          messagesEndRef={messagesEndRef}
        />
        <AgentComposer
          availableModels={availableModels}
          inputValue={inputValue}
          isGuestMode={isGuestMode}
          selectedModelConfigId={selectedModelConfigId}
          selectedModelName={selectedModelName}
          sseLoading={sseLoading}
          onAbort={handleAbort}
          onInputChange={setInputValue}
          onModelChange={handleModelChange}
          onSend={handleSend}
        />
      </div>
    </div>
  );
};

export default AgentPage;
