// src/pages/Fund/FundMarket.tsx
import React, { useState, useCallback, useMemo } from "react";
import {
  Card,
  Table,
  Tag,
  Button,
  Input,
  Space,
  Segmented,
  Select,
  message,
} from "antd";
import { ReloadOutlined, PlusOutlined } from "@ant-design/icons";
import { Link } from "react-router-dom";
import type { ColumnsType } from "antd/es/table";
import type { SearchFund } from "@/types/fund";
import { searchFund, followFund } from "@/api/fund";
import type { FundRangeKey } from "@/api/fund";
import FollowModal from "./components/FollowModal";

const { Search } = Input;

const TABLE_SCROLL_Y = "calc(100vh - 200px)";

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

const RANGE_FIELD: Record<FundRangeKey, keyof SearchFund> = {
  day: "day_growth",
  week: "week_growth",
  month: "month_growth",
  three_month: "three_month_growth",
  six_month: "six_month_growth",
  year: "current_year_growth",
  two_year: "two_year_growth",
  three_year: "three_year_growth",
  five_year: "five_year_growth",
};

const toNumber = (v: unknown): number | null => {
  if (v == null || v === "") return null;
  const num = typeof v === "string" ? parseFloat(v) : (v as number);
  return Number.isFinite(num) ? num : null;
};

/**
 * 格式化增长率显示
 * @param v 增长率值
 * @returns 格式化后的显示文本
 */
const renderGrowth = (v: string | number | null | undefined) => {
  const num = toNumber(v);
  if (num == null) return "-";
  return (
    <span style={{ color: num >= 0 ? "#f5222d" : "#52c41a", fontWeight: 600 }}>
      {num >= 0 ? "+" : ""}
      {num.toFixed(2)}%
    </span>
  );
};

/**
 * 基金市场页面属性
 */
interface FundMarketProps {
  /** 关注成功后的回调
   * 用于通知父组件刷新关注列表
   */
  onFollowSuccess?: () => void;
}

/**
 * 基金市场页面
 * 支持搜索基金、查看基金列表、添加关注
 */
const FundMarket: React.FC<FundMarketProps> = ({ onFollowSuccess }) => {
  const [list, setList] = useState<SearchFund[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [range, setRange] = useState<FundRangeKey>("day");
  const [fundType, setFundType] = useState<string | undefined>(undefined);

  const [sortField, setSortField] = useState<keyof SearchFund | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder | null>(null);

  const [modalVisible, setModalVisible] = useState(false);
  const [selectedFund, setSelectedFund] = useState<SearchFund | null>(null);
  const [followLoading, setFollowLoading] = useState(false);

  const growthField = RANGE_FIELD[range];

  const handleSearch = useCallback(
    async (
      keyword: string,
      page: number = 1,
      currentRange?: FundRangeKey,
      currentFundType?: string | undefined,
    ) => {
      if (!keyword.trim()) {
        setList([]);
        return;
      }
      setLoading(true);
      try {
        const res = await searchFund({
          keyword,
          page,
          limit: 20,
          range: currentRange ?? range,
          fund_type: currentFundType ?? fundType,
        });
        const data = res.data || [];
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
      void handleSearch(searchKeyword, 1, next, fundType);
    },
    [handleSearch, searchKeyword, fundType],
  );

  const handleFundTypeChange = useCallback(
    (next: string | undefined) => {
      setFundType(next);
      void handleSearch(searchKeyword, 1, range, next);
    },
    [handleSearch, searchKeyword, range],
  );

  /**
   * 打开关注弹窗
   * @param fund 要关注的基金
   */
  const handleOpenModal = (fund: SearchFund) => {
    if (fund.is_followed) return;
    setSelectedFund(fund);
    setModalVisible(true);
  };

  /**
   * 确认添加关注
   * @param remark 备注
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
      const av = toNumber(a[sortField]);
      const bv = toNumber(b[sortField]);
      const an = av ?? 0;
      const bn = bv ?? 0;
      return sortOrder === "ascend" ? an - bn : bn - an;
    });
    return sorted;
  }, [list, sortField, sortOrder]);

  const handleTableChange = (
    _pagination: unknown,
    _filters: unknown,
    sorter: unknown,
  ) => {
    const s = sorter as
      | { field?: keyof SearchFund | null; order?: SortOrder | null }
      | { field?: keyof SearchFund | null; order?: SortOrder | null }[];
    const first = Array.isArray(s) ? s[0] : s;
    const field = first?.field ?? null;
    const order = first?.order ?? null;
    setSortField(field);
    setSortOrder(order);
  };

  const columns: ColumnsType<SearchFund> = [
    {
      title: "基金代码",
      dataIndex: "code",
      width: 90,
      render: (v: string, record) => (
        <Link to={`/fund/detail/${record.code}`} style={{ color: "#1677ff" }}>
          {v}
        </Link>
      ),
    },
    {
      title: "基金名称",
      dataIndex: "name",
      width: 180,
      ellipsis: true,
      render: (v: string, record) => (
        <Link to={`/fund/detail/${record.code}`} style={{ color: "#000" }}>
          {v}
        </Link>
      ),
    },
    {
      title: "类型",
      dataIndex: "type",
      width: 100,
      render: (v) => (v ? <Tag>{v}</Tag> : "-"),
    },
    {
      title: "净值",
      dataIndex: "nav",
      width: 100,
      render: (v) => (v != null ? v.toFixed(4) : "-"),
    },
    {
      title: "累计净值",
      dataIndex: "acc_nav",
      width: 110,
      render: (v) => (v != null ? v.toFixed(4) : "-"),
    },
    {
      title: "涨跌幅",
      dataIndex: growthField,
      width: 110,
      sorter: true,
      sortOrder: sortField === growthField ? sortOrder : null,
      render: renderGrowth,
    },
    {
      title: "夏普比率",
      dataIndex: "sharpe_ratio",
      width: 110,
      sorter: true,
      sortOrder: sortField === "sharpe_ratio" ? sortOrder : null,
      render: (v) => {
        const num = toNumber(v);
        return num == null ? "-" : num.toFixed(3);
      },
    },
    {
      title: "最大回撤",
      dataIndex: "max_drawdown",
      width: 110,
      sorter: true,
      sortOrder: sortField === "max_drawdown" ? sortOrder : null,
      render: (v) => {
        const num = toNumber(v);
        return num == null ? "-" : `${num.toFixed(2)}%`;
      },
    },
    {
      title: "最新净值",
      dataIndex: "latest_nav",
      width: 110,
      sorter: true,
      sortOrder: sortField === "latest_nav" ? sortOrder : null,
      render: (v) => (v != null ? v.toFixed(4) : "-"),
    },
    {
      title: "操作",
      key: "action",
      width: 100,
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
            <Search
              placeholder="搜索基金代码/名称"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onSearch={(v) => handleSearch(v, 1)}
              style={{ width: 300 }}
              enterButton
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={() => handleSearch(searchKeyword, 1)}
            >
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
            onChange: (page) => handleSearch(searchKeyword, page),
          }}
          scroll={{ x: 1200, y: TABLE_SCROLL_Y }}
          size="small"
          onChange={handleTableChange}
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
