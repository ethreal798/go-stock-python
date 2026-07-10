import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Card,
  Input,
  Button,
  List,
  Avatar,
  Space,
  Tooltip,
  Typography,
  Spin,
  Divider,
  message,
} from "antd";
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  ClearOutlined,
  PlusOutlined,
  StopOutlined,
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useSSE } from "@/hooks/useSSE";
import { useAuthStore } from "@/stores/authStore";
import {
  getStreamChatUrl,
  getSessionList,
  createSession,
  clearSession,
} from "@/api/agent";
import type { ChatMessage, ChatSession } from "@/types";

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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const {
    loading: sseLoading,
    connect: sseConnect,
    abort: sseAbort,
  } = useSSE({
    onMessage: (data) => {
      try {
        const parsed = JSON.parse(data) as { content?: string; delta?: string };
        const delta = parsed.content ?? parsed.delta ?? data;
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === "assistant" && last.loading) {
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + delta, loading: false },
            ];
          }
          return prev;
        });
      } catch {
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
    getSessionList()
      .then((res) => {
        const list = (res.data as { data?: ChatSession[] })?.data ?? [];
        setSessions(list);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async () => {
    const content = inputValue.trim();
    if (!content || sseLoading) return;
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

    sseConnect(getStreamChatUrl(), {
      sessionId: currentSession?.id,
      message: content,
    });
  };

  const handleNewSession = async () => {
    try {
      const res = await createSession();
      const session = (res.data as { data?: ChatSession })?.data;
      if (session) {
        setSessions((prev) => [session, ...prev]);
        setCurrentSession(session);
        setMessages([]);
      }
    } catch {
      // ignore
    }
  };

  const handleClear = async () => {
    if (!currentSession) {
      setMessages([]);
      return;
    }
    try {
      await clearSession(currentSession.id);
      setMessages([]);
      message.success("会话已清空");
    } catch {
      // ignore
    }
  };

  return (
    <div style={{ display: "flex", height: "calc(100vh - 80px)", gap: 12 }}>
      {/* 会话列表 */}
      <Card
        size="small"
        title="会话列表"
        style={{ width: 220, flexShrink: 0, overflowY: "auto" }}
        extra={
          <Tooltip title={isGuestMode ? "请登录后使用新建会话" : "新建会话"}>
            <Button
              size="small"
              icon={<PlusOutlined />}
              onClick={handleNewSession}
              disabled={isGuestMode}
            />
          </Tooltip>
        }
        bodyStyle={{ padding: 0 }}
      >
        <List
          size="small"
          dataSource={sessions}
          renderItem={(session) => (
            <List.Item
              onClick={() => {
                setCurrentSession(session);
                setMessages(session.messages ?? []);
              }}
              style={{
                cursor: "pointer",
                padding: "8px 12px",
                background:
                  currentSession?.id === session.id ? "#e6f4ff" : undefined,
              }}
            >
              <Text ellipsis style={{ width: "100%" }}>
                {session.title || "新会话"}
              </Text>
            </List.Item>
          )}
        />
      </Card>

      {/* 聊天区 */}
      <Card
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
        bodyStyle={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          padding: 0,
          overflow: "hidden",
        }}
        title={
          <Space>
            <RobotOutlined style={{ color: "#1677ff" }} />
            <span>AI 智能助手</span>
          </Space>
        }
        extra={
          <Space>
            <Tooltip title={isGuestMode ? "请登录后使用清空功能" : "清空会话"}>
              <Button
                size="small"
                icon={<ClearOutlined />}
                onClick={handleClear}
                disabled={isGuestMode}
              />
            </Tooltip>
          </Space>
        }
      >
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
                {msg.loading ? (
                  <Spin size="small" />
                ) : msg.role === "assistant" ? (
                  <div className="markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
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

        <Divider style={{ margin: 0 }} />

        {/* 输入区 */}
        <div style={{ padding: "12px 16px", display: "flex", gap: 8 }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={isGuestMode ? "请登录后参与对话..." : "输入消息，Ctrl+Enter 发送..."}
            autoSize={{ minRows: 2, maxRows: 5 }}
            onKeyDown={(e) => {
              if (e.ctrlKey && e.key === "Enter" && !isGuestMode) {
                e.preventDefault();
                handleSend();
              }
            }}
            style={{ flex: 1 }}
            disabled={isGuestMode}
          />
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={sseLoading}
              disabled={!inputValue.trim() || isGuestMode}
            >
              发送
            </Button>
            {sseLoading && (
              <Button icon={<StopOutlined />} onClick={sseAbort} danger>
                停止
              </Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Agent;
