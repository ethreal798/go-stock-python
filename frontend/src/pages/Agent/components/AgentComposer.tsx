import React from "react";
import { Button, Dropdown, Input, Space } from "antd";
import { DownOutlined, SendOutlined, StopOutlined } from "@ant-design/icons";
import type { ChatAvailableModel } from "@/types/agent";

const { TextArea } = Input;

interface AgentComposerProps {
  availableModels: ChatAvailableModel[];
  inputValue: string;
  isGuestMode: boolean;
  selectedModelConfigId: string | null;
  selectedModelName: string;
  sseLoading: boolean;
  onAbort: () => void;
  onInputChange: (value: string) => void;
  onModelChange: (modelConfigId: string) => void;
  onSend: () => void;
}

const AgentComposer: React.FC<AgentComposerProps> = ({
  availableModels,
  inputValue,
  isGuestMode,
  selectedModelConfigId,
  selectedModelName,
  sseLoading,
  onAbort,
  onInputChange,
  onModelChange,
  onSend,
}) => {
  return (
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
          onChange={(e) => onInputChange(e.target.value)}
          placeholder={
            isGuestMode ? "请登录后参与对话..." : "输入消息，Ctrl+Enter 发送..."
          }
          autoSize={{ minRows: 5, maxRows: 8 }}
          onKeyDown={(e) => {
            if (e.ctrlKey && e.key === "Enter" && !isGuestMode) {
              e.preventDefault();
              onSend();
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
              selectedKeys: selectedModelConfigId ? [selectedModelConfigId] : [],
              items: availableModels.map((model) => ({
                key: String(model.model_config_id),
                label: model.model_name,
              })),
              onClick: ({ key }) => onModelChange(String(key)),
            }}
          >
            <Button type="text" disabled={availableModels.length === 0}>
              <Space size={4}>
                <span>
                  {availableModels.length === 0 ? "暂无模型" : selectedModelName}
                </span>
                <DownOutlined />
              </Space>
            </Button>
          </Dropdown>
          {sseLoading ? (
            <Button icon={<StopOutlined />} onClick={onAbort} danger>
              停止
            </Button>
          ) : (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={onSend}
              disabled={!inputValue.trim() || isGuestMode}
            >
              发送
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentComposer;
