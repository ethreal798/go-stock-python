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
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PoweroffOutlined,
  LinkOutlined,
} from "@ant-design/icons";
import {
  createAIModelConfig,
  deleteAIModelConfig,
  getAIModelConfigDetail,
  getAIModelConfigs,
  testAIModelConfig,
  testAIModelConfigDraft,
  updateAIModelConfig,
} from "@/api/settings";
import { useAuthStore } from "@/stores/authStore";
import type {
  AIModelConfigCreateRequest,
  AIModelConfigResponse,
  AIProvider,
} from "@/types";
import openAIIcon from "@/assets/open-a-i.png";
import deepSeekIcon from "@/assets/deepseek.png";
import bailianIcon from "@/assets/alibailian.png";

const { Text } = Typography;

const providerMeta: Record<AIProvider, { label: string; icon: string }> = {
  openai: { label: "OpenAI", icon: openAIIcon },
  deepseek: { label: "DeepSeek", icon: deepSeekIcon },
  bailian: { label: "阿里云百炼", icon: bailianIcon },
};

const PROVIDER_OPTIONS: Array<{ label: React.ReactNode; value: AIProvider }> = [
  {
    label: (
      <Space size={6}>
        <img
          src={providerMeta.openai.icon}
          alt="OpenAI"
          style={{ width: 25, height: 25, position: "relative", top: 5 }}
        />
        <span>{providerMeta.openai.label}</span>
      </Space>
    ),
    value: "openai",
  },
  {
    label: (
      <Space size={6}>
        <img
          src={providerMeta.deepseek.icon}
          alt="DeepSeek"
          style={{ width: 24, height: 24, position: "relative", top: 5 }}
        />
        <span>{providerMeta.deepseek.label}</span>
      </Space>
    ),
    value: "deepseek",
  },
  {
    label: (
      <Space size={6}>
        <img
          src={providerMeta.bailian.icon}
          alt="阿里云百炼"
          style={{ width: 22, height: 22, position: "relative", top: 5 }}
        />
        <span>{providerMeta.bailian.label}</span>
      </Space>
    ),
    value: "bailian",
  },
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

interface AIModelFormValues {
  displayName: string;
  apiKey: string;
  baseUrl: string;
  model: string;
  maxTokens: number;
  temperature: number;
}

const providerCodeMap: Record<AIProvider, string> = {
  openai: "openai_compatible",
  deepseek: "deepseek",
  bailian: "通义千问",
};

const providerTextToTab = (provider: string): AIProvider => {
  const normalized = provider.trim().toLowerCase();
  if (normalized.includes("deepseek")) {
    return "deepseek";
  }
  if (
    normalized.includes("通义千问") ||
    normalized.includes("百炼") ||
    normalized.includes("bailian") ||
    normalized.includes("qwen")
  ) {
    return "bailian";
  }
  return "openai";
};

const mapResponseToFormValues = (
  model: AIModelConfigResponse,
): AIModelFormValues => ({
  displayName: model.name,
  apiKey: "",
  baseUrl: model.base_url.replace(/`/g, "").trim(),
  model: model.model,
  maxTokens: model.max_output_tokens,
  temperature: model.temperature,
});

const AISettings: React.FC = () => {
  const isGuestMode = useAuthStore((state) => state.isGuestMode);
  const [activeProvider, setActiveProvider] = useState<AIProvider>("openai");
  const [models, setModels] = useState<AIModelConfigResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<AIModelConfigResponse | null>(null);
  const [testedOk, setTestedOk] = useState(false);
  const [testing, setTesting] = useState(false);
  const [form] = Form.useForm();

  const modelsForProvider = useMemo(
    () =>
      models.filter((m) => providerTextToTab(m.provider) === activeProvider),
    [activeProvider, models],
  );

  const fetchModels = async () => {
    setListLoading(true);
    try {
      const res = await getAIModelConfigs();
      const data = res.data || [];
      setModels(data);
    } catch {
      // ignore
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  useEffect(() => {
    if (!modalOpen) return;
    setTestedOk(false);

    const draft = editing
      ? mapResponseToFormValues(editing)
      : {
          ...getDefaultModelDraft(activeProvider),
          apiKey: "",
        };

    form.setFieldsValue(draft);
  }, [activeProvider, editing, form, modalOpen]);

  const openCreateModal = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEditModal = async (model: AIModelConfigResponse) => {
    try {
      setLoading(true);
      const res = await getAIModelConfigDetail(model.id);
      const detailList = res.data || [];
      const target =
        detailList.find((item) => item.id === model.id) ??
        detailList[0] ??
        model;
      setEditing(target);
      setModalOpen(true);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      const values = (await form.validateFields([
        "displayName",
        "apiKey",
        "baseUrl",
        "model",
        "maxTokens",
        "temperature",
      ])) as AIModelFormValues;

      setTesting(true);
      const payload: AIModelConfigCreateRequest & { message?: string } = {
        name: values.displayName,
        provider: providerCodeMap[activeProvider],
        base_url: values.baseUrl,
        model: values.model,
        max_output_tokens: values.maxTokens,
        temperature: values.temperature,
        timeout_seconds: 60,
        enabled: editing?.enabled ?? modelsForProvider.length === 0,
        extra_config: {},
        api_key: values.apiKey,
        message: "ping",
      };

      const res = editing
        ? await testAIModelConfig(editing.id)
        : await testAIModelConfigDraft(payload);

      const result = res.data;
      setTestedOk(result.success);
      if (result.success) {
        message.success(result.message || "测试连接成功");
      } else {
        message.error(result.message || "测试连接失败");
      }
    } catch {
      setTestedOk(false);
    } finally {
      setTesting(false);
    }
  };

  const handleQuickTest = async (model: AIModelConfigResponse) => {
    try {
      setTesting(true);
      const res = await testAIModelConfig(model.id);
      const result = res.data;
      if (result.success) {
        message.success(result.message || `${model.name} 测试连接成功`);
      } else {
        message.error(result.message || `${model.name} 测试连接失败`);
      }
    } catch {
      // ignore
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
      setLoading(true);
      const values = (await form.validateFields()) as AIModelFormValues;
      const payload: AIModelConfigCreateRequest = {
        name: values.displayName,
        provider: providerCodeMap[activeProvider],
        base_url: values.baseUrl,
        model: values.model,
        max_output_tokens: values.maxTokens,
        temperature: values.temperature,
        timeout_seconds: 60,
        enabled: editing?.enabled ?? modelsForProvider.length === 0,
        extra_config: {},
        api_key: values.apiKey,
      };

      if (editing) {
        await updateAIModelConfig(editing.id, payload);
      } else {
        await createAIModelConfig(payload);
      }

      await fetchModels();
      message.success(editing ? "模型已更新" : "模型已添加");
      setModalOpen(false);
      setEditing(null);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Card
        title={
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <Segmented
              options={PROVIDER_OPTIONS}
              value={activeProvider}
              onChange={(v) => setActiveProvider(v as AIProvider)}
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
          loading={listLoading}
          dataSource={modelsForProvider}
          locale={{ emptyText: "暂无已添加模型" }}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Tooltip
                  key="toggle-tip"
                  title={isGuestMode ? "请登录后操作" : ""}
                >
                  <Button
                    type={item.enabled ? "default" : "primary"}
                    icon={<PoweroffOutlined />}
                    onClick={async () => {
                      try {
                        setLoading(true);
                        await updateAIModelConfig(item.id, {
                          enabled: !item.enabled,
                        });
                        await fetchModels();
                        message.success(!item.enabled ? "已启用" : "已停用");
                      } catch {
                        // ignore
                      } finally {
                        setLoading(false);
                      }
                    }}
                    disabled={isGuestMode}
                    loading={loading}
                  >
                    {item.enabled ? "停用" : "启用"}
                  </Button>
                </Tooltip>,
                <Button
                  key="test"
                  icon={<LinkOutlined />}
                  onClick={() => handleQuickTest(item)}
                  disabled={isGuestMode}
                  loading={testing}
                />,
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
                  onConfirm={async () => {
                    try {
                      setLoading(true);
                      await deleteAIModelConfig(item.id);
                      await fetchModels();
                      message.success("模型已删除");
                    } catch {
                      // ignore
                    } finally {
                      setLoading(false);
                    }
                  }}
                  disabled={isGuestMode}
                >
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    disabled={isGuestMode}
                  />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Space size={8}>
                    <Text strong>{item.name}</Text>
                    {item.enabled ? (
                      <Tag color="blue">已启用</Tag>
                    ) : (
                      <Tag>未启用</Tag>
                    )}
                    <Tag color="geekblue">{item.model}</Tag>
                  </Space>
                }
                description={
                  <Text type="secondary" ellipsis={{ tooltip: item.base_url }}>
                    {item.base_url.replace(/`/g, "").trim()}
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
            <Button
              onClick={handleTestConnection}
              loading={testing}
              disabled={isGuestMode || loading}
            >
              测试连接
            </Button>
            <Button
              type="primary"
              onClick={handleSaveModel}
              disabled={isGuestMode || loading}
              loading={loading}
            >
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
          <Form.Item
            label="API Key"
            name="apiKey"
            rules={[{ required: true, message: "请输入 API Key" }]}
          >
            <Input.Password placeholder="sk-..." />
          </Form.Item>
          <Form.Item
            label="Base URL"
            name="baseUrl"
            rules={[{ required: true, message: "请输入 Base URL" }]}
          >
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item
            label="模型"
            name="model"
            rules={[{ required: true, message: "请输入模型名" }]}
          >
            <Input placeholder="gpt-4o-mini" />
          </Form.Item>
          <Form.Item
            label="最大 Token 数"
            name="maxTokens"
            rules={[{ required: true, message: "请输入最大 Token 数" }]}
          >
            <Slider min={512} max={32768} step={512} />
          </Form.Item>
          <Form.Item
            label="Temperature"
            name="temperature"
            rules={[{ required: true, message: "请输入 Temperature" }]}
          >
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
