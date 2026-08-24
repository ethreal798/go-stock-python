import React from "react";
import { Card, Descriptions, Space, Tag, Typography, Divider } from "antd";
import {
  GithubOutlined,
  HeartOutlined,
  RobotOutlined,
  NotificationOutlined,
  FundOutlined,
  StarOutlined,
  SettingOutlined,
  DashboardOutlined,
  StockOutlined,
  ClockCircleOutlined,
  BellOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  RocketOutlined,
} from "@ant-design/icons";

const { Title, Paragraph, Text, Link } = Typography;

const launchedFeatures = [
  { icon: <RobotOutlined />, label: "AI 智能对话（SSE 流式）" },
  {
    icon: <RobotOutlined />,
    label: "多模型支持（OpenAI / DeepSeek / 阿里百炼）",
  },
  // { icon: <SearchOutlined />, label: "RAG 检索增强" },
  // { icon: <NotificationOutlined />, label: "新闻资讯" },
  { icon: <NotificationOutlined />, label: "7×24 快讯" },
  { icon: <FundOutlined />, label: "基金市场" },
  { icon: <FundOutlined />, label: "基金搜索与详情" },
  { icon: <StarOutlined />, label: "我的关注" },
  { icon: <SettingOutlined />, label: "AI 模型配置" },
];

const developingFeatures = [
  { icon: <DashboardOutlined />, label: "自选股行情" },
  { icon: <StockOutlined />, label: "行情中心与 K 线图" },
  { icon: <ClockCircleOutlined />, label: "定时任务" },
  { icon: <BellOutlined />, label: "消息推送（钉钉/邮件）" },
  { icon: <DatabaseOutlined />, label: "数据源配置" },
];

const About: React.FC = () => {
  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        <Card>
          <div style={{ textAlign: "center", padding: "24px 0" }}>
            <img
              src="/stock.svg"
              alt="StockMate"
              style={{ width: 64, height: 64, marginBottom: 12 }}
            />
            <Title level={2} style={{ margin: 0 }}>
              StockMate
            </Title>
            <Paragraph type="secondary" style={{ marginTop: 8 }}>
              AI 驱动的基金分析与智能投资助手平台
            </Paragraph>
            <Space>
              <Tag color="blue">v1.0.0</Tag>
              <Tag color="green">Web 版</Tag>
            </Space>
          </div>

          <Divider />

          <Descriptions column={1} labelStyle={{ width: 120 }}>
            <Descriptions.Item label="已上线">
              <Space wrap size={[8, 8]}>
                {launchedFeatures.map(({ icon, label }) => (
                  <Tag key={label} color="green" icon={icon}>
                    {label}
                  </Tag>
                ))}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="开发中">
              <Space wrap size={[8, 8]}>
                {developingFeatures.map(({ icon, label }) => (
                  <Tag key={label} color="orange" icon={icon}>
                    {label}
                  </Tag>
                ))}
              </Space>
            </Descriptions.Item>
          </Descriptions>

          <Divider />

          <Descriptions column={1} labelStyle={{ width: 120 }}>
            <Descriptions.Item label="前端">
              <Space wrap>
                <Tag>React 18</Tag>
                <Tag>TypeScript</Tag>
                <Tag>Vite</Tag>
                <Tag>Ant Design 5</Tag>
                <Tag>ECharts</Tag>
                <Tag>Zustand</Tag>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="后端">
              <Space wrap>
                <Tag>Python 3.12</Tag>
                <Tag>FastAPI</Tag>
                <Tag>SQLAlchemy</Tag>
                <Tag>Redis</Tag>
                <Tag>LangGraph</Tag>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="数据来源">
              <Space wrap>
                <Tag>东方财富</Tag>
                <Tag>财联社</Tag>
                <Tag>华尔街见闻</Tag>
                <Tag>新浪财经</Tag>
              </Space>
            </Descriptions.Item>
          </Descriptions>

          <Divider />

          <Space style={{ width: "100%", justifyContent: "center" }}>
            <Link
              href="https://github.com/ethreal798/stockmate"
              target="_blank"
            >
              <GithubOutlined /> GitHub
            </Link>
            <Text type="secondary">·</Text>
            <Text type="secondary">
              <CheckCircleOutlined style={{ color: "#52c41a" }} />{" "}
              功能持续迭代中
            </Text>
            <Text type="secondary">·</Text>
            <Text type="secondary">
              <RocketOutlined style={{ color: "#1677ff" }} />{" "}
              <HeartOutlined style={{ color: "#f5222d" }} /> 感谢所有开源贡献者
            </Text>
          </Space>

          <Divider />

          <Paragraph
            type="secondary"
            style={{ textAlign: "center", fontSize: 13 }}
          >
            免责声明：本工具仅供学习研究使用，不构成投资建议。股市有风险，投资需谨慎。
          </Paragraph>
        </Card>
      </div>
    </div>
  );
};

export default About;
