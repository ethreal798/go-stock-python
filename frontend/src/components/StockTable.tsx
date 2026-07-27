import React from "react";
import { Table, Tag, Button, Space, Tooltip, Popconfirm } from "antd";
import {
  DeleteOutlined,
  LineChartOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import type { Stock, StockPrice } from "@/types/stock";

interface StockTableProps {
  stocks: Stock[];
  prices: Record<string, StockPrice>;
  loading?: boolean;
  onDelete?: (code: string) => void;
  onViewChart?: (stock: Stock) => void;
  isGuestMode?: boolean;
}

const formatNumber = (v: number, digits = 2) =>
  v == null ? "-" : v.toFixed(digits);

const formatAmount = (v: number): string => {
  if (v == null) return "-";
  if (v >= 1e8) return `${(v / 1e8).toFixed(2)}亿`;
  if (v >= 1e4) return `${(v / 1e4).toFixed(2)}万`;
  return v.toFixed(0);
};

const ChangeCell: React.FC<{ value: number; suffix?: string }> = ({
  value,
  suffix = "%",
}) => {
  if (value == null) return <span>-</span>;
  const isUp = value >= 0;
  return (
    <span style={{ color: isUp ? "#f5222d" : "#52c41a", fontWeight: 600 }}>
      {isUp ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
      {Math.abs(value).toFixed(2)}
      {suffix}
    </span>
  );
};

const StockTable: React.FC<StockTableProps> = ({
  stocks,
  prices,
  loading,
  onDelete,
  onViewChart,
  isGuestMode,
}) => {
  const columns: ColumnsType<Stock> = [
    {
      title: "代码",
      dataIndex: "code",
      width: 90,
      fixed: "left",
      render: (code: string, record) => (
        <Space size={4}>
          <span style={{ fontFamily: "monospace", fontWeight: 600 }}>
            {code}
          </span>
          {record.market && (
            <Tag style={{ fontSize: 10, padding: "0 3px", lineHeight: "16px" }}>
              {record.market}
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: "名称",
      dataIndex: "name",
      width: 100,
      fixed: "left",
      render: (name: string, record) => {
        const p = prices[record.code];
        return <span>{p?.name ?? name}</span>;
      },
    },
    {
      title: "现价",
      key: "price",
      width: 90,
      render: (_, record) => {
        const p = prices[record.code];
        return p ? (
          <span style={{ fontWeight: 700, fontSize: 15 }}>
            {formatNumber(p.price)}
          </span>
        ) : (
          "-"
        );
      },
    },
    {
      title: "涨跌幅",
      key: "changeRate",
      width: 90,
      sorter: (a, b) =>
        (prices[a.code]?.changeRate ?? 0) - (prices[b.code]?.changeRate ?? 0),
      render: (_, record) => {
        const p = prices[record.code];
        return p ? <ChangeCell value={p.changeRate} /> : "-";
      },
    },
    {
      title: "涨跌额",
      key: "change",
      width: 80,
      render: (_, record) => {
        const p = prices[record.code];
        return p ? <ChangeCell value={p.change} suffix="" /> : "-";
      },
    },
    {
      title: "成交量",
      key: "volume",
      width: 90,
      render: (_, record) => {
        const p = prices[record.code];
        return p ? formatAmount(p.volume) : "-";
      },
    },
    {
      title: "成交额",
      key: "amount",
      width: 100,
      render: (_, record) => {
        const p = prices[record.code];
        return p ? formatAmount(p.amount) : "-";
      },
    },
    {
      title: "今开",
      key: "open",
      width: 80,
      render: (_, record) => {
        const p = prices[record.code];
        return p ? formatNumber(p.open) : "-";
      },
    },
    {
      title: "最高",
      key: "high",
      width: 80,
      render: (_, record) => {
        const p = prices[record.code];
        return p ? (
          <span style={{ color: "#f5222d" }}>{formatNumber(p.high)}</span>
        ) : (
          "-"
        );
      },
    },
    {
      title: "最低",
      key: "low",
      width: 80,
      render: (_, record) => {
        const p = prices[record.code];
        return p ? (
          <span style={{ color: "#52c41a" }}>{formatNumber(p.low)}</span>
        ) : (
          "-"
        );
      },
    },
    {
      title: "换手率",
      key: "turnover",
      width: 80,
      render: (_, record) => {
        const p = prices[record.code];
        return p?.turnover != null ? `${formatNumber(p.turnover)}%` : "-";
      },
    },
    {
      title: "分组",
      dataIndex: "group",
      width: 80,
      render: (v: string) => (v ? <Tag color="cyan">{v}</Tag> : null),
    },
    {
      title: "操作",
      key: "actions",
      width: 100,
      fixed: "right",
      render: (_, record) => (
        <Space size={4}>
          {onViewChart && (
            <Tooltip title="查看K线">
              <Button
                size="small"
                icon={<LineChartOutlined />}
                onClick={() => onViewChart(record)}
              />
            </Tooltip>
          )}
          {onDelete && (
            <Popconfirm
              title={`确定从自选股中删除 ${record.name ?? record.code}？`}
              onConfirm={() => onDelete(record.code)}
              disabled={isGuestMode}
            >
              <Tooltip title={isGuestMode ? "请登录后使用删除功能" : "删除"}>
                <Button
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  disabled={isGuestMode}
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Table
      rowKey="code"
      columns={columns}
      dataSource={stocks}
      loading={loading}
      pagination={{
        pageSize: 50,
        showSizeChanger: true,
        showQuickJumper: true,
      }}
      size="small"
      scroll={{ x: 1100 }}
      rowClassName={(record) => {
        const p = prices[record.code];
        if (!p) return "";
        if (p.changeRate > 0) return "row-up";
        if (p.changeRate < 0) return "row-down";
        return "";
      }}
    />
  );
};

export default StockTable;
