import React, { useEffect } from "react";
import {
  Card,
  Form,
  Input,
  Button,
  Select,
  Switch,
  Slider,
  Tabs,
  message,
  Space,
  Divider,
  Typography,
  Tooltip,
} from "antd";
import { SaveOutlined, UndoOutlined } from "@ant-design/icons";
import { useSettingsStore } from "@/stores/settingsStore";
import { useAuthStore } from "@/stores/authStore";
import request from "@/api/index";

const { Text } = Typography;

const Settings: React.FC = () => {
  const isGuestMode = useAuthStore((state) => state.isGuestMode);
  const {
    settings,
    updateAI,
    updateNotify,
    updateDataSource,
    setLoading,
    loading,
    setSaved,
  } = useSettingsStore();
  const [aiForm] = Form.useForm();
  const [notifyForm] = Form.useForm();
  const [dsForm] = Form.useForm();

  useEffect(() => {
    aiForm.setFieldsValue(settings.ai);
    notifyForm.setFieldsValue(settings.notify);
    dsForm.setFieldsValue(settings.dataSource);
  }, [settings, aiForm, notifyForm, dsForm]);

  const handleSaveAI = async () => {
    try {
      const values = await aiForm.validateFields();
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

  const handleSaveNotify = async () => {
    try {
      const values = await notifyForm.validateFields();
      setLoading(true);
      await request.put("/settings/notify", values);
      updateNotify(values);
      message.success("通知配置保存成功");
      setSaved(true);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDS = async () => {
    try {
      const values = await dsForm.validateFields();
      setLoading(true);
      await request.put("/settings/datasource", values);
      updateDataSource(values);
      message.success("数据源配置保存成功");
      setSaved(true);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const tabItems = [
    {
      key: "ai",
      label: "AI 配置",
      children: (
        <Form form={aiForm} layout="vertical" style={{ maxWidth: 600 }}>
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
                  onClick={handleSaveAI}
                  loading={loading}
                  disabled={isGuestMode}
                >
                  保存配置
                </Button>
              </Tooltip>
              <Button
                icon={<UndoOutlined />}
                onClick={() => aiForm.setFieldsValue(settings.ai)}
                disabled={isGuestMode}
              >
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: "notify",
      label: "通知配置",
      children: (
        <Form form={notifyForm} layout="vertical" style={{ maxWidth: 600 }}>
          <Divider orientation="left">钉钉通知</Divider>
          <Form.Item
            label="启用钉钉通知"
            name="dingdingEnabled"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
          <Form.Item label="钉钉 Webhook Token" name="dingdingToken">
            <Input placeholder="请输入钉钉机器人 Token" />
          </Form.Item>
          <Form.Item label="钉钉加签密钥" name="dingdingSecret">
            <Input.Password placeholder="SEC..." />
          </Form.Item>
          <Divider orientation="left">邮件通知</Divider>
          <Form.Item
            label="启用邮件通知"
            name="emailEnabled"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
          <Form.Item label="SMTP 服务器" name="emailSmtp">
            <Input placeholder="smtp.example.com:587" />
          </Form.Item>
          <Form.Item label="发件人" name="emailFrom">
            <Input placeholder="noreply@example.com" />
          </Form.Item>
          <Form.Item label="收件人" name="emailTo">
            <Input placeholder="多个用逗号分隔" />
          </Form.Item>
          <Form.Item>
            <Tooltip title={isGuestMode ? "请登录后修改配置" : ""}>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSaveNotify}
                loading={loading}
                disabled={isGuestMode}
              >
                保存配置
              </Button>
            </Tooltip>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: "datasource",
      label: "数据源配置",
      children: (
        <Form form={dsForm} layout="vertical" style={{ maxWidth: 600 }}>
          <Form.Item
            label="Tushare Token"
            name="tushareToken"
            extra={
              <Text type="secondary">
                前往{" "}
                <a href="https://tushare.pro" target="_blank" rel="noreferrer">
                  tushare.pro
                </a>{" "}
                获取 Token
              </Text>
            }
          >
            <Input.Password placeholder="请输入 Tushare Token" />
          </Form.Item>
          <Form.Item
            label="启用问财数据"
            name="iwencaiEnabled"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
          <Form.Item>
            <Tooltip title={isGuestMode ? "请登录后修改配置" : ""}>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSaveDS}
                loading={loading}
                disabled={isGuestMode}
              >
                保存配置
              </Button>
            </Tooltip>
          </Form.Item>
        </Form>
      ),
    },
  ];

  return (
    <Card title="系统设置" bodyStyle={{ padding: "0 0 16px" }}>
      <Tabs items={tabItems} tabBarStyle={{ padding: "0 16px" }} />
    </Card>
  );
};

export default Settings;
