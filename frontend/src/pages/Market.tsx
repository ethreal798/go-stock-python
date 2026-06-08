import React, { useEffect, useState } from 'react'
import { Card, Tabs, Table, Tag, Space, Badge, Statistic, Row, Col } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined, FireOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { getHotStocks, getLimitUpStocks, getAbnormalStocks, getDragonTiger, getMarketIndexes } from '@/api/market'
import type { MarketIndex } from '@/types'

interface HotStockRow {
  rank: number
  code: string
  name: string
  price: number
  changeRate: number
  hotValue: number
}

interface LimitStockRow {
  code: string
  name: string
  price: number
  changeRate: number
  limitTime?: string
  reason?: string
}

const Market: React.FC = () => {
  const [indexes, setIndexes] = useState<MarketIndex[]>([])
  const [hotStocks, setHotStocks] = useState<HotStockRow[]>([])
  const [limitUpStocks, setLimitUpStocks] = useState<LimitStockRow[]>([])
  const [dragonTiger, setDragonTiger] = useState<unknown[]>([])
  const [abnormal, setAbnormal] = useState<unknown[]>([])
  const [loadingMap, setLoadingMap] = useState<Record<string, boolean>>({})

  const setTabLoading = (tab: string, v: boolean) =>
    setLoadingMap((m) => ({ ...m, [tab]: v }))

  useEffect(() => {
    getMarketIndexes()
      .then((res) => {
        const data = (res.data as { data?: MarketIndex[] })?.data ?? []
        setIndexes(data)
      })
      .catch(() => {})
  }, [])

  const loadHot = () => {
    setTabLoading('hot', true)
    getHotStocks()
      .then((res) => {
        const data = (res.data as { data?: HotStockRow[] })?.data ?? []
        setHotStocks(data)
      })
      .catch(() => {})
      .finally(() => setTabLoading('hot', false))
  }

  const loadLimitUp = () => {
    setTabLoading('limitUp', true)
    getLimitUpStocks()
      .then((res) => {
        const data = (res.data as { data?: LimitStockRow[] })?.data ?? []
        setLimitUpStocks(data)
      })
      .catch(() => {})
      .finally(() => setTabLoading('limitUp', false))
  }

  const loadDragonTiger = () => {
    setTabLoading('dragon', true)
    getDragonTiger()
      .then((res: any) => {
        const data = (res.data as { data?: { list: unknown[] } })?.data?.list ?? []
        setDragonTiger(data)
      })
      .catch(() => {})
      .finally(() => setTabLoading('dragon', false))
  }

  const loadAbnormal = () => {
    setTabLoading('abnormal', true)
    getAbnormalStocks()
      .then((res) => {
        const data = (res.data as { data?: unknown[] })?.data ?? []
        setAbnormal(data)
      })
      .catch(() => {})
      .finally(() => setTabLoading('abnormal', false))
  }

  useEffect(() => { loadHot() }, [])

  const hotColumns: ColumnsType<HotStockRow> = [
    { title: '排名', dataIndex: 'rank', width: 60, render: (v: number) => <Tag color={v <= 3 ? 'gold' : 'default'}>{v}</Tag> },
    { title: '代码', dataIndex: 'code', width: 90 },
    { title: '名称', dataIndex: 'name' },
    { title: '现价', dataIndex: 'price', render: (v: number) => v?.toFixed(2) },
    {
      title: '涨跌幅',
      dataIndex: 'changeRate',
      render: (v: number) => (
        <span style={{ color: v >= 0 ? '#f5222d' : '#52c41a', fontWeight: 600 }}>
          {v >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          {Math.abs(v).toFixed(2)}%
        </span>
      ),
    },
    { title: '热度', dataIndex: 'hotValue' },
  ]

  const limitColumns: ColumnsType<LimitStockRow> = [
    { title: '代码', dataIndex: 'code', width: 90 },
    { title: '名称', dataIndex: 'name' },
    { title: '涨停价', dataIndex: 'price', render: (v: number) => <span style={{ color: '#f5222d', fontWeight: 600 }}>{v?.toFixed(2)}</span> },
    { title: '涨跌幅', dataIndex: 'changeRate', render: (v: number) => <Tag color="red">{v?.toFixed(2)}%</Tag> },
    { title: '封板时间', dataIndex: 'limitTime' },
    { title: '涨停原因', dataIndex: 'reason', ellipsis: true },
  ]

  const tabItems = [
    {
      key: 'hot',
      label: <span><FireOutlined />热股榜</span>,
      children: (
        <Table
          rowKey="code"
          columns={hotColumns}
          dataSource={hotStocks}
          loading={loadingMap['hot']}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      ),
    },
    {
      key: 'limitUp',
      label: '涨停板',
      children: (
        <Table
          rowKey="code"
          columns={limitColumns}
          dataSource={limitUpStocks}
          loading={loadingMap['limitUp']}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      ),
    },
    {
      key: 'dragon',
      label: '龙虎榜',
      children: (
        <Table
          rowKey="code"
          columns={[
            { title: '代码', dataIndex: 'code', width: 90 },
            { title: '名称', dataIndex: 'name' },
            { title: '涨跌幅', dataIndex: 'changeRate' },
          ]}
          dataSource={dragonTiger as LimitStockRow[]}
          loading={loadingMap['dragon']}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      ),
    },
    {
      key: 'abnormal',
      label: '异动',
      children: (
        <Table
          rowKey="code"
          columns={[
            { title: '代码', dataIndex: 'code', width: 90 },
            { title: '名称', dataIndex: 'name' },
            { title: '类型', dataIndex: 'type' },
            { title: '涨跌幅', dataIndex: 'changeRate' },
          ]}
          dataSource={abnormal as LimitStockRow[]}
          loading={loadingMap['abnormal']}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      ),
    },
  ]

  return (
    <div>
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        {indexes.map((idx) => (
          <Col key={idx.code} xs={12} sm={8} md={6} lg={4}>
            <Card size="small" bodyStyle={{ padding: '10px 14px' }}>
              <Statistic
                title={idx.name}
                value={idx.price}
                precision={2}
                valueStyle={{ color: idx.changeRate >= 0 ? '#f5222d' : '#52c41a', fontSize: 18 }}
                suffix={
                  <span style={{ fontSize: 13 }}>
                    {idx.changeRate >= 0 ? '+' : ''}{idx.changeRate?.toFixed(2)}%
                  </span>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Card bodyStyle={{ padding: 0 }}>
        <Tabs
          items={tabItems}
          onChange={(key) => {
            if (key === 'limitUp') loadLimitUp()
            if (key === 'dragon') loadDragonTiger()
            if (key === 'abnormal') loadAbnormal()
          }}
          tabBarStyle={{ margin: '0 16px' }}
        />
      </Card>
    </div>
  )
}

export default Market
