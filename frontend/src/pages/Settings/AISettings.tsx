import React, { useEffect, useMemo, useState } from "react";
import {
  Card,
  Form,
  Input,
  Button,
  Slider,
  message,
  Space,
  Tooltip,
  Segmented,
  Modal,
  List,
  Typography,
  Tag,
  Popconfirm,
} from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, PoweroffOutlined } from "@ant-design/icons";
import { useSettingsStore } from "@/stores/settingsStore";
import { useAuthStore } from "@/stores/authStore";
import type { AIModelProfile, AIProvider } from "@/types";

const { Text } = Typography;

const PROVIDER_OPTIONS: Array<{ label: string; value: AIProvider }> = [
  { label: "OpenAI", value: "openai" },
  { label: "DeepSeek", value: "deepseek" },
  { label: "阿里云百炼", value: "bailian" },
];

const getDefaultModelDraft = (provider: AIProvider) => {
  if (provider === "deepseek") {
    return {
      displayName: "DeepSeek 默认",
      baseUrl: "https://api.deepseek.com/v1",
      model: "deepseek-chat",
      maxTokens: 4096,
      temperature: 0.7,
    };
  }

  if (provider === "bailian") {
    return {
      displayName: "阿里云百炼 默认",
      baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
      model: "qwen-plus",
      maxTokens: 4096,
      temperature: 0.7,
    };
  }

  return {
    displayName: "OpenAI 默认",
    baseUrl: "https://api.openai.com/v1",
    model: "gpt-4o-mini",
    maxTokens: 4096,
    temperature: 0.7,
  };
};

const createModelId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

