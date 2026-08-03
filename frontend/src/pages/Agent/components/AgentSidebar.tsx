import React from "react";
import { Button, List, Space, Tooltip, Typography } from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import type { ChatHistoryItem } from "@/types/agent";
import agentLogo from "@/assets/agent.svg";

const { Text } = Typography;

interface AgentSidebarProps {
  collapsed: boolean;
  currentSession: ChatHistoryItem | null;
  isGuestMode: boolean;
  sessions: ChatHistoryItem[];
  onDeleteSession: (threadId: string) => void;
  onNewSession: () => void;
  onSelectSession: (session: ChatHistoryItem) => void;
}

const AgentSidebar: React.FC<AgentSidebarProps> = ({
  collapsed,
  currentSession,
  isGuestMode,
  sessions,
  onDeleteSession,
  onNewSession,
  onSelectSession,
}) => {
  const currentThreadId =
    currentSession?.thread_id ?? currentSession?.conversation_id ?? null;

  return (
    <div
      style={{
        width: collapsed ? 0 : 260,
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        background: "#fefefeff",
        borderRight: collapsed ? "none" : "1px solid #f0f0f0",
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
            onClick={onNewSession}
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
          renderItem={(session) => {
            const sessionThreadId =
              session.thread_id ?? session.conversation_id ?? "";
            const selected =
              !!sessionThreadId && currentThreadId === sessionThreadId;

            return (
              <List.Item
                onClick={() => {
                  if (!sessionThreadId) {
                    return;
                  }
                  onSelectSession(session);
                }}
                style={{
                  cursor: "pointer",
                  margin: "0 8px 6px",
                  padding: "10px 12px",
                  background: selected ? "#e6f4ff" : "#fff",
                  borderRadius: 8,
                  border: selected
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
                        if (!sessionThreadId) {
                          return;
                        }
                        onDeleteSession(sessionThreadId);
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
            );
          }}
        />
      </div>
    </div>
  );
};

export default AgentSidebar;
