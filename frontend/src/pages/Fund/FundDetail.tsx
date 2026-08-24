// src/pages/Fund/FundDetail.tsx
import React, { useMemo, useState, useEffect } from "react";
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
  message,
  Spin,
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
import { followFund, unfollowFund, getFundDetail } from "@/api/fund";
import { useFundPerformance } from "@/hooks/useFundPerformance";
import type { PerformanceSeries, FundDetailResponse } from "@/types/fund";

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

const PERIOD_MAP: Record<RangeKey, string> = {
  week: "1w",
  month: "1m",
  three_month: "3m",
  six_month: "6m",
  year: "1y",
  three_year: "3y",
  all: "since_inception",
};

const toNumber = (v: unknown): number => {
  if (v == null || v === "") return 0;
  const n = typeof v === "string" ? parseFloat(v) : (v as number);
  return Number.isFinite(n) ? n : 0;
};

const formatNullable = (
  v: number | null | undefined,
  digits = 2,
  suffix = "%",
): string => {
  if (v == null) return "-";
  const n = Number(v);
  if (!Number.isFinite(n)) return "-";
  return `${n.toFixed(digits)}${suffix}`;
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

const FundDetail: React.FC = () => {
  const { code } = useParams<{ code: string }>();
  const [range, setRange] = useState<RangeKey>("year");
  const [isFollowed, setIsFollowed] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);
  const [detailData, setDetailData] = useState<FundDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fundCode = code || "005827";

  useEffect(() => {
    if (!fundCode) return;
    setDetailLoading(true);
    getFundDetail(fundCode)
      .then((res) => {
        const data = res.data as FundDetailResponse;
        setDetailData(data);
        
        setIsFollowed(data.is_in_watchlist);
      })
      .catch(() => {
        setDetailData(null);
        
      })
      .finally(() => setDetailLoading(false));
  }, [fundCode]);

  const handleToggleFollow = async () => {
    setFollowLoading(true);
    try {
      if (isFollowed) {
        await unfollowFund(fundCode);
        setIsFollowed(false);
        message.success("已取消关注");
      } else {
        await followFund({ fund_code: fundCode });
        setIsFollowed(true);
        message.success("关注成功");
      }
    } catch {
      // 网络错误统一由 api/index.ts 处理
    } finally {
      setFollowLoading(false);
    }
  };

  const apiPeriod = PERIOD_MAP[range];
  const { data: perfData, loading: perfLoading } = useFundPerformance(
    fundCode,
    apiPeriod,
  );

  const SERIES_COLORS = ["#1677ff", "#8c8c8c", "#faad14", "#73d13d", "#eb2f96"];

  const chartOption = useMemo(() => {
    if (!perfData) {
      return {
        tooltip: {},
        legend: {},
        grid: {},
        xAxis: {},
        yAxis: {},
        series: [],
      };
    }

    const seriesList = perfData.series;
    const categories = seriesList[0]?.points.map((p) => p[0]) ?? [];

    const isHb = perfData.is_hb;

    const echartsSeries = seriesList.map(
      (s: PerformanceSeries, idx: number) => {
        const color = SERIES_COLORS[idx % SERIES_COLORS.length];
        const values = s.points.map((p) => p[1]);

        if (isHb) {
          return {
            name: s.name,
            type: "line",
            showSymbol: false,
            smooth: true,
            lineStyle: { width: 2, color },
            itemStyle: { color },
            data: values,
          };
        }

        return {
          name: s.name,
          type: "line",
          showSymbol: false,
          smooth: true,
          lineStyle: {
            width: s.key === "fund" ? 2 : 1.5,
            color,
            type: s.key === "fund" ? "solid" : "dashed",
          },
          itemStyle: { color },
          areaStyle:
            s.key === "fund"
              ? {
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
                }
              : undefined,
          data: values,
        };
      },
    );

    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross" },
        valueFormatter: (val: number) => `${val.toFixed(2)}%`,
      },
      legend: {
        data: seriesList.map((s) => s.name),
        top: 0,
        right: 10,
      },
      grid: { left: 60, right: 30, top: 40, bottom: 50 },
      xAxis: {
        type: "category",
        data: categories,
        boundaryGap: false,
        axisLine: { lineStyle: { color: "#ddd" } },
        axisLabel: { color: "#666", fontSize: 11 },
      },
      yAxis: {
        type: "value",
        scale: true,
        splitLine: { lineStyle: { color: "#f2f2f2" } },
        axisLabel: {
          color: "#666",
          fontSize: 11,
          formatter: (val: number) => `${val.toFixed(2)}%`,
        },
      },
      dataZoom: [
        { type: "inside", start: 0, end: 100 },
        { type: "slider", height: 20, bottom: 10, start: 0, end: 100 },
      ],
      series: echartsSeries,
    };
  }, [perfData]);

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

  const latest = detailData?.latest;
  const isHb = detailData?.is_hb ?? false;

  const unitNav = latest?.unit_nav;
  const dailyGrowth = latest?.daily_growth_pct;
  const incomePer10k = latest?.income_per_10k;
  const annualized7d = latest?.annualized_7d_pct;

  const weekGrowth = latest?.return_1w_pct;
  const monthGrowth = latest?.return_1m_pct;
  const threeMonthGrowth = latest?.return_3m_pct;
  const sixMonthGrowth = latest?.return_6m_pct;
  const yearGrowth = latest?.return_1y_pct;
  const threeYearGrowth = latest?.return_3y_pct;
  const sinceInception = latest?.return_since_inception_pct;

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
              {detailData?.name || "-"}
            </span>
            <Tag color="geekblue">{detailData?.code || fundCode}</Tag>
            <Tag>{detailData?.fund_type || "-"}</Tag>
          </Space>
        }
        extra={
          <Space size={8}>
            <Button
              type={isFollowed ? "default" : "primary"}
              icon={<PlusOutlined />}
              loading={followLoading}
              onClick={handleToggleFollow}
            >
              {isFollowed ? "已关注" : "加自选"}
            </Button>
            <Button icon={<BellOutlined />}>提醒</Button>
            <Button icon={<ShareAltOutlined />}>分享</Button>
          </Space>
        }
      >
        <Spin spinning={detailLoading}>
          {!latest ? (
            <div
              style={{
                textAlign: "center",
                padding: "40px 0",
                color: "#8c8c8c",
              }}
            >
              暂无数据
            </div>
          ) : isHb ? (
            <Row gutter={[24, 20]} style={{ marginTop: 0 }}>
              <Col span={6}>
                <Statistic
                  title="万份收益"
                  value={incomePer10k ?? "-"}
                  precision={incomePer10k != null ? 4 : undefined}
                  valueStyle={{ fontSize: 26, fontWeight: 700 }}
                  suffix={
                    incomePer10k != null ? (
                      <span style={{ fontSize: 13, marginLeft: 8 }}>元</span>
                    ) : undefined
                  }
                />
                <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
                  7日年化 {formatNullable(annualized7d)}
                </div>
              </Col>
              <Col span={6}>
                <Statistic
                  title="近一年涨跌幅"
                  value={
                    yearGrowth != null ? Number(yearGrowth.toFixed(2)) : "-"
                  }
                  precision={yearGrowth != null ? 2 : undefined}
                  valueStyle={{
                    color:
                      yearGrowth != null
                        ? yearGrowth >= 0
                          ? "#f5222d"
                          : "#52c41a"
                        : undefined,
                    fontSize: 22,
                    fontWeight: 700,
                  }}
                  prefix={yearGrowth != null && yearGrowth >= 0 ? "+" : ""}
                  suffix="%"
                />
                <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
                  14日年化 {formatNullable(latest?.annualized_14d_pct)}
                </div>
              </Col>
              <Col span={6}>
                <Statistic
                  title="近三年涨跌幅"
                  value={
                    threeYearGrowth != null
                      ? Number(threeYearGrowth.toFixed(2))
                      : "-"
                  }
                  precision={threeYearGrowth != null ? 2 : undefined}
                  valueStyle={{
                    color:
                      threeYearGrowth != null
                        ? threeYearGrowth >= 0
                          ? "#f5222d"
                          : "#52c41a"
                        : undefined,
                    fontSize: 22,
                    fontWeight: 700,
                  }}
                  prefix={
                    threeYearGrowth != null && threeYearGrowth >= 0 ? "+" : ""
                  }
                  suffix="%"
                />
                <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
                  28日年化 {formatNullable(latest?.annualized_28d_pct)}
                </div>
              </Col>
              <Col span={6}>
                <Statistic
                  title="成立来涨跌幅"
                  value={
                    sinceInception != null
                      ? Number(sinceInception.toFixed(2))
                      : "-"
                  }
                  precision={sinceInception != null ? 2 : undefined}
                  valueStyle={{
                    color:
                      sinceInception != null
                        ? sinceInception >= 0
                          ? "#f5222d"
                          : "#52c41a"
                        : undefined,
                    fontSize: 22,
                    fontWeight: 700,
                  }}
                  prefix={
                    sinceInception != null && sinceInception >= 0 ? "+" : ""
                  }
                  suffix="%"
                />
                <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
                  同类排名暂无
                </div>
              </Col>
            </Row>
          ) : (
            <Row gutter={[24, 20]} style={{ marginTop: 0 }}>
              <Col span={6}>
                <Statistic
                  title={`最新净值（${latest?.data_date ?? "-"}）`}
                  value={unitNav ?? "-"}
                  precision={unitNav != null ? 4 : undefined}
                  valueStyle={{ fontSize: 26, fontWeight: 700 }}
                  suffix={
                    unitNav != null ? (
                      <span style={{ fontSize: 13, marginLeft: 8 }}>
                        {renderGrowth(dailyGrowth)}
                      </span>
                    ) : undefined
                  }
                />
                <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
                  累计净值 {formatNullable(latest?.accumulated_nav, 4)}
                </div>
              </Col>
              <Col span={6}>
                <Statistic
                  title="近一年涨跌幅"
                  value={
                    yearGrowth != null ? Number(yearGrowth.toFixed(2)) : "-"
                  }
                  precision={yearGrowth != null ? 2 : undefined}
                  valueStyle={{
                    color:
                      yearGrowth != null
                        ? yearGrowth >= 0
                          ? "#f5222d"
                          : "#52c41a"
                        : undefined,
                    fontSize: 22,
                    fontWeight: 700,
                  }}
                  prefix={yearGrowth != null && yearGrowth >= 0 ? "+" : ""}
                  suffix="%"
                />
                <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
                  同类排名暂无
                </div>
              </Col>
              <Col span={6}>
                <Statistic
                  title="近三年涨跌幅"
                  value={
                    threeYearGrowth != null
                      ? Number(threeYearGrowth.toFixed(2))
                      : "-"
                  }
                  precision={threeYearGrowth != null ? 2 : undefined}
                  valueStyle={{
                    color:
                      threeYearGrowth != null
                        ? threeYearGrowth >= 0
                          ? "#f5222d"
                          : "#52c41a"
                        : undefined,
                    fontSize: 22,
                    fontWeight: 700,
                  }}
                  prefix={
                    threeYearGrowth != null && threeYearGrowth >= 0 ? "+" : ""
                  }
                  suffix="%"
                />
                <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
                  同类排名暂无
                </div>
              </Col>
              <Col span={6}>
                <Statistic
                  title="成立来涨跌幅"
                  value={
                    sinceInception != null
                      ? Number(sinceInception.toFixed(2))
                      : "-"
                  }
                  precision={sinceInception != null ? 2 : undefined}
                  valueStyle={{
                    color:
                      sinceInception != null
                        ? sinceInception >= 0
                          ? "#f5222d"
                          : "#52c41a"
                        : undefined,
                    fontSize: 22,
                    fontWeight: 700,
                  }}
                  prefix={
                    sinceInception != null && sinceInception >= 0 ? "+" : ""
                  }
                  suffix="%"
                />
                <div style={{ marginTop: 4, fontSize: 12, color: "#8c8c8c" }}>
                  同类排名暂无
                </div>
              </Col>
            </Row>
          )}

          <Divider style={{ margin: "20px 0" }} />

          {latest && (
            <Row gutter={24}>
              <Col span={24}>
                <Space size={16} wrap style={{ marginBottom: 4 }}>
                  {[
                    {
                      label: "近一周",
                      v: weekGrowth,
                    },
                    { label: "近一月", v: monthGrowth },
                    { label: "近三月", v: threeMonthGrowth },
                    { label: "近六月", v: sixMonthGrowth },
                    { label: "近一年", v: yearGrowth },
                    { label: "近三年", v: threeYearGrowth },
                    { label: "成立来", v: sinceInception },
                  ].map((item) => (
                    <div key={item.label} style={{ minWidth: 92 }}>
                      <div
                        style={{
                          fontSize: 12,
                          color: "#8c8c8c",
                          marginBottom: 2,
                        }}
                      >
                        {item.label}
                      </div>
                      <div style={{ fontSize: 15, fontWeight: 600 }}>
                        {item.v != null ? renderGrowth(item.v) : "-"}
                      </div>
                    </div>
                  ))}
                </Space>
              </Col>
            </Row>
          )}
        </Spin>
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
        <Spin spinning={perfLoading} tip="加载中...">
          <ReactECharts
            option={chartOption}
            style={{ height: 420, width: "100%" }}
            notMerge
            lazyUpdate
          />
        </Spin>
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
