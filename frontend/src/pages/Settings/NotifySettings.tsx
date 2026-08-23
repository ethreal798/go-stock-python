import React from "react";
import DevelopingPlaceholder from "@/components/DevelopingPlaceholder";
// import { Card, Form, Input, Button, Switch, message, Divider, Tooltip } from "antd";
// import { SaveOutlined } from "@ant-design/icons";
// import { useSettingsStore } from "@/stores/settingsStore";
// import { useAuthStore } from "@/stores/authStore";
// import request from "@/api/index";

const NotifySettings: React.FC = () => {
  return <DevelopingPlaceholder />;
  // const isGuestMode = useAuthStore((state) => state.isGuestMode);
  // const { settings, updateNotify, setLoading, loading, setSaved } = useSettingsStore();
  // const [form] = Form.useForm();

  // useEffect(() => {
  //   form.setFieldsValue(settings.notify);
  // }, [form, settings.notify]);

  // const handleSave = async () => {
  //   try {
  //     const values = await form.validateFields();
  //     setLoading(true);
  //     await request.put("/settings/notify", values);
  //     updateNotify(values);
  //     message.success("通知配置保存成功");
  //     setSaved(true);
  //   } catch {
  //     // ignore
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  // return (
  //   <Card title="通知配置" bodyStyle={{ padding: 16 }}>
  //     <Form form={form} layout="vertical" style={{ maxWidth: 600 }}>
  //       <Divider orientation="left">钉钉通知</Divider>
  //       <Form.Item label="启用钉钉通知" name="dingdingEnabled" valuePropName="checked">
  //         <Switch />
  //       </Form.Item>
  //       <Form.Item label="钉钉 Webhook Token" name="dingdingToken">
  //         <Input placeholder="请输入钉钉机器人 Token" />
  //       </Form.Item>
  //       <Form.Item label="钉钉加签密钥" name="dingdingSecret">
  //         <Input.Password placeholder="SEC..." />
  //       </Form.Item>

  //       <Divider orientation="left">邮件通知</Divider>
  //       <Form.Item label="启用邮件通知" name="emailEnabled" valuePropName="checked">
  //         <Switch />
  //       </Form.Item>
  //       <Form.Item label="SMTP 服务器" name="emailSmtp">
  //         <Input placeholder="smtp.example.com:587" />
  //       </Form.Item>
  //       <Form.Item label="发件人" name="emailFrom">
  //         <Input placeholder="noreply@example.com" />
  //       </Form.Item>
  //       <Form.Item label="收件人" name="emailTo">
  //         <Input placeholder="多个用逗号分隔" />
  //       </Form.Item>
  //       <Form.Item>
  //         <Tooltip title={isGuestMode ? "请登录后修改配置" : ""}>
  //           <Button
  //             type="primary"
  //             icon={<SaveOutlined />}
  //             onClick={handleSave}
  //             loading={loading}
  //             disabled={isGuestMode}
  //           >
  //             保存配置
  //           </Button>
  //         </Tooltip>
  //       </Form.Item>
  //     </Form>
  //   </Card>
  // );
};

export default NotifySettings;
