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
import type { ColumnsType } from "antd/es/table";
import type {
  SorterResult,
  TablePaginationConfig,
} from "antd/es/table/interface";
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import type {
  FundRankingItem,
  FundSortKey,
  FundCategoryKey,
  FundPeriodSortKey,
} from "@/types/fund";
import { getFundRanking, followFund } from "@/api/fund";
import FollowModal from "./components/FollowModal";

/**
 * 分类下拉（仅保留开放基金/货币基金；exchange 暂未上线）
 */
const CATEGORY_OPTIONS: { label: string; value: FundCategoryKey }[] = [
  { label: "开放基金", value: "open" },
  { label: "货币基金", value: "money" },
];

/**
 * 开放基金：周期排序选项（Segmented Tab 与 "涨跌幅" 列排序共用）
 */
const PERIOD_OPTIONS: { label: string; value: FundPeriodSortKey }[] = [
  { label: "近一周", value: "1w" },
  { label: "近一月", value: "1m" },
  { label: "近三月", value: "3m" },
  { label: "近六月", value: "6m" },
  { label: "近一年", value: "1y" },
  { label: "近两年", value: "2y" },
  { label: "近三年", value: "3y" },
  { label: "近五年", value: "5y" },
  { label: "今年以来", value: "ytd" },
  { label: "成立来", value: "since_inception" },
];

/**
 * 周期 key -> latest.增长率 字段映射
 */
const PERIOD_GROWTH_FIELD: Record<FundPeriodSortKey, string> = {
  "1w": "return_1w_pct",
  "1m": "return_1m_pct",
  "3m": "return_3m_pct",
  "6m": "return_6m_pct",
  "1y": "return_1y_pct",
  "2y": "return_2y_pct",
  "3y": "return_3y_pct",
  "5y": "return_5y_pct",
  ytd: "return_ytd_pct",
  since_inception: "return_since_inception_pct",
};

/**
 * 开放基金可排序列：表格 column key → 接口 sort 参数值
 */
const OPEN_COLUMN_SORT_KEY: Record<string, FundSortKey> = {
  growth: "1y", // 运行时会根据选中的 PERIOD 动态覆盖
  accumulated_nav: "accumulated_nav",
  unit_nav: "unit_nav",
};

/**
 * 货币基金可排序列：表格 column key → 接口 sort 参数值
 */
const MONEY_COLUMN_SORT_KEY: Record<string, FundSortKey> = {
  annualized_7d: "annualized_7d_pct",
  income_per_10k: "income_per_10k",
};

type SortOrder = "asc" | "desc";

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
 * 表格行数据：由 FundRankingItem 归一化
 */
interface FundRankingTableRow extends FundRankingItem {
  _key: string;
}

const toRankingTableRow = (item: FundRankingItem): FundRankingTableRow => ({
  ...item,
  _key: item.code,
});

interface FundMarketProps {
  onFollowSuccess?: () => void;
}

