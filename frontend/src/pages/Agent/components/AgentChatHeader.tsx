import React from "react";
import { Button, Tooltip } from "antd";
import { MenuFoldOutlined, MenuUnfoldOutlined } from "@ant-design/icons";

interface AgentChatHeaderProps {
  sidebarCollapsed: boolean;
  onToggleSidebar: () => void;
}

const AgentChatHeader: React.FC<AgentChatHeaderProps> = ({
  sidebarCollapsed,
  onToggleSidebar,
}) => {
  return (
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
          onClick={onToggleSidebar}
        />
      </Tooltip>
    </div>
  );
};

export default AgentChatHeader;
