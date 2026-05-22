import React, { useState } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, theme } from 'antd'
import type { MenuProps } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import {
  DashboardOutlined,
  StockOutlined,
  RobotOutlined,
  NotificationOutlined,
  FundOutlined,
  ClockCircleOutlined,
  SettingOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import AppRouter from './router'
import 'dayjs/locale/zh-cn'
import dayjs from 'dayjs'

dayjs.locale('zh-cn')

const { Sider, Header, Content } = Layout

const menuItems: MenuProps['items'] = [
  { key: '/', icon: <DashboardOutlined />, label: '自选股' },
  { key: '/market', icon: <StockOutlined />, label: '行情中心' },
  { key: '/agent', icon: <RobotOutlined />, label: 'AI 对话' },
  { key: '/news', icon: <NotificationOutlined />, label: '新闻资讯' },
  { key: '/fund', icon: <FundOutlined />, label: '基金' },
  { key: '/cron-tasks', icon: <ClockCircleOutlined />, label: '定时任务' },
  { key: '/settings', icon: <SettingOutlined />, label: '设置' },
  { key: '/about', icon: <InfoCircleOutlined />, label: '关于' },
]

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{ background: '#001529' }}
        width={200}
      >
        <div
          style={{
            height: 48,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? 0 : '0 16px',
            color: '#fff',
            fontSize: collapsed ? 20 : 16,
            fontWeight: 700,
            overflow: 'hidden',
            whiteSpace: 'nowrap',
            transition: 'all 0.2s',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            marginBottom: 4,
          }}
        >
          {collapsed ? '📈' : '📈 Go-Stock'}
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
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,21,41,.08)',
            height: 48,
            lineHeight: '48px',
          }}
        >
          <span style={{ fontSize: 16, fontWeight: 600, color: '#1d2129' }}>
            {menuItems?.find((m) => m?.key === location.pathname)
              ? (menuItems.find((m) => m?.key === location.pathname) as { label: string })?.label
              : 'Go-Stock 股票分析平台'}
          </span>
        </Header>
        <Content
          style={{
            margin: 0,
            padding: 16,
            minHeight: 'calc(100vh - 48px)',
            background: '#f0f2f5',
            overflowY: 'auto',
          }}
        >
          <AppRouter />
        </Content>
      </Layout>
    </Layout>
  )
}

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
        algorithm: theme.defaultAlgorithm,
      }}
    >
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
