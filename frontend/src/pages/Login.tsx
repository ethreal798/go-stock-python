import React, { useState } from "react";
import { Form, Input, Button, Col, Typography, message, Divider } from "antd";
import { UserOutlined, LockOutlined, MailOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { login, register } from "@/api/auth";

const { Title, Text } = Typography;

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const navigate = useNavigate();
  const loginStore = useAuthStore((state) => state.login);
  const [form] = Form.useForm();

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      if (isRegister) {
        // 注册逻辑
        const res = await register({
          email: values.email,
          username: values.username,
          password: values.password,
        });
        // TODO: 处理注册成功后的逻辑
        const { access_token, token_type } = res.data;
        loginStore(access_token, token_type);
        message.success("注册并登录成功");
      } else {
        // 登录逻辑
        const formData = new FormData();
        formData.append("username", values.email);
        formData.append("password", values.password);

        const res = await login(formData);
        const { access_token, token_type } = res.data;
        loginStore(access_token, token_type);
        message.success("登录成功");
      }
      navigate("/");
    } catch (error: any) {
      console.log(error);
      if (error.response?.status === 401) {
        message.error(error.response.data.detail || "邮箱或密码错误");
      } else {
        message.error(isRegister ? "注册失败" : "登录失败");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: "100vh", display: "flex", overflow: "hidden" }}>
      {/* 左侧 70% 宽度的大图片区域 */}
      <Col
        span={17}
        style={{
          background: "#001529",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#fff",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <Title style={{ color: "#fff", fontSize: "48px" }}>Go-Stock</Title>
          <Text style={{ color: "rgba(255,255,255,0.65)", fontSize: "18px" }}>
            专业的股票分析与量化交易平台
          </Text>
          {/* 这里留出图片位置，目前用渐变色代替背景 */}
          <div
            style={{
              marginTop: "40px",
              width: "80%",
              height: "400px",
              background: "linear-gradient(135deg, #1677ff 0%, #001529 100%)",
              borderRadius: "12px",
              boxShadow: "0 20px 50px rgba(0,0,0,0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "24px",
              fontStyle: "italic",
              opacity: 0.8,
            }}
          >
            大屏行情展示图占位
          </div>
        </div>
      </Col>

      {/* 右侧 30% 登录注册表单 */}
      <Col
        span={7}
        style={{
          background: "#fff",
          padding: "0 40px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
        }}
      >
        <div style={{ maxWidth: "400px", width: "100%", margin: "0 auto" }}>
          <div style={{ marginBottom: "40px", textAlign: "center" }}>
            <Title level={2}>{isRegister ? "创建账号" : "欢迎回来"}</Title>
            <Text type="secondary">
              {isRegister
                ? "请输入您的基本信息开始体验"
                : "请输入您的邮箱和密码进行登录"}
            </Text>
          </div>

          <Form
            form={form}
            name="auth_form"
            layout="vertical"
            onFinish={onFinish}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              label="邮箱"
              name="email"
              rules={[
                { required: true, message: "请输入您的邮箱" },
                { type: "email", message: "请输入有效的邮箱地址" },
              ]}
            >
              <Input prefix={<MailOutlined />} placeholder="example@mail.com" />
            </Form.Item>

            {isRegister && (
              <Form.Item
                label="用户名"
                name="username"
                rules={[{ required: true, message: "请输入用户名" }]}
              >
                <Input prefix={<UserOutlined />} placeholder="jie798" />
              </Form.Item>
            )}

            <Form.Item
              label="密码"
              name="password"
              rules={[{ required: true, message: "请输入密码" }]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="******" />
            </Form.Item>

            <Form.Item style={{ marginTop: "24px" }}>
              <Button
                type="primary"
                htmlType="submit"
                block
                loading={loading}
                style={{ height: "45px" }}
              >
                {isRegister ? "注册并登录" : "立即登录"}
              </Button>
            </Form.Item>
          </Form>

          <Divider plain>
            <Text type="secondary" style={{ fontSize: "12px" }}>
              其他操作
            </Text>
          </Divider>

          <div style={{ textAlign: "center" }}>
            <Button
              type="link"
              onClick={() => {
                setIsRegister(!isRegister);
                form.resetFields();
              }}
            >
              {isRegister ? "已有账号？立即登录" : "还没有账号？点击注册"}
            </Button>
          </div>
        </div>
      </Col>
    </div>
  );
};

export default Login;
