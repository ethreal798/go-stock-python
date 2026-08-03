import React from "react";
import { Avatar, Spin } from "antd";
import { RobotOutlined, UserOutlined } from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/types/agent";

interface AgentMessageListProps {
  historyLoading: boolean;
  messages: ChatMessage[];
  messagesEndRef: React.Ref<HTMLDivElement>;
}

const AgentMessageList: React.FC<AgentMessageListProps> = ({
  historyLoading,
  messages,
  messagesEndRef,
}) => {
  return (
    <div style={{ flex: 1, overflowY: "auto", padding: "12px 16px" }}>
      {historyLoading && (
        <div style={{ textAlign: "center", marginTop: 24 }}>
          <Spin />
        </div>
      )}
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
                {(msg.loading || msg.aborted || msg.error) && (
                  <div
                    style={{
                      marginTop: 8,
                      display: "flex",
                      justifyContent: "flex-end",
                    }}
                  >
                    <div
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                        color: msg.aborted
                          ? "#d46b08"
                          : msg.error
                            ? "#ff4d4f"
                            : "#999",
                        fontSize: 12,
                        fontWeight: msg.aborted ? 500 : 400,
                      }}
                    >
                      {msg.loading && <Spin size="small" />}
                      <span>
                        {msg.aborted
                          ? "[已中断！]"
                          : msg.error
                            ? "请求失败"
                            : "生成中..."}
                      </span>
                    </div>
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
  );
};

export default AgentMessageList;
