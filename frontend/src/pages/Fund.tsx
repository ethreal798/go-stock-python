import React, { useEffect, useState, useCallback } from 'react'
import { Card, Table, Tag, Space, Input, Button } from 'antd'
import { ReloadOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import request from '@/api/index'
import type { Fund as FundType } from '@/types'

const { Search } = Input

const Fund: React.FC = () => {
  const [funds, setFunds] = useState<FundType[]>([])
  const [loading, setLoading] = useState(false)
  const [keyword, setKeyword] = useState('')

  const fetchFunds = useCallback(async (kw?: string) => {
    setLoading(true)
    try {
      const res = await request.get<{ data?: FundType[] }>('/funds', { params: { keyword: kw } })
      const data = (res.data as { data?: FundType[] })?.data ?? []
      setFunds(data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchFunds()
  }, [fetchFunds])

  const columns: ColumnsType<FundType> = [
    { title: '基金代码', dataIndex: 'code', width: 100 },
    { title: '基金名称', dataIndex: 'name', ellipsis: true },
    { title: '类型', dataIndex: 'type', width: 80, render: (v: string) => <Tag>{v}</Tag> },
    { title: '净值', dataIndex: 'nav', render: (v: number) => v?.toFixed(4) },
    { title: '累计净值', dataIndex: 'accNav', render: (v: number) => v?.toFixed(4) },
    {
      title: '日增长率',
      dataIndex: 'dayGrowth',
      render: (v: number) => (
        <span style={{ color: v >= 0 ? '#f5222d' : '#52c41a', fontWeight: 600 }}>
          {v >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          {Math.abs(v ?? 0).toFixed(2)}%
        </span>
      ),
    },
    {
      title: '近一周',
      dataIndex: 'weekGrowth',
      render: (v: number) =>
        v != null ? (
          <span style={{ color: v >= 0 ? '#f5222d' : '#52c41a' }}>
            {v >= 0 ? '+' : ''}{v.toFixed(2)}%
          </span>
        ) : '-',
    },
    {
      title: '近一月',
      dataIndex: 'monthGrowth',
      render: (v: number) =>
        v != null ? (
          <span style={{ color: v >= 0 ? '#f5222d' : '#52c41a' }}>
            {v >= 0 ? '+' : ''}{v.toFixed(2)}%
          </span>
        ) : '-',
    },
  ]

  return (
    <Card
      title="基金"
      extra={
        <Space>
          <Search
            placeholder="搜索基金代码/名称"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onSearch={(v) => fetchFunds(v)}
            style={{ width: 220 }}
          />
          <Button icon={<ReloadOutlined />} onClick={() => fetchFunds(keyword)}>
            刷新
          </Button>
        </Space>
      }
      bodyStyle={{ padding: 0 }}
    >
      <Table
        rowKey="code"
        columns={columns}
        dataSource={funds}
        loading={loading}
        pagination={{ pageSize: 20 }}
        size="small"
      />
    </Card>
  )
}

export default Fund
