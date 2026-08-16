// src/pages/Fund/components/FundTable.tsx
import React from "react";
import { Table, Tag, Button, Tooltip } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { Link } from "react-router-dom";
import dayjs from "dayjs";
import type { FundTableRow } from "@/types/fund";

/**
 * 数字转换工具
 */
const toNumber = (v: unknown): number | null => {
  if (v == null || v === "") return null;
  const n = typeof v === "string" ? parseFloat(v) : (v as number);
  return Number.isFinite(n) ? n : null;
};

/**
 * 格式化增长率显示
 */
const renderGrowth = (v: unknown, digits = 2) => {
  const num = toNumber(v);
  if (num == null) return "-";
  const color = num > 0 ? "#f5222d" : num < 0 ? "#52c41a" : "inherit";
  return (
    <span style={{ color, fontWeight: 600 }}>
      {num > 0 ? "+" : ""}
      {num.toFixed(digits)}%
    </span>
  );
};

/**
 * FundTable 组件属性
 */
interface FundTableProps {
  /** 数据源 */
  data: FundTableRow[];
  /** 加载状态 */
  loading?: boolean;
  /** 空数据提示文字 */
  emptyText?: string;
  /** 是否显示备注列 */
  showRemark?: boolean;
  /** 是否显示操作列（关注/取消关注） */
  showAction?: boolean;
  /** 关注按钮点击回调 */
  onFollow?: (record: FundTableRow) => void;
  /** 取消关注按钮点击回调 */
  onUnfollow?: (record: FundTableRow) => void;
  /** 分页配置 */
  pagination?: {
    pageSize?: number;
    current?: number;
    total?: number;
    onChange?: (page: number) => void;
    showQuickJumper?: boolean;
  };
  /** 横向滚动宽度 */
  scrollX?: number;
  /** 纵向滚动高度 */
  scrollY?: string;
}

/**
 * 基金表格组件 - 可复用于搜索结果和关注列表
 *
 * 支持展示：基金名称、净值、累计净值、日增长、近一周、近一月、近三月、近六月、近一年、今年以来、成立来等
 * 支持操作：关注/取消关注
 */
const FundTable: React.FC<FundTableProps> = ({
  data,
  loading = false,
  emptyText = "暂无数据",
  showRemark = false,
  showAction = true,
  onFollow,
  onUnfollow,
  pagination,
  scrollX,
  scrollY = "72vh",
}) => {
  const columns: ColumnsType<FundTableRow> = [
    {
      title: "基金名称",
      width: 290,
      fixed: "left",
      render: (_, record) => {
        const latestDate = record.latest?.data_date ?? record.last_seen_data_date;
        return (
          <Link
            to={`/fund/detail/${record.code ?? ""}`}
            style={{
              display: "block",
              color: "inherit",
              textDecoration: "none",
            }}
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
                flexWrap: "wrap",
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
              {latestDate ? (
                <span style={{ color: "#8c8c8c" }}>
                  {dayjs(latestDate).format("MM-DD")}
                </span>
              ) : null}
            </div>
          </Link>
        );
      },
    },
    {
      title: "单位净值",
      width: 130,
      render: (_, record) => {
        const v = record.latest?.unit_nav;
        return v != null ? (
          <Tooltip
            title={
              record.latest?.data_date
                ? `净值日期：${record.latest.data_date}`
                : undefined
            }
          >
            <span style={{ fontWeight: 600, color: "#000" }}>{v.toFixed(4)}</span>
          </Tooltip>
        ) : (
          "-"
        );
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
      title: "日增长",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.latest?.daily_growth_pct),
    },
    {
      title: "近一周",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.latest?.return_1w_pct),
    },
    {
      title: "近一月",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.latest?.return_1m_pct),
    },
    {
      title: "近三月",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.latest?.return_3m_pct),
    },
    {
      title: "近六月",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.latest?.return_6m_pct),
    },
    {
      title: "近一年",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.latest?.return_1y_pct),
    },
    {
      title: "今年以来",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.latest?.return_ytd_pct),
    },
    {
      title: "成立来",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.latest?.return_since_inception_pct),
    },
  ];

  if (showRemark) {
    columns.push({ title: "备注", width: 140, dataIndex: "remark" });
  }

  if (showAction) {
    columns.push({
      title: "操作",
      key: "action",
      width: 120,
      fixed: "right",
      render: (_, record) => {
        const isFollowed = record.is_followed === true;
        if (isFollowed) {
          return (
            <Button
              type="link"
              danger
              size="small"
              onClick={() => onUnfollow?.(record)}
            >
              取消关注
            </Button>
          );
        }
        return (
          <Button
            type="primary"
            size="small"
            icon={<PlusOutlined />}
            onClick={() => onFollow?.(record)}
          >
            关注
          </Button>
        );
      },
    });
  }

  // 计算横向滚动宽度
  const defaultScrollX = showRemark ? 1520 : showAction ? 1380 : 1260;
  const finalScrollX = scrollX ?? defaultScrollX;

  // 有数据时才设置纵向滚动，避免空数据时出现空白滚动条
  const finalScrollY = data.length > 0 ? scrollY : undefined;

  return (
    <Table<FundTableRow>
      rowKey="id"
      columns={columns}
      dataSource={data}
      loading={loading}
      pagination={pagination}
      scroll={{ x: finalScrollX, y: finalScrollY }}
      size="small"
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
            {emptyText}
          </div>
        ),
      }}
    />
  );
};

export default FundTable;