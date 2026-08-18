// src/pages/Fund/FundDetail.tsx
import React, { useMemo, useState } from "react";
import {
  Breadcrumb,
  Card,
  Row,
  Col,
  Statistic,
  Tag,
  Button,
  Space,
  Tabs,
  Table,
  Descriptions,
  Progress,
  List,
  Typography,
  Segmented,
  Divider,
} from "antd";
import {
  ArrowLeftOutlined,
  PlusOutlined,
  BellOutlined,
  ShareAltOutlined,
  InfoCircleOutlined,
  RiseOutlined,
  FallOutlined,
} from "@ant-design/icons";
import { Link, useParams } from "react-router-dom";
import ReactECharts from "echarts-for-react";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";

const { Paragraph, Text } = Typography;

type RangeKey =
  | "week"
  | "month"
  | "three_month"
  | "six_month"
  | "year"
  | "three_year"
  | "all";

const RANGE_OPTIONS: { label: string; value: RangeKey }[] = [
  { label: "近一周", value: "week" },
  { label: "近一月", value: "month" },
  { label: "近三月", value: "three_month" },
  { label: "近六月", value: "six_month" },
  { label: "近一年", value: "year" },
  { label: "近三年", value: "three_year" },
  { label: "成立来", value: "all" },
];

const toNumber = (v: unknown): number => {
  if (v == null || v === "") return 0;
  const n = typeof v === "string" ? parseFloat(v) : (v as number);
  return Number.isFinite(n) ? n : 0;
};

const renderGrowth = (v: number | string | null | undefined, digits = 2) => {
  const num = toNumber(v);
  const color = num > 0 ? "#f5222d" : num < 0 ? "#52c41a" : "inherit";
  const Icon =
    num > 0 ? RiseOutlined : num < 0 ? FallOutlined : InfoCircleOutlined;
  return (
    <span style={{ color, fontWeight: 600 }}>
      {num !== 0 && <Icon style={{ fontSize: 12, marginRight: 2 }} />}
      {num > 0 ? "+" : ""}
      {num.toFixed(digits)}%
    </span>
  );
};

interface HoldingRow {
  key: string;
  code: string;
  name: string;
  ratio: number;
  change: number;
  latest_price: number;
}

const MOCK_HOLDINGS: HoldingRow[] = [
  {
    key: "1",
    code: "600519",
    name: "贵州茅台",
    ratio: 9.82,
    change: 1.35,
    latest_price: 1680.5,
  },
  {
    key: "2",
    code: "000858",
    name: "五粮液",
    ratio: 7.64,
    change: -0.82,
    latest_price: 142.3,
  },
  {
    key: "3",
    code: "300750",
    name: "宁德时代",
    ratio: 6.51,
    change: 2.11,
    latest_price: 238.9,
  },
  {
    key: "4",
    code: "601318",
    name: "中国平安",
    ratio: 5.88,
    change: 0.45,
    latest_price: 49.2,
  },
  {
    key: "5",
    code: "600036",
    name: "招商银行",
    ratio: 5.2,
    change: -0.31,
    latest_price: 35.7,
  },
  {
    key: "6",
    code: "000333",
    name: "美的集团",
    ratio: 4.77,
    change: 1.02,
    latest_price: 68.4,
  },
  {
    key: "7",
    code: "002594",
    name: "比亚迪",
    ratio: 4.32,
    change: 3.21,
    latest_price: 261.8,
  },
  {
    key: "8",
    code: "600276",
    name: "恒瑞医药",
    ratio: 3.95,
    change: -1.15,
    latest_price: 48.1,
  },
  {
    key: "9",
    code: "601888",
    name: "中国中免",
    ratio: 3.58,
    change: 2.86,
    latest_price: 82.5,
  },
  {
    key: "10",
    code: "000001",
    name: "平安银行",
    ratio: 3.12,
    change: -0.55,
    latest_price: 11.3,
  },
];

