// src/pages/Fund/FundMarket.tsx
import React, { useState, useCallback, useMemo } from "react";
import {
  Card,
  Table,
  Tag,
  Button,
  Space,
  Segmented,
  Select,
  message,
} from "antd";
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import type { ColumnsType } from "antd/es/table";
import type { FollowFundInfo, FundTableRow } from "@/types/fund";
import { searchFund, followFund } from "@/api/fund";
import type { FundRangeKey } from "@/api/fund";
import FollowModal from "./components/FollowModal";

const FUND_TYPE_OPTIONS: { label: string; value: string }[] = [
  { label: "股票型", value: "股票型" },
  { label: "混合型", value: "混合型" },
  { label: "债券型", value: "债券型" },
  { label: "指数型", value: "指数型" },
  { label: "QDII", value: "QDII" },
  { label: "FOF", value: "FOF" },
  { label: "货币型", value: "货币型" },
];

type SortOrder = "ascend" | "descend";

const RANGE_OPTIONS: { label: string; value: FundRangeKey }[] = [
  { label: "日涨幅", value: "day" },
  { label: "近一周", value: "week" },
  { label: "近一月", value: "month" },
  { label: "近三月", value: "three_month" },
  { label: "近六月", value: "six_month" },
  { label: "近一年", value: "year" },
  { label: "近两年", value: "two_year" },
  { label: "近三年", value: "three_year" },
  { label: "近五年", value: "five_year" },
];

/**
 * 根据范围键获取对应的增长字段名
 */
const RANGE_GROWTH_FIELD: Record<FundRangeKey, string> = {
  day: "daily_growth_pct",
  week: "return_1w_pct",
  month: "return_1m_pct",
  three_month: "return_3m_pct",
  six_month: "return_6m_pct",
  year: "return_1y_pct",
  two_year: "return_2y_pct",
  three_year: "return_3y_pct",
  five_year: "return_3y_pct", // 五年暂时用三年字段
};

const toNumber = (v: unknown): number | null => {
  if (v == null || v === "") return null;
  const num = typeof v === "string" ? parseFloat(v) : (v as number);
  return Number.isFinite(num) ? num : null;
};

/**
 * 格式化增长率显示
 */
const renderGrowth = (v: string | number | null | undefined) => {
  const num = toNumber(v);
  if (num == null) return "-";
  return (
    <span
      style={{
        color: num >= 0 ? "#f5222d" : "#52c41a",
        fontWeight: 600,
      }}
    >
      {num >= 0 ? "+" : ""}
      {num.toFixed(2)}%
    </span>
  );
};

/**
 * 将 FollowFundInfo 转换为 FundTableRow
 */
const toFundTableRow = (info: FollowFundInfo): FundTableRow => ({
  id: info.id,
  code: info.code,
  name: info.name,
  type: info.type,
  is_followed: info.is_in_watchlist ?? false,
  latest: info.latest,
  last_seen_data_date: info.last_seen_data_date,
});

/**
 * 基金市场页面属性
 */
interface FundMarketProps {
  /** 关注成功后的回调 */
  onFollowSuccess?: () => void;
}

/**
 * 基金市场页面
 * 支持按时间范围筛选、基金类型筛选
 * 搜索功能已迁移到独立的搜索页面
 */
