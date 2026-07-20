import React, { useEffect } from "react";
import { Card, Form, Input, Button, Select, Slider, message, Space, Tooltip } from "antd";
import { SaveOutlined, UndoOutlined } from "@ant-design/icons";
import { useSettingsStore } from "@/stores/settingsStore";
import { useAuthStore } from "@/stores/authStore";
import request from "@/api/index";

const AISettings: React.FC = () => {
  const isGuestMode = useAuthStore((state) => state.isGuestMode);
  const { settings, updateAI, setLoading, loading, setSaved } = useSettingsStore();
  const [form] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue(settings.ai);
  }, [form, settings.ai]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await request.put("/settings", values);
      updateAI(values);
      message.success("AI 配置保存成功");
      setSaved(true);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="AI 配置" bodyStyle={{ padding: 16 }}>
      <Form form={form} layout="vertical" style={{ maxWidth: 600 }}>
        <Form.Item label="AI 提供商" name="provider">
          <Select
            options={[
              { label: "OpenAI", value: "openai" },
              { label: "Ollama (本地)", value: "ollama" },
              { label: "智谱 ChatGLM", value: "zhipu" },
              { label: "通义千问", value: "qwen" },
              { label: "DeepSeek", value: "deepseek" },
              { label: "文心一言", value: "wenxin" },
            ]}
          />
        </Form.Item>
        <Form.Item label="API Key" name="apiKey">
          <Input.Password placeholder="sk-..." />
        </Form.Item>
        <Form.Item label="Base URL" name="baseUrl">
          <Input placeholder="https://api.openai.com/v1" />
        </Form.Item>
        <Form.Item label="模型" name="model">
          <Input placeholder="gpt-4o-mini" />
        </Form.Item>
        <Form.Item label="最大 Token 数" name="maxTokens">
          <Slider min={512} max={32768} step={512} />
        </Form.Item>
        <Form.Item label="Temperature" name="temperature">
          <Slider min={0} max={2} step={0.1} />
        </Form.Item>
        <Form.Item>
          <Space>
            <Tooltip title={isGuestMode ? "请登录后修改配置" : ""}>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={loading}
                disabled={isGuestMode}
              >
                保存配置
              </Button>
            </Tooltip>
            <Button
              icon={<UndoOutlined />}
              onClick={() => form.setFieldsValue(settings.ai)}
              disabled={isGuestMode}
            >
              重置
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default AISettings;