const MOCK_ANNOUNCEMENTS = [
  {
    title: "关于本基金增加C类基金份额并修改基金合同的公告",
    date: "2026-08-10",
    type: "基金合同",
  },
  {
    title: "2026年第2号招募说明书更新",
    date: "2026-08-05",
    type: "招募说明书",
  },
  { title: "2026年第二季度报告", date: "2026-07-20", type: "季度报告" },
  {
    title: "关于旗下部分基金新增华瑞保险销售为代销机构的公告",
    date: "2026-07-12",
    type: "代销机构",
  },
  { title: "2025年年度报告摘要", date: "2026-03-30", type: "年度报告" },
];

const genTrendData = (range: RangeKey) => {
  const counts: Record<RangeKey, number> = {
    week: 7,
    month: 22,
    three_month: 66,
    six_month: 132,
    year: 250,
    three_year: 750,
    all: 1200,
  };
  const n = counts[range];
  const dates: string[] = [];
  const nav: number[] = [];
  const benchmark: number[] = [];
  let base = 1.0;
  let base2 = 1.0;
  const today = dayjs();
  for (let i = n - 1; i >= 0; i--) {
    dates.push(today.subtract(i, "day").format("YYYY-MM-DD"));
    base *= 1 + (Math.sin(i / 10) * 0.002 + (Math.random() - 0.48) * 0.008);
    base2 *= 1 + (Math.cos(i / 14) * 0.001 + (Math.random() - 0.49) * 0.006);
    nav.push(+base.toFixed(4));
    benchmark.push(+base2.toFixed(4));
  }
  return { dates, nav, benchmark };
};