const FundMarket: React.FC<FundMarketProps> = ({ onFollowSuccess }) => {
  const navigate = useNavigate();

  const [list, setList] = useState<FundTableRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [range, setRange] = useState<FundRangeKey>("day");
  const [fundType, setFundType] = useState<string | undefined>(undefined);

  const [sortField, setSortField] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder | null>(null);

  const [modalVisible, setModalVisible] = useState(false);
  const [selectedFund, setSelectedFund] = useState<FundTableRow | null>(null);
  const [followLoading, setFollowLoading] = useState(false);

  const growthField = RANGE_GROWTH_FIELD[range];

  const handleSearch = useCallback(
    async (
      page: number = 1,
      currentRange?: FundRangeKey,
      currentFundType?: string | undefined,
    ) => {
      setLoading(true);
      try {
        const res = await searchFund({
          keyword: "",
          page,
          limit: 20,
          range: currentRange ?? range,
          fund_type: currentFundType ?? fundType,
        });
        const data = (res.data || []).map(toFundTableRow);
        if (page === 1) {
          setList(data);
        } else {
          setList((prev) => [...prev, ...data]);
        }
        setCurrentPage(page);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    },
    [range, fundType],
  );

  const handleRangeChange = useCallback(
    (next: FundRangeKey) => {
      setRange(next);
      void handleSearch(1, next, fundType);
    },
    [handleSearch, fundType],
  );

  const handleFundTypeChange = useCallback(
    (next: string | undefined) => {
      setFundType(next);
      void handleSearch(1, range, next);
    },
    [handleSearch, range],
  );

  /**
   * 打开关注弹窗
   */
  const handleOpenModal = (fund: FundTableRow) => {
    if (fund.is_followed) return;
    setSelectedFund(fund);
    setModalVisible(true);
  };

  /**
   * 确认添加关注
   */
  const handleConfirmFollow = async (remark: string) => {
    if (!selectedFund) return;
    setFollowLoading(true);
    try {
      await followFund({ fund_code: selectedFund.code, remark });
      setList((prev) =>
        prev.map((item) =>
          item.code === selectedFund.code
            ? { ...item, is_followed: true }
            : item,
        ),
      );
      message.success("关注成功");
      setModalVisible(false);
      onFollowSuccess?.();
    } catch {
      // ignore
    } finally {
      setFollowLoading(false);
    }
  };

  const sortedList = useMemo(() => {
    if (!sortField || !sortOrder) return list;
    const sorted = [...list];
    sorted.sort((a, b) => {
      // 从 latest 中获取值
      const av = toNumber(a.latest?.[growthField as keyof typeof a.latest]);
      const bv = toNumber(b.latest?.[growthField as keyof typeof b.latest]);
      const an = av ?? 0;
      const bn = bv ?? 0;
      return sortOrder === "ascend" ? an - bn : bn - an;
    });
    return sorted;
  }, [list, sortField, sortOrder, growthField]);

  const handleTableChange = (
    _pagination: unknown,
    _filters: unknown,
    sorter: unknown,
  ) => {
    const s = sorter as
      | { field?: string | null; order?: SortOrder | null }
      | { field?: string | null; order?: SortOrder | null }[];
    const first = Array.isArray(s) ? s[0] : s;
    const field = first?.field ?? null;
    const order = first?.order ?? null;
    setSortField(field);
    setSortOrder(order);
  };

  const columns: ColumnsType<FundTableRow> = [
    {
      title: "基金名称",
      width: 290,
      render: (_, record) => (
        <a
          href={`/fund/detail/${record.code ?? ""}`}
          onClick={(e) => {
            e.preventDefault();
            navigate(`/fund/detail/${record.code ?? ""}`);
          }}
          style={{ display: "block", color: "inherit", textDecoration: "none" }}
        >
          <div
            style={{
              fontSize: 15,
              fontWeight: 600,
              color: "#000",
              lineHeight: 1.4,
              marginBottom: 4,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {record.name ?? "-"}
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: 12,
            }}
          >
            {record.code ? (
              <span style={{ color: "#1677ff" }}>{record.code}</span>
            ) : null}
            {record.type ? (
              <Tag style={{ margin: 0, fontSize: 12, padding: "0 6px" }}>
                {record.type}
              </Tag>
            ) : null}
          </div>
        </a>
      ),
    },
    {
      title: "单位净值",
      width: 130,
      render: (_, record) => {
        const v = record.latest?.unit_nav;
        return v != null ? v.toFixed(4) : "-";
      },
    },
    {
      title: "累计净值",
      width: 130,
      render: (_, record) => {
        const v = record.latest?.accumulated_nav;
        return v != null ? v.toFixed(4) : "-";
      },
    },
    {
      title: "涨跌幅",
      key: "growth",
      width: 130,
      sorter: true,
      sortOrder: sortField === growthField ? sortOrder : null,
      render: (_, record) => {
        const v = record.latest?.[growthField as keyof typeof record.latest];
        return renderGrowth(v as number | string | null | undefined);
      },
    },
    {
      title: "近一年",
      width: 130,
      sorter: true,
      sortOrder: sortField === "return_1y_pct" ? sortOrder : null,
      render: (_, record) => renderGrowth(record.latest?.return_1y_pct),
    },
    {
      title: "成立来",
      width: 130,
      sorter: true,
      sortOrder: sortField === "return_since_inception_pct" ? sortOrder : null,
      render: (_, record) =>
        renderGrowth(record.latest?.return_since_inception_pct),
    },
    {
      title: "最新净值",
      width: 130,
      sorter: true,
      sortOrder: sortField === "unit_nav" ? sortOrder : null,
      render: (_, record) => {
        const v = record.latest?.unit_nav;
        return v != null ? v.toFixed(4) : "-";
      },
    },
    {
      title: "操作",
      key: "action",
      width: 130,
      render: (_, record) => {
        const isFollowed = record.is_followed === true;
        return (
          <Button
            type={isFollowed ? "text" : "primary"}
            icon={isFollowed ? undefined : <PlusOutlined />}
            size="small"
            disabled={isFollowed}
            onClick={() => !isFollowed && handleOpenModal(record)}
          >
            {isFollowed ? "已关注" : "关注"}
          </Button>
        );
      },
    },
  ];

  return (
    <>
      <Card
        bodyStyle={{ padding: 16 }}
        title={
          <Segmented<FundRangeKey>
            value={range}
            options={RANGE_OPTIONS}
            onChange={handleRangeChange}
          />
        }
        extra={
          <Space size={12} wrap>
            <Select
              placeholder="基金类型"
              allowClear
              value={fundType}
              onChange={handleFundTypeChange}
              style={{ width: 130 }}
              options={FUND_TYPE_OPTIONS}
            />
            <Button
              icon={<SearchOutlined />}
              onClick={() => navigate("/fund/search")}
              title="搜索基金"
            >
              搜索
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => handleSearch(1)}>
              刷新
            </Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={sortedList}
          loading={loading}
          pagination={{
            pageSize: 20,
            current: currentPage,
            showQuickJumper: true,
            onChange: (page) => handleSearch(page),
          }}
          scroll={{ y: "72vh" }}
          size="small"
          onChange={handleTableChange}
          locale={{
            emptyText: (
              <div
                style={{
                  padding: "80px 0",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#8c8c8c",
                  fontSize: 14,
                }}
              >
                暂无数据
              </div>
            ),
          }}
        />
      </Card>

      {/* 关注弹窗 */}
      <FollowModal
        visible={modalVisible}
        fund={selectedFund}
        onOk={handleConfirmFollow}
        onCancel={() => setModalVisible(false)}
        loading={followLoading}
      />
    </>
  );
};

export default FundMarket;
