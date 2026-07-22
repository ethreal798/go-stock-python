import React, { useEffect } from "react";
import { Card, Form, Input, Button, Switch, message, Tooltip, Typography } from "antd";
import { SaveOutlined } from "@ant-design/icons";
import { useSettingsStore } from "@/stores/settingsStore";
import { useAuthStore } from "@/stores/authStore";
import request from "@/api/index";

const { Text } = Typography;

const DataSourceSettings: React.FC = () => {
  const isGuestMode = useAuthStore((state) => state.isGuestMode);
  const { settings, updateDataSource, setLoading, loading, setSaved } = useSettingsStore();
  const [form] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue(settings.dataSource);
  }, [form, settings.dataSource]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
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

  return (
    <Card title="数据源配置" bodyStyle={{ padding: 16 }}>
      <Form form={form} layout="vertical" style={{ maxWidth: 600 }}>
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
        <Form.Item label="启用问财数据" name="iwencaiEnabled" valuePropName="checked">
          <Switch />
        </Form.Item>
        <Form.Item>
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
        </Form.Item>
      </Form>
    </Card>
  );
};

export default DataSourceSettings;
