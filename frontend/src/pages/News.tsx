import React, { useEffect, useState, useCallback } from 'react'
import { Card, List, Tag, Space, Input, Tabs, Badge, Typography, Button } from 'antd'
import { ReloadOutlined, LinkOutlined, ThunderboltOutlined, ReadOutlined } from '@ant-design/icons'
import { getNewsList, getFlashNews } from '@/api/market'
import type { NewsItem } from '@/types'
import dayjs from 'dayjs'

const { Search } = Input
const { Text, Paragraph } = Typography

const News: React.FC = () => {
  const [flashNews, setFlashNews] = useState<NewsItem[]>([])
  const [newsList, setNewsList] = useState<NewsItem[]>([])
  const [flashLoading, setFlashLoading] = useState(false)
  const [newsLoading, setNewsLoading] = useState(false)
  const [keyword, setKeyword] = useState('')

  const fetchFlash = useCallback(async () => {
    setFlashLoading(true)
    try {
      const res = await getFlashNews({ pageSize: 50 })
      const data = (res.data as { data?: NewsItem[] })?.data ?? []
      setFlashNews(data)
    } catch {
      // ignore
    } finally {
      setFlashLoading(false)
    }
  }, [])

  const fetchNews = useCallback(async (kw?: string) => {
    setNewsLoading(true)
    try {
      const res = await getNewsList({ keyword: kw, pageSize: 30 })
      const data = (res.data as { data?: NewsItem[] })?.data ?? []
      setNewsList(data)
    } catch {
      // ignore
    } finally {
      setNewsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchFlash()
    fetchNews()
  }, [fetchFlash, fetchNews])

  const tabItems = [
    {
      key: 'flash',
      label: (
        <span>
          <ThunderboltOutlined style={{ color: '#faad14' }} />
          快讯电报
          <Badge count={flashNews.length} style={{ marginLeft: 6 }} />
        </span>
      ),
      children: (
        <List
          loading={flashLoading}
          dataSource={flashNews}
          size="small"
          renderItem={(item) => (
            <List.Item
              extra={
                item.url && (
                  <a href={item.url} target="_blank" rel="noreferrer">
                    <LinkOutlined />
                  </a>
                )
              }
            >
              <List.Item.Meta
                title={
                  <Space size={4} wrap>
                    <Text style={{ fontWeight: 500 }}>{item.title}</Text>
                    {item.tags?.map((t) => <Tag key={t} color="blue" style={{ fontSize: 11 }}>{t}</Tag>)}
                  </Space>
                }
                description={
                  <Space>
                    <Tag color="purple">{item.source}</Tag>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {dayjs(item.publishedAt).format('MM-DD HH:mm')}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      ),
    },
    {
      key: 'news',
      label: (
        <span>
          <ReadOutlined />
          新闻资讯
        </span>
      ),
      children: (
        <>
          <Search
            placeholder="搜索新闻关键词..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onSearch={(v) => fetchNews(v)}
            style={{ marginBottom: 12 }}
          />
          <List
            loading={newsLoading}
            dataSource={newsList}
            renderItem={(item) => (
              <List.Item
                actions={[
                  item.url && (
                    <a key="link" href={item.url} target="_blank" rel="noreferrer">
                      查看详情
                    </a>
                  ),
                ].filter(Boolean)}
              >
                <List.Item.Meta
                  title={
                    <a href={item.url ?? '#'} target="_blank" rel="noreferrer" style={{ fontWeight: 600 }}>
                      {item.title}
                    </a>
                  }
                  description={
                    <Space>
                      <Tag>{item.source}</Tag>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {dayjs(item.publishedAt).format('YYYY-MM-DD HH:mm')}
                      </Text>
                    </Space>
                  }
                />
                {item.content && (
                  <Paragraph
                    ellipsis={{ rows: 2 }}
                    type="secondary"
                    style={{ fontSize: 13, marginTop: 4 }}
                  >
                    {item.content}
                  </Paragraph>
                )}
              </List.Item>
            )}
          />
        </>
      ),
    },
  ]

  return (
    <Card
      title="新闻资讯"
      extra={
        <Button icon={<ReloadOutlined />} onClick={() => { fetchFlash(); fetchNews(keyword) }}>
          刷新
        </Button>
      }
      bodyStyle={{ padding: '0 0 16px' }}
    >
      <Tabs items={tabItems} tabBarStyle={{ padding: '0 16px' }} />
    </Card>
  )
}

export default News