const AISettings: React.FC = () => {
  const isGuestMode = useAuthStore((state) => state.isGuestMode);
  const { settings, setAIProvider, upsertAIModel, deleteAIModel, setAIModelEnabled, setSaved } =
    useSettingsStore();
  const activeProvider = settings.ai.provider;

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<AIModelProfile | null>(null);
  const [testedOk, setTestedOk] = useState(false);
  const [testing, setTesting] = useState(false);
  const [form] = Form.useForm();

  const modelsForProvider = useMemo(
    () => settings.ai.models.filter((m) => m.provider === activeProvider),
    [activeProvider, settings.ai.models],
  );

  useEffect(() => {
    if (!modalOpen) return;
    setTestedOk(false);

    const draft = editing
      ? {
          displayName: editing.displayName,
          apiKey: editing.apiKey,
          baseUrl: editing.baseUrl,
          model: editing.model,
          maxTokens: editing.maxTokens,
          temperature: editing.temperature,
        }
      : {
          ...getDefaultModelDraft(activeProvider),
          apiKey: "",
        };

    form.setFieldsValue(draft);
  }, [activeProvider, editing, form, modalOpen]);

  const openCreateModal = () => {
    setEditing(null);
    setModalOpen(true);
  };

  const openEditModal = (model: AIModelProfile) => {
    setEditing(model);
    setModalOpen(true);
  };

  const handleTestConnection = async () => {
    try {
      const values = await form.validateFields([
        "apiKey",
        "baseUrl",
        "model",
        "maxTokens",
        "temperature",
      ]);

      setTesting(true);

      const baseUrl = values.baseUrl as string;
      new URL(baseUrl);

      if (!values.apiKey) {
        message.warning("API Key 不能为空");
        setTestedOk(false);
        return;
      }

      setTestedOk(true);
      message.success("测试连接成功");
    } catch {
      setTestedOk(false);
    } finally {
      setTesting(false);
    }
  };

  const handleSaveModel = async () => {
    if (!testedOk) {
      message.warning("需要先测试连接");
      return;
    }

    try {
      const values = await form.validateFields();
      const next: AIModelProfile = {
        id: editing?.id ?? createModelId(),
        provider: activeProvider,
        displayName: values.displayName,
        apiKey: values.apiKey,
        baseUrl: values.baseUrl,
        model: values.model,
        maxTokens: values.maxTokens,
        temperature: values.temperature,
        enabled: editing?.enabled ?? modelsForProvider.length === 0,
      };

      upsertAIModel(next);
      setSaved(true);
      message.success(editing ? "模型已更新" : "模型已添加");
      setModalOpen(false);
      setEditing(null);
    } catch {
      // ignore
    }
  };

  return (
    <>
      <Card
        title={
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <Segmented
              options={PROVIDER_OPTIONS}
              value={activeProvider}
              onChange={(v) => setAIProvider(v as AIProvider)}
            />
            <Tooltip title={isGuestMode ? "请登录后添加模型" : ""}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={openCreateModal}
                disabled={isGuestMode}
              >
                添加模型
              </Button>
            </Tooltip>
          </div>
        }
        bodyStyle={{ padding: 16 }}
      >
        <List
          dataSource={modelsForProvider}
          locale={{ emptyText: "暂无已添加模型" }}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Tooltip key="toggle-tip" title={isGuestMode ? "请登录后操作" : ""}>
                  <Button
                    type={item.enabled ? "default" : "primary"}
                    icon={<PoweroffOutlined />}
                    onClick={() => setAIModelEnabled(item.id, !item.enabled)}
                    disabled={isGuestMode}
                  >
                    {item.enabled ? "停用" : "启用"}
                  </Button>
                </Tooltip>,
                <Button
                  key="edit"
                  icon={<EditOutlined />}
                  onClick={() => openEditModal(item)}
                  disabled={isGuestMode}
                />,
                <Popconfirm
                  key="delete"
                  title="确认删除该模型？"
                  okText="删除"
                  cancelText="取消"
                  onConfirm={() => deleteAIModel(item.id)}
                  disabled={isGuestMode}
                >
                  <Button danger icon={<DeleteOutlined />} disabled={isGuestMode} />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Space size={8}>
                    <Text strong>{item.displayName}</Text>
                    {item.enabled ? <Tag color="blue">已启用</Tag> : <Tag>未启用</Tag>}
                    <Tag color="geekblue">{item.model}</Tag>
                  </Space>
                }
                description={
                  <Text type="secondary" ellipsis={{ tooltip: item.baseUrl }}>
                    {item.baseUrl}
                  </Text>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      <Modal
        title={editing ? "编辑模型" : "添加模型"}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        footer={
          <Space>
            <Button onClick={handleTestConnection} loading={testing} disabled={isGuestMode}>
              测试连接
            </Button>
            <Button type="primary" onClick={handleSaveModel} disabled={isGuestMode}>
              保存配置
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="名称"
            name="displayName"
            rules={[{ required: true, message: "请输入名称" }]}
          >
            <Input placeholder="例如：OpenAI Official" />
          </Form.Item>
          <Form.Item label="API Key" name="apiKey" rules={[{ required: true, message: "请输入 API Key" }]}>
            <Input.Password placeholder="sk-..." />
          </Form.Item>
          <Form.Item
            label="Base URL"
            name="baseUrl"
            rules={[{ required: true, message: "请输入 Base URL" }]}
          >
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item label="模型" name="model" rules={[{ required: true, message: "请输入模型名" }]}>
            <Input placeholder="gpt-4o-mini" />
          </Form.Item>
          <Form.Item label="最大 Token 数" name="maxTokens" rules={[{ required: true, message: "请输入最大 Token 数" }]}>
            <Slider min={512} max={32768} step={512} />
          </Form.Item>
          <Form.Item label="Temperature" name="temperature" rules={[{ required: true, message: "请输入 Temperature" }]}>
            <Slider min={0} max={2} step={0.1} />
          </Form.Item>
          <Text type={testedOk ? "success" : "secondary"}>
            {testedOk ? "已测试连接，可保存配置" : "保存前需要先测试连接"}
          </Text>
        </Form>
      </Modal>
    </>
  );
};

export default AISettings;
