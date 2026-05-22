import React from 'react'
import { Card, Descriptions, Space, Tag, Typography, Divider } from 'antd'
import {
  GithubOutlined,
  HeartOutlined,
} from '@ant-design/icons'

const { Title, Paragraph, Text, Link } = Typography

const About: React.FC = () => {
  return (
    <div style={{ maxWidth: 700 }}>
      <Card>
        <div style={{ textAlign: 'center', padding: '24px 0' }}>
          <div style={{ fontSize: 64, marginBottom: 12 }}>📈</div>
          <Title level={2} style={{ margin: 0 }}>Go-Stock</Title>
          <Paragraph type="secondary" style={{ marginTop: 8 }}>
            股票分析与 AI 智能投资助手平台
          </Paragraph>
          <Space>
            <Tag color="blue">v2.0.0</Tag>
            <Tag color="green">Web 版</Tag>
          </Space>
        </div>

        <Divider />

        <Descriptions column={1} labelStyle={{ width: 120 }}>
          <Descriptions.Item label="版本">2.0.0 (Python + React)</Descriptions.Item>
          <Descriptions.Item label="框架">FastAPI + React 18 + Ant Design 5</Descriptions.Item>
          <Descriptions.Item label="功能">
            <Space wrap>
              <Tag>自选股行情</Tag>
              <Tag>K线图</Tag>
              <Tag>AI 智能对话</Tag>
              <Tag>新闻资讯</Tag>
              <Tag>基金</Tag>
              <Tag>定时任务</Tag>
              <Tag>钉钉推送</Tag>
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="数据来源">
            <Space>
              <Tag>东方财富</Tag>
              <Tag>新浪财经</Tag>
              <Tag>Tushare</Tag>
              <Tag>问财</Tag>
            </Space>
          </Descriptions.Item>
        </Descriptions>

        <Divider />

        <Space style={{ width: '100%', justifyContent: 'center' }}>
          <Link href="https://github.com/ArvinLovegood/go-stock" target="_blank">
            <GithubOutlined /> GitHub
          </Link>
          <Text type="secondary">·</Text>
          <Text type="secondary">
            <HeartOutlined style={{ color: '#f5222d' }} /> 感谢所有开源贡献者
          </Text>
        </Space>

        <Divider />

        <Paragraph type="secondary" style={{ textAlign: 'center', fontSize: 13 }}>
          免责声明：本工具仅供学习研究使用，不构成投资建议。股市有风险，投资需谨慎。
        </Paragraph>
      </Card>
    </div>
  )
}

export default About
