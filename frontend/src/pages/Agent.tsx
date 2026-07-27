import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Input,
  Button,
  List,
  Avatar,
  Space,
  Tooltip,
  Typography,
  Spin,
  message,
  Dropdown,
} from "antd";
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  PlusOutlined,
  StopOutlined,
  DeleteOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DownOutlined,
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useSSE } from "@/hooks/useSSE";
import { useAuthStore } from "@/stores/authStore";
import {
  buildStreamChatPayload,
  getStreamChatUrl,
  getSessionList,
  deleteSession,
  getAvailableChatModels,
} from "@/api/agent";
import type {
  ChatAvailableModel,
  ChatMessage,
  ChatSession,
  ChatStreamRequest,
} from "@/types/agent";
import agentLogo from "@/assets/agent.svg";

const { TextArea } = Input;
const { Text } = Typography;

const Agent: React.FC = () => {
  const isGuestMode = useAuthStore((state) => state.isGuestMode);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(
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
  const [selectedModelName, setSelectedModelName] = useState<string>("");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchSessions = useCallback(() => {
    return getSessionList()
      .then((res) => {
        const list = (res.data as { data?: ChatSession[] })?.data ?? [];
        setSessions(list);
        return list;
      })
      .catch(() => [] as ChatSession[]);
  }, []);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const {
    loading: sseLoading,
    connect: sseConnect,
    abort: sseAbort,
  } = useSSE({
    onMessage: ({ event, data }) => {
      if (event === "metadata") {
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
          if (last && last.role === "assistant") {
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + delta },
            ];
          }
          return prev;
        });
      } catch {
        if (event !== "delta") {
          return;
        }
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === "assistant") {
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + data },
            ];
          }
          return prev;
        });
      }
    },
    onDone: () => {
      setMessages((prev) =>
        prev.map((m) => (m.loading ? { ...m, loading: false } : m)),
      );
      fetchSessions().then((list) => {
        if (!currentSession && list.length > 0) {
          setCurrentSession(list[0]);
        }
      });
      scrollToBottom();
    },
    onError: () => {
      setMessages((prev) =>
        prev.map((m) =>
          m.loading
            ? { ...m, loading: false, error: true, content: "请求失败，请重试" }
            : m,
        ),
      );
    },
  });

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

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
    if (!content || sseLoading) return;
    if (!selectedModelConfigId) {
      message.warning("请先选择可用模型");
      return;
    }
    setInputValue("");

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: Date.now(),
    };
    const assistantMsg: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      loading: true,
    };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    const conversationId =
      messages.some((msg) => msg.role === "user") && currentSession
        ? currentSession.id
        : null;

    const payload: ChatStreamRequest = buildStreamChatPayload({
      message: content,
      model_config_id: Number(selectedModelConfigId),
      conversation_id: conversationId,
      capability: "general",
    });

    sseConnect(getStreamChatUrl(), payload);
  };

  const handleNewSession = async () => {
    setCurrentSession(null);
    setMessages([]);
    setInputValue("");
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((session) => session.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
      message.success("会话已删除");
    } catch {
      // ignore
    }
  };

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
      {/* 会话列表 */}
      <div
        style={{
          width: sidebarCollapsed ? 0 : 260,
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
          background: "#fefefeff",
          borderRight: sidebarCollapsed ? "none" : "1px solid #f0f0f0",
          overflow: "hidden",
          transition: "width 0.2s ease",
        }}
      >
        <div
          style={{
            height: 56,
            padding: "0 12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Space size={10}>
            <img
              src={agentLogo}
              alt="StockMate"
              style={{ width: 20, height: 20, display: "block", flexShrink: 0 }}
            />
            <span style={{ fontSize: 16, fontWeight: 600 }}>StockMate</span>
          </Space>
          <Tooltip title={isGuestMode ? "请登录后使用新建会话" : "新建会话"}>
            <Button
              size="small"
              type="text"
              icon={<PlusOutlined />}
              onClick={handleNewSession}
              disabled={isGuestMode}
            />
          </Tooltip>
        </div>
        <div
          style={{
            padding: "12px 12px 8px",
            fontSize: 13,
            fontWeight: 600,
            color: "#666",
          }}
        >
          历史会话
        </div>
        <div style={{ flex: 1, overflowY: "auto" }}>
          <List
            size="small"
            dataSource={sessions}
            locale={{ emptyText: "暂无历史会话" }}
            renderItem={(session) => (
              <List.Item
                onClick={() => {
                  setCurrentSession(session);
                  setMessages(session.messages ?? []);
                }}
                style={{
                  cursor: "pointer",
                  margin: "0 8px 6px",
                  padding: "10px 12px",
                  background:
                    currentSession?.id === session.id ? "#e6f4ff" : "#fff",
                  borderRadius: 8,
                  border:
                    currentSession?.id === session.id
                      ? "1px solid #91caff"
                      : "1px solid transparent",
                }}
                actions={[
                  <Tooltip key="delete-tip" title="删除会话">
                    <Button
                      type="text"
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={(event) => {
                        event.stopPropagation();
                        handleDeleteSession(session.id);
                      }}
                      disabled={isGuestMode}
                    />
                  </Tooltip>,
                ]}
              >
                <Text ellipsis style={{ width: "100%", paddingRight: 8 }}>
                  {session.title || "新会话"}
                </Text>
              </List.Item>
            )}
          />
        </div>
      </div>

      {/* 聊天区 */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: 56,
            padding: "0 16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderBottom: "1px solid #f0f0f0",
          }}
        >
          <Tooltip title={sidebarCollapsed ? "展开侧边栏" : "收起侧边栏"}>
            <Button
              size="small"
              type="text"
              icon={
                sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />
              }
              onClick={() => setSidebarCollapsed((prev) => !prev)}
            />
          </Tooltip>
        </div>

        {/* 消息列表 */}
        <div style={{ flex: 1, overflowY: "auto", padding: "12px 16px" }}>
          {messages.length === 0 && (
            <div style={{ textAlign: "center", color: "#999", marginTop: 80 }}>
              <RobotOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <p>你好！我是AI股票分析助手，有什么可以帮您的？</p>
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: "flex",
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                marginBottom: 16,
              }}
            >
              {msg.role === "assistant" && (
                <Avatar
                  icon={<RobotOutlined />}
                  style={{
                    background: "#1677ff",
                    flexShrink: 0,
                    marginRight: 8,
                  }}
                />
              )}
              <div
                style={{
                  maxWidth: "72%",
                  background: msg.role === "user" ? "#1677ff" : "#f5f5f5",
                  color: msg.role === "user" ? "#fff" : "#000",
                  borderRadius: 8,
                  padding: "8px 12px",
                  wordBreak: "break-word",
                }}
              >
                {msg.role === "assistant" ? (
                  <div className="markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                    {msg.loading && (
                      <div
                        style={{
                          marginTop: 8,
                          display: "inline-flex",
                          alignItems: "center",
                          gap: 6,
                          color: "#999",
                          fontSize: 12,
                        }}
                      >
                        <Spin size="small" />
                        <span>生成中...</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <span>{msg.content}</span>
                )}
              </div>
              {msg.role === "user" && (
                <Avatar
                  icon={<UserOutlined />}
                  style={{
                    background: "#87d068",
                    flexShrink: 0,
                    marginLeft: 8,
                  }}
                />
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区 */}
        <div style={{ padding: "16px" }}>
          <div
            style={{
              border: "1px solid #d9d9d9",
              borderRadius: 12,
              padding: 12,
              background: "#fff",
            }}
          >
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={
                isGuestMode
                  ? "请登录后参与对话..."
                  : "输入消息，Ctrl+Enter 发送..."
              }
              autoSize={{ minRows: 5, maxRows: 8 }}
              onKeyDown={(e) => {
                if (e.ctrlKey && e.key === "Enter" && !isGuestMode) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              variant="borderless"
              style={{ padding: 0, resize: "none" }}
              disabled={isGuestMode}
            />
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                alignItems: "center",
                gap: 8,
              }}
            >
              <Dropdown
                trigger={["click"]}
                menu={{
                  selectable: true,
                  selectedKeys: selectedModelConfigId
                    ? [selectedModelConfigId]
                    : [],
                  items: availableModels.map((model) => ({
                    key: String(model.model_config_id),
                    label: model.model_name,
                  })),
                  onClick: ({ key }) => {
                    const picked = availableModels.find(
                      (m) => String(m.model_config_id) === String(key),
                    );
                    setSelectedModelConfigId(String(key));
                    setSelectedModelName(picked?.model_name ?? "");
                  },
                }}
              >
                <Button type="text" disabled={availableModels.length === 0}>
                  <Space size={4}>
                    <span>
                      {availableModels.length === 0
                        ? "暂无模型"
                        : selectedModelName}
                    </span>
                    <DownOutlined />
                  </Space>
                </Button>
              </Dropdown>
              {sseLoading ? (
                <Button icon={<StopOutlined />} onClick={sseAbort} danger>
                  停止
                </Button>
              ) : (
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isGuestMode}
                >
                  发送
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Agent;