const FundMarket: React.FC<FundMarketProps> = ({ onFollowSuccess }) => {
  const navigate = useNavigate();

  const [list, setList] = useState<FundRankingTableRow[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState<number>(1);

  const [category, setCategory] = useState<FundCategoryKey>("open");
  /** 周期分段选中的值（只影响"涨跌幅"列排序时的后端 sort 传参） */
  const [period, setPeriod] = useState<FundPeriodSortKey>("1y");
  /** 当前排序列（表格 column key）：growth / accumulated_nav / unit_nav；货币基金排序不对外暴露 */
  const [sortColumn, setSortColumn] = useState<string>("growth");
  const [order, setOrder] = useState<SortOrder>("desc");

  const [modalVisible, setModalVisible] = useState(false);
  const [selectedFund, setSelectedFund] = useState<FundRankingTableRow | null>(
    null,
  );
  const [followLoading, setFollowLoading] = useState(false);

  /**
   * 根据当前排序列 + 周期，推导出传给接口的 sort 值
   */
  const resolveSortKey = useCallback(
    (column: string, currentPeriod: FundPeriodSortKey): FundSortKey => {
      if (category === "money") {
        return (
          (MONEY_COLUMN_SORT_KEY[column] as FundSortKey) ?? "annualized_7d_pct"
        );
      }
      if (column === "growth") return currentPeriod;
      return (OPEN_COLUMN_SORT_KEY[column] as FundSortKey) ?? currentPeriod;
    },
    [category],
  );

  /**
   * 拉取排行榜数据
   */
  const fetchRanking = useCallback(
    async (
      page: number = 1,
      opts?: {
        category?: FundCategoryKey;
        sort?: FundSortKey;
        order?: SortOrder;
      },
    ) => {
      setLoading(true);
      try {
        const nextCategory = opts?.category ?? category;
        const nextSort =
          opts?.sort ??
          (nextCategory === "money"
            ? "1y"
            : resolveSortKey(sortColumn, period));
        const nextOrder = opts?.order ?? order;
        const res = await getFundRanking({
          category: nextCategory,
          sort: nextSort,
          order: nextOrder,
          page,
          limit: 20,
        });
        const raw = res.data;
        const body =
          raw != null && typeof raw === "object"
            ? (raw as {
                items?: FundRankingItem[];
                total?: number;
                page?: number;
              })
            : null;
        const rows = (body?.items ?? []).map(toRankingTableRow);
        if (page === 1) {
          setList(rows);
        } else {
          setList((prev) => [...prev, ...rows]);
        }
        setTotal(body?.total ?? rows.length);
        setCurrentPage(body?.page ?? page);
      } catch (error) {
        console.error(error);
        message.error("基金排行加载失败");
      } finally {
        setLoading(false);
      }
    },
    [category, sortColumn, period, order, resolveSortKey],
  );

  /**
   * 首次加载
   */
  React.useEffect(() => {
    void fetchRanking(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * 切换周期分段（仅开放基金 Tab 区域）
   * - 切换时自动把排序列回到 "growth"，排序方向保持（默认 desc）
   */
  const handlePeriodChange = useCallback(
    (next: FundPeriodSortKey) => {
      setPeriod(next);
      setSortColumn("growth");
      void fetchRanking(1, { sort: next });
    },
    [fetchRanking],
  );

  /**
   * 切换分类（开放/货币）
   */
  const handleCategoryChange = useCallback(
    (next: FundCategoryKey) => {
      setCategory(next);
      if (next === "money") {
        setPeriod("1y");
        setSortColumn("growth");
      }
      void fetchRanking(1, { category: next });
    },
    [fetchRanking],
  );

  /**
   * 表格列点击排序（开放基金：涨跌幅/累计净值/最新净值；货币基金：七日年化/万份收益）
   * - 同列点击：切换 asc / desc
   * - 换列：默认 desc
   * - toggle 效果：点击同一列在升序、降序之间循环切换
   */
  const handleTableChange = useCallback(
    (
      _pagination: TablePaginationConfig,
      _filters: unknown,
      sorter:
        | SorterResult<FundRankingTableRow>
        | SorterResult<FundRankingTableRow>[],
    ) => {
      const first = Array.isArray(sorter) ? sorter[0] : sorter;
      const columnKey =
        typeof first?.columnKey === "string"
          ? first.columnKey
          : (first?.field as string | undefined);
      const nextOrderRaw = first?.order as "ascend" | "descend" | undefined;

      if (!columnKey) return;

      const isMoney = category === "money";
      const sortKeyMap = isMoney ? MONEY_COLUMN_SORT_KEY : OPEN_COLUMN_SORT_KEY;

      if (!sortKeyMap[columnKey]) return; // 非排序列，忽略

      // 如果点击的是当前排序列，且 order 变为 undefined（Ant Design 三态循环到默认），
      // 则手动切换排序方向以实现 toggle 效果
      let nextOrder: SortOrder;
      if (columnKey === sortColumn && nextOrderRaw == null) {
        nextOrder = order === "desc" ? "asc" : "desc";
      } else if (!nextOrderRaw) {
        // 新列默认降序
        nextOrder = "desc";
      } else {
        nextOrder = nextOrderRaw === "ascend" ? "asc" : "desc";
      }

      if (isMoney) {
        const nextSort = sortKeyMap[columnKey] as FundSortKey;
        setSortColumn(columnKey);
        setOrder(nextOrder);
        void fetchRanking(1, {
          category: "money",
          sort: nextSort,
          order: nextOrder,
        });
      } else {
        const nextSort =
          columnKey === "growth"
            ? period
            : (sortKeyMap[columnKey] as FundSortKey);
        setSortColumn(columnKey);
        setOrder(nextOrder);
        void fetchRanking(1, { sort: nextSort, order: nextOrder });
      }
    },
    [category, period, fetchRanking, sortColumn, order],
  );

  const handleOpenModal = (fund: FundRankingTableRow) => {
    if (fund.is_in_watchlist) return;
    setSelectedFund(fund);
    setModalVisible(true);
  };

  const handleConfirmFollow = async (remark: string) => {
    if (!selectedFund) return;
    setFollowLoading(true);
    try {
      await followFund({ fund_code: selectedFund.code, remark });
      setList((prev) =>
        prev.map((item) =>
          item.code === selectedFund.code
            ? { ...item, is_in_watchlist: true }
            : item,
        ),
      );
      message.success("关注成功");
      setModalVisible(false);
      onFollowSuccess?.();
    } catch {
      message.error("关注失败，请重试");
    } finally {
      setFollowLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    void fetchRanking(page);
  };

  /* ----------------- 开放基金列 ----------------- */

  const openGrowthField = PERIOD_GROWTH_FIELD[period];

  /** antd Table 需要：当前排序列 + order */
  const currentTableOrder = order === "asc" ? "ascend" : "descend";
  const currentTableOrderForColumn = (key: string) => {
    if (sortColumn === key) return currentTableOrder;
    return null;
  };

  const openColumns: ColumnsType<FundRankingTableRow> = [
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
      title: "涨跌幅",
      key: "growth",
      dataIndex: "growth",
      width: 130,
      sorter: true,
      sortOrder: sortColumn === "growth" ? currentTableOrder : null,
      render: (_, record) =>
        renderGrowth(
          record.latest?.[openGrowthField as keyof typeof record.latest] as
            | number
            | string
            | null
            | undefined,
        ),
    },
    {
      title: "累计净值",
      key: "accumulated_nav",
      dataIndex: "accumulated_nav",
      width: 130,
      sorter: true,
      sortOrder: sortColumn === "accumulated_nav" ? currentTableOrder : null,
      render: (_, record) => {
        const v = record.latest?.accumulated_nav;
        return v != null ? v.toFixed(4) : "-";
      },
    },
    {
      title: "最新净值",
      key: "unit_nav",
      dataIndex: "unit_nav",
      width: 130,
      sorter: true,
      sortOrder: sortColumn === "unit_nav" ? currentTableOrder : null,
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
        const isFollowed = record.is_in_watchlist === true;
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

  /* ----------------- 货币基金列 ----------------- */

  const moneyColumns: ColumnsType<FundRankingTableRow> = [
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
      title: "七日年化",
      key: "annualized_7d",
      dataIndex: "annualized_7d_pct",
      width: 130,
      sorter: true,
      sortOrder: currentTableOrderForColumn("annualized_7d"),
      render: (_, record) => {
        const v = record.latest?.annualized_7d_pct;
        const num = toNumber(v);
        if (num == null) return "-";
        return (
          <span style={{ fontWeight: 600, color: "#000" }}>
            {num.toFixed(4)}%
          </span>
        );
      },
    },
    {
      title: "万份收益",
      key: "income_per_10k",
      dataIndex: "income_per_10k",
      width: 130,
      sorter: true,
      sortOrder: currentTableOrderForColumn("income_per_10k"),
      render: (_, record) => {
        const v = record.latest?.income_per_10k;
        const num = toNumber(v);
        if (num == null) return "-";
        return (
          <span style={{ fontWeight: 600, color: "#000" }}>
            {num.toFixed(4)}
          </span>
        );
      },
    },
    {
      title: "操作",
      key: "action",
      width: 130,
      render: (_, record) => {
        const isFollowed = record.is_in_watchlist === true;
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

  const columns = useMemo(
    () => (category === "money" ? moneyColumns : openColumns),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [category, sortColumn, order, period],
  );

  const showPeriodTabs = category !== "money";

  return (
    <>
      <Card
        bodyStyle={{ padding: 16 }}
        title={
          showPeriodTabs ? (
            <Segmented<FundPeriodSortKey>
              value={period}
              options={PERIOD_OPTIONS}
              onChange={handlePeriodChange}
            />
          ) : (
            <span style={{ color: "#1d2129", fontWeight: 600, fontSize: 16 }}>
              货币基金
            </span>
          )
        }
        extra={
          <Space size={12} wrap>
            <Select<FundCategoryKey>
              placeholder="基金分类"
              value={category}
              onChange={handleCategoryChange}
              style={{ width: 140 }}
              options={CATEGORY_OPTIONS}
            />
            <Button
              icon={<SearchOutlined />}
              onClick={() => navigate("/fund/search")}
              title="搜索基金"
            >
              搜索
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => fetchRanking(1)}>
              刷新
            </Button>
          </Space>
        }
      >
        <Table<FundRankingTableRow>
          rowKey="_key"
          columns={columns}
          dataSource={list}
          loading={loading}
          pagination={{
            pageSize: 20,
            current: currentPage,
            total,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: handlePageChange,
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
        fund={
          selectedFund
            ? {
                code: selectedFund.code,
                name: selectedFund.name,
              }
            : null
        }
        onOk={handleConfirmFollow}
        onCancel={() => setModalVisible(false)}
        loading={followLoading}
      />
    </>
  );
};

export default FundMarket;
