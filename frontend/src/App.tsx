import React, { useState } from "react";
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider, Layout, Menu, theme, Dropdown, Space, Avatar, Button, Typography } from "antd";
import type { MenuProps } from "antd";
import zhCN from "antd/locale/zh_CN";
import {
  DashboardOutlined,
  StockOutlined,
  RobotOutlined,
  NotificationOutlined,
  FundOutlined,
  ClockCircleOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  UserOutlined,
  LogoutOutlined,
  LoginOutlined,
} from "@ant-design/icons";
import { useNavigate, useLocation, Routes, Route } from "react-router-dom";
import AppRouter from "./router";
import Login from "@/pages/Login";
import { useAuthStore } from "@/stores/authStore";
import "dayjs/locale/zh-cn";
import dayjs from "dayjs";

dayjs.locale("zh-cn");

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

const menuItems: MenuProps["items"] = [
  { key: "/", icon: <DashboardOutlined />, label: "自选股" },
  { key: "/market", icon: <StockOutlined />, label: "行情中心" },
  { key: "/agent", icon: <RobotOutlined />, label: "AI 对话" },
  { key: "/news", icon: <NotificationOutlined />, label: "新闻资讯" },
  { 
    key: "/fund", 
    icon: <FundOutlined />, 
    label: "基金",
    children: [
      { key: "/fund", label: "我的关注" },
      { key: "/fund/market", label: "基金市场" }
    ]
  },
  { key: "/cron-tasks", icon: <ClockCircleOutlined />, label: "定时任务" },
  {
    key: "/settings",
    icon: <SettingOutlined />,
    label: "设置",
    children: [
      { key: "/settings", label: "AI 配置" },
      { key: "/settings/notify", label: "通知配置" },
      { key: "/settings/datasource", label: "数据源配置" },
    ],
  },
  { key: "/about", icon: <InfoCircleOutlined />, label: "关于" },
];

const findMenuLabel = (
  items: MenuProps["items"] | undefined,
  targetKey: string
): React.ReactNode | null => {
  if (!items) return null;

  for (const item of items) {
    if (!item) continue;

    if ("key" in item && item.key === targetKey) {
      return item.label;
    }

    if ("children" in item) {
      const childLabel = findMenuLabel(item.children, targetKey);
      if (childLabel) {
        return childLabel;
      }
    }
  }

  return null;
};

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token_type, isAuthenticated, logout } = useAuthStore();

  const userMenuItems: MenuProps["items"] = [
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "退出登录",
      onClick: () => {
        logout();
        navigate("/login");
      },
    },
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{ background: "#001529" }}
        width={200}
      >
        <div
          style={{
            height: 48,
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "flex-start",
            padding: collapsed ? 0 : "0 16px",
            color: "#fff",
            fontSize: collapsed ? 20 : 16,
            fontWeight: 700,
            overflow: "hidden",
            whiteSpace: "nowrap",
            transition: "all 0.2s",
            borderBottom: "1px solid rgba(255,255,255,0.1)",
            marginBottom: 4,
          }}
        >
          {collapsed ? "📈" : "📈 Go-Stock"}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          mode="inline"
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: "0 24px",
            background: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            boxShadow: "0 1px 4px rgba(0,21,41,.08)",
            height: 48,
            lineHeight: "48px",
          }}
        >
          <span style={{ fontSize: 16, fontWeight: 600, color: "#1d2129" }}>
            {findMenuLabel(menuItems, location.pathname) ?? "Go-Stock 股票分析平台"}
          </span>

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {isAuthenticated && token_type ? (  
              <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                <Space style={{ cursor: "pointer", padding: "0 8px" }}>
                  <Avatar
                    size="small"
                    icon={<UserOutlined />}
                    style={{ backgroundColor: "#1677ff" }}
                  />
                  <Text
                    strong
                    style={{ maxWidth: 100 }}
                    ellipsis={{ tooltip: token_type }}
                  >
                    {token_type}
                  </Text>
                </Space>
              </Dropdown>
            ) : (
              <Button
                type="primary"
                icon={<LoginOutlined />}
                onClick={() => navigate("/login")}
              >
                登录
              </Button>
            )}
          </div>
        </Header>
        <Content
          style={{
            margin: 0,
            padding: 16,
            minHeight: "calc(100vh - 48px)",
            background: "#f0f2f5",
            overflowY: "auto",
          }}
        >
          <AppRouter />
        </Content>
      </Layout>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: "#1677ff",
          borderRadius: 6,
        },
        algorithm: theme.defaultAlgorithm,
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<AppLayout />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