const FundDetail: React.FC = () => {
  const { code } = useParams<{ code: string }>();
  const [range, setRange] = useState<RangeKey>("year");
  const [isFollowed, setIsFollowed] = useState(false);

  const trendData = useMemo(() => genTrendData(range), [range]);

  const chartOption = useMemo(() => {
    const start = trendData.nav[0] ?? 1;
    const latest = trendData.nav[trendData.nav.length - 1] ?? 1;
    const navYield = ((latest - start) / start) * 100;
    const bStart = trendData.benchmark[0] ?? 1;
    const bLatest = trendData.benchmark[trendData.benchmark.length - 1] ?? 1;
    const benchYield = ((bLatest - bStart) / bStart) * 100;
    return {
      tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
      legend: {
        data: ["本基金净值", "业绩比较基准"],
        top: 0,
        right: 10,
      },
      grid: { left: 50, right: 30, top: 40, bottom: 50 },
      xAxis: {
        type: "category",
        data: trendData.dates,
        boundaryGap: false,
        axisLine: { lineStyle: { color: "#ddd" } },
        axisLabel: { color: "#666", fontSize: 11 },
      },
      yAxis: {
        type: "value",
        scale: true,
        splitLine: { lineStyle: { color: "#f2f2f2" } },
        axisLabel: { color: "#666", fontSize: 11 },
      },
      dataZoom: [
        { type: "inside", start: 0, end: 100 },
        { type: "slider", height: 20, bottom: 10, start: 0, end: 100 },
      ],
      series: [
        {
          name: "本基金净值",
          type: "line",
          showSymbol: false,
          smooth: true,
          lineStyle: { width: 2, color: "#1677ff" },
          itemStyle: { color: "#1677ff" },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(22,119,255,0.25)" },
                { offset: 1, color: "rgba(22,119,255,0.02)" },
              ],
            },
          },
          data: trendData.nav,
          markLine: {
            silent: true,
            symbol: "none",
            lineStyle: { color: "#f5222d", type: "dashed" },
            label: {
              formatter: `区间收益 ${navYield >= 0 ? "+" : ""}${navYield.toFixed(2)}%`,
              position: "insideEndTop",
              color: "#f5222d",
            },
            data: [{ type: "average" }],
          },
        },
        {
          name: "业绩比较基准",
          type: "line",
          showSymbol: false,
          smooth: true,
          lineStyle: { width: 1.5, color: "#8c8c8c", type: "dashed" },
          itemStyle: { color: "#8c8c8c" },
          data: trendData.benchmark,
          markLine: {
            silent: true,
            symbol: "none",
            lineStyle: { color: "#8c8c8c", type: "dashed" },
            label: {
              formatter: `基准 ${benchYield >= 0 ? "+" : ""}${benchYield.toFixed(2)}%`,
              position: "insideEndBottom",
              color: "#8c8c8c",
            },
            data: [{ type: "average" }],
          },
        },
      ],
    };
  }, [trendData]);

  const holdingColumns: ColumnsType<HoldingRow> = [
    { title: "序号", dataIndex: "key", width: 60, align: "center" },
    { title: "股票代码", dataIndex: "code", width: 100 },
    { title: "股票名称", dataIndex: "name", width: 140 },
    {
      title: "占净值比",
      dataIndex: "ratio",
      width: 140,
      render: (v: number) => (
        <Space>
          <Progress
            percent={v * 5}
            size="small"
            showInfo={false}
            style={{ width: 80 }}
          />
          <Text strong>{v.toFixed(2)}%</Text>
        </Space>
      ),
    },
    {
      title: "最新价",
      dataIndex: "latest_price",
      width: 100,
      render: (v: number) => v.toFixed(2),
    },
    {
      title: "当日涨跌",
      dataIndex: "change",
      width: 110,
      render: (v: number) => renderGrowth(v),
    },
  ];

  const latestNav = 2.3845;
  const dayGrowth = 0.68;
  const weekGrowth = 1.12;
  const monthGrowth = -0.45;
  const threeMonthGrowth = 5.23;
  const sixMonthGrowth = 8.97;
  const yearGrowth = 18.42;
  const threeYearGrowth = 45.66;
  const sinceInception = 138.42;
  const benchmarkSince = 62.35;

  return (
    <div style={{ paddingBottom: 20 }}>
      <Space style={{ marginBottom: 16 }}>
        <Link to="/fund/market">
          <Button icon={<ArrowLeftOutlined />}>返回基金市场</Button>
        </Link>
        <Breadcrumb
          items={[
            { title: <Link to="/fund">基金</Link> },
            { title: <Link to="/fund/market">基金市场</Link> },
            { title: "基金详情" },
          ]}
        />
      </Space>

      <Card
        bodyStyle={{ padding: "20px 24px" }}
        title={
          <Space size={16} align="center">
            <span style={{ fontSize: 20, fontWeight: 700, color: "#000" }}>
              易方达蓝筹精选混合
            </span>
            <Tag color="geekblue">{code || "005827"}</Tag>
            <Tag>混合型</Tag>
          </Space>
        }
        extra={
          <Space size={8}>
            <Button
              type={isFollowed ? "default" : "primary"}
              icon={<PlusOutlined />}
              onClick={() => setIsFollowed((v) => !v)}
            >
              {isFollowed ? "已关注" : "加自选"}
            </Button>
            <Button icon={<BellOutlined />}>提醒</Button>
            <Button icon={<ShareAltOutlined />}>分享</Button>
          </Space>
        }
      >
        <Row gutter={[24, 20]} style={{ marginTop: 0 }}>
          <Col span={6}>
            <Statistic
              title="最新净值（2026-08-11）"
              value={latestNav}
              precision={4}
              valueStyle={{ fontSize: 26, fontWeight: 700 }}
              suffix={
                <span style={{ fontSize: 13, marginLeft: 8 }}>
                  {renderGrowth(dayGrowth)}
                </span>
              }
            />
            <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
              估算净值 {latestNav + 0.0032}（{dayjs().format("HH:mm")}）
            </div>
          </Col>
          <Col span={6}>
            <Statistic
              title="近一年涨跌幅"
              value={yearGrowth}
              precision={2}
              valueStyle={{
                color: yearGrowth >= 0 ? "#f5222d" : "#52c41a",
                fontSize: 22,
                fontWeight: 700,
              }}
              prefix={yearGrowth >= 0 ? "+" : ""}
              suffix="%"
            />
            <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
              同类排名 128 / 1,892（前 6.77%）
            </div>
          </Col>
          <Col span={6}>
            <Statistic
              title="近三年涨跌幅"
              value={threeYearGrowth}
              precision={2}
              valueStyle={{
                color: threeYearGrowth >= 0 ? "#f5222d" : "#52c41a",
                fontSize: 22,
                fontWeight: 700,
              }}
              prefix={threeYearGrowth >= 0 ? "+" : ""}
              suffix="%"
            />
            <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
              同类排名 205 / 1,520（前 13.49%）
            </div>
          </Col>
          <Col span={6}>
            <Statistic
              title="成立来涨跌幅"
              value={sinceInception}
              precision={2}
              valueStyle={{ color: "#f5222d", fontSize: 22, fontWeight: 700 }}
              prefix="+"
              suffix="%"
            />
            <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
              基准 {benchmarkSince >= 0 ? "+" : ""}
              {benchmarkSince.toFixed(2)}% · 成立日 2018-09-05
            </div>
          </Col>
        </Row>

        <Divider style={{ margin: "20px 0" }} />

        <Row gutter={24}>
          <Col span={24}>
            <Space size={16} wrap style={{ marginBottom: 4 }}>
              {[
                { label: "近一周", v: weekGrowth },
                { label: "近一月", v: monthGrowth },
                { label: "近三月", v: threeMonthGrowth },
                { label: "近六月", v: sixMonthGrowth },
                { label: "近一年", v: yearGrowth },
                { label: "近三年", v: threeYearGrowth },
                { label: "成立来", v: sinceInception },
              ].map((item) => (
                <div key={item.label} style={{ minWidth: 92 }}>
                  <div
                    style={{ fontSize: 12, color: "#8c8c8c", marginBottom: 2 }}
                  >
                    {item.label}
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 600 }}>
                    {renderGrowth(item.v)}
                  </div>
                </div>
              ))}
            </Space>
          </Col>
        </Row>
      </Card>

      <Card
        style={{ marginTop: 16 }}
        bodyStyle={{ padding: "16px 24px 24px" }}
        title="业绩走势"
        extra={
          <Segmented<RangeKey>
            value={range}
            options={RANGE_OPTIONS}
            onChange={setRange}
          />
        }
      >
        <ReactECharts
          option={chartOption}
          style={{ height: 420, width: "100%" }}
          notMerge
          lazyUpdate
        />
      </Card>

      <Card style={{ marginTop: 16 }} bodyStyle={{ padding: 0 }}>
        <Tabs
          size="large"
          defaultActiveKey="holdings"
          tabBarStyle={{ paddingLeft: 24 }}
          items={[
            {
              key: "holdings",
              label: "基金持仓",
              children: (
                <div style={{ padding: "16px 24px" }}>
                  <Row gutter={24} style={{ marginBottom: 16 }}>
                    <Col span={8}>
                      <Descriptions column={1} size="small" bordered>
                        <Descriptions.Item label="股票占净比">
                          86.32%
                        </Descriptions.Item>
                        <Descriptions.Item label="债券占净比">
                          3.85%
                        </Descriptions.Item>
                        <Descriptions.Item label="现金占净比">
                          8.91%
                        </Descriptions.Item>
                        <Descriptions.Item label="其他">
                          0.92%
                        </Descriptions.Item>
                      </Descriptions>
                    </Col>
                    <Col span={16}>
                      <Descriptions column={2} size="small" bordered>
                        <Descriptions.Item label="前十持仓占比合计">
                          54.79%
                        </Descriptions.Item>
                        <Descriptions.Item label="持仓集中度">
                          中高
                        </Descriptions.Item>
                        <Descriptions.Item label="换手率（近一年）">
                          186.42%
                        </Descriptions.Item>
                        <Descriptions.Item label="行业集中度">
                          消费+科技
                        </Descriptions.Item>
                        <Descriptions.Item label="最新规模">
                          682.5 亿元
                        </Descriptions.Item>
                        <Descriptions.Item label="报告期">
                          2026Q2
                        </Descriptions.Item>
                      </Descriptions>
                    </Col>
                  </Row>
                  <Table<HoldingRow>
                    rowKey="key"
                    columns={holdingColumns}
                    dataSource={MOCK_HOLDINGS}
                    pagination={false}
                    size="small"
                  />
                </div>
              ),
            },
            {
              key: "manager",
              label: "基金经理",
              children: (
                <div style={{ padding: "16px 24px" }}>
                  <Row gutter={24}>
                    <Col span={6}>
                      <Card hoverable style={{ borderRadius: 8 }}>
                        <Space
                          direction="vertical"
                          size={12}
                          style={{ width: "100%" }}
                        >
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 12,
                            }}
                          >
                            <div
                              style={{
                                width: 60,
                                height: 60,
                                borderRadius: "50%",
                                background:
                                  "linear-gradient(135deg,#1677ff,#69b1ff)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                color: "#fff",
                                fontSize: 22,
                                fontWeight: 700,
                              }}
                            >
                              张
                            </div>
                            <div>
                              <div style={{ fontSize: 17, fontWeight: 700 }}>
                                张坤
                              </div>
                              <div style={{ color: "#8c8c8c", fontSize: 13 }}>
                                投资总监 · 从业 15 年
                              </div>
                            </div>
                          </div>
                          <Divider style={{ margin: "4px 0" }} />
                          <Descriptions column={1} size="small">
                            <Descriptions.Item label="任职日期">
                              2018-09-05
                            </Descriptions.Item>
                            <Descriptions.Item label="任职回报">
                              <span
                                style={{ color: "#f5222d", fontWeight: 600 }}
                              >
                                +138.42%
                              </span>
                            </Descriptions.Item>
                            <Descriptions.Item label="年化回报">
                              <span
                                style={{ color: "#f5222d", fontWeight: 600 }}
                              >
                                +12.56%
                              </span>
                            </Descriptions.Item>
                            <Descriptions.Item label="在管基金数">
                              8 只 · 合计 1,205 亿
                            </Descriptions.Item>
                          </Descriptions>
                          <Paragraph
                            type="secondary"
                            ellipsis={{
                              rows: 4,
                              expandable: true,
                              symbol: "展开",
                            }}
                          >
                            理学硕士，曾任易方达基金研究员、基金经理助理，现任易方达基金管理有限公司副总经理级高级基金经理、权益投资决策委员会成员。
                            投资风格偏大盘价值，长期坚守优质公司，换手率较低，注重安全边际，代表产品管理规模长期居行业前列。
                          </Paragraph>
                        </Space>
                      </Card>
                    </Col>
                    <Col span={18}>
                      <Card title="在管产品（部分）" size="small">
                        <Table
                          size="small"
                          pagination={false}
                          rowKey="code"
                          columns={[
                            { title: "基金代码", dataIndex: "code" },
                            { title: "基金名称", dataIndex: "name" },
                            { title: "任职日期", dataIndex: "start" },
                            {
                              title: "任职回报",
                              dataIndex: "yield",
                              render: (v: number) => renderGrowth(v),
                            },
                            {
                              title: "规模（亿）",
                              dataIndex: "scale",
                              render: (v) => v.toFixed(1),
                            },
                          ]}
                          dataSource={[
                            {
                              code: "005827",
                              name: "易方达蓝筹精选混合",
                              start: "2018-09-05",
                              yield: 138.42,
                              scale: 682.5,
                            },
                            {
                              code: "110011",
                              name: "易方达中小盘混合",
                              start: "2012-09-28",
                              yield: 527.86,
                              scale: 287.4,
                            },
                            {
                              code: "000083",
                              name: "易方达消费行业股票",
                              start: "2016-01-22",
                              yield: 298.15,
                              scale: 152.3,
                            },
                            {
                              code: "010186",
                              name: "易方达优质企业三年持有",
                              start: "2020-07-16",
                              yield: 12.46,
                              scale: 83.2,
                            },
                          ]}
                        />
                      </Card>
                    </Col>
                  </Row>
                </div>
              ),
            },
            {
              key: "info",
              label: "基本信息",
              children: (
                <div style={{ padding: "16px 24px" }}>
                  <Row gutter={24}>
                    <Col span={12}>
                      <Descriptions
                        title="基金概况"
                        column={1}
                        bordered
                        size="small"
                        labelStyle={{ width: 140 }}
                      >
                        <Descriptions.Item label="基金全称">
                          易方达蓝筹精选混合型证券投资基金
                        </Descriptions.Item>
                        <Descriptions.Item label="基金简称">
                          易方达蓝筹精选混合
                        </Descriptions.Item>
                        <Descriptions.Item label="基金代码">
                          005827.OF
                        </Descriptions.Item>
                        <Descriptions.Item label="基金类型">
                          混合型-偏股
                        </Descriptions.Item>
                        <Descriptions.Item label="发行日期">
                          2018-08-20 ~ 2018-09-03
                        </Descriptions.Item>
                        <Descriptions.Item label="成立日期 / 规模">
                          2018-09-05 · 682.50 亿元
                        </Descriptions.Item>
                        <Descriptions.Item label="基金管理人">
                          易方达基金管理有限公司
                        </Descriptions.Item>
                        <Descriptions.Item label="基金托管人">
                          中国工商银行股份有限公司
                        </Descriptions.Item>
                        <Descriptions.Item label="基金经理">
                          张坤
                        </Descriptions.Item>
                      </Descriptions>
                    </Col>
                    <Col span={12}>
                      <Descriptions
                        title="交易规则"
                        column={1}
                        bordered
                        size="small"
                        labelStyle={{ width: 140 }}
                      >
                        <Descriptions.Item label="管理费 / 托管费">
                          1.50% / 0.25%（每年）
                        </Descriptions.Item>
                        <Descriptions.Item label="销售服务费">
                          -
                        </Descriptions.Item>
                        <Descriptions.Item label="最高申购费率">
                          1.50%（前端）
                        </Descriptions.Item>
                        <Descriptions.Item label="最高赎回费率">
                          1.50%（持有 {"<"} 7天）
                        </Descriptions.Item>
                        <Descriptions.Item label="业绩比较基准">
                          沪深300指数收益率×60% + 中证港股通综合指数×20% +
                          中债总指数×20%
                        </Descriptions.Item>
                        <Descriptions.Item label="跟踪标的">
                          该基金无跟踪标的
                        </Descriptions.Item>
                        <Descriptions.Item label="收益分配原则">
                          在符合分红条件的前提下，本基金每年收益分配次数最多为12次
                        </Descriptions.Item>
                      </Descriptions>
                    </Col>
                  </Row>
                </div>
              ),
            },
            {
              key: "announcement",
              label: "基金公告",
              children: (
                <div style={{ padding: "16px 24px" }}>
                  <List
                    size="large"
                    dataSource={MOCK_ANNOUNCEMENTS}
                    renderItem={(item) => (
                      <List.Item
                        key={item.title}
                        actions={[
                          <span
                            style={{ color: "#8c8c8c", fontSize: 12 }}
                            key="date"
                          >
                            {item.date}
                          </span>,
                          <Button type="link" size="small" key="view">
                            查看
                          </Button>,
                        ]}
                      >
                        <Space>
                          <Tag color="blue">{item.type}</Tag>
                          <span style={{ color: "#000" }}>{item.title}</span>
                        </Space>
                      </List.Item>
                    )}
                  />
                </div>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default FundDetail;
