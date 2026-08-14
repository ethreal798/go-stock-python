// src/pages/Fund/MyFollows.tsx
import React, { useState, useEffect, useCallback } from "react";
import { Card, Table, Tag, Button, message, Tooltip } from "antd";
import type { ColumnsType } from "antd/es/table";
import { Link } from "react-router-dom";
import type { FollowFund } from "@/types/fund";
import { getFollowedFunds, unfollowFund } from "@/api/fund";
import dayjs from "dayjs";

const toNumber = (v: unknown): number | null => {
  if (v == null || v === "") return null;
  const n = typeof v === "string" ? parseFloat(v) : (v as number);
  return Number.isFinite(n) ? n : null;
};

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

const MyFollows: React.FC = () => {
  const [list, setList] = useState<FollowFund[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchList = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getFollowedFunds();
      setList(res.data || []);
    } catch {
      // 网络错误统一由 api/index.ts 处理
    } finally {
      setLoading(false);
    }
  }, []);

  const handleUnfollow = useCallback(
    async (fundCode: string) => {
      try {
        await unfollowFund(fundCode);
        message.success("已取消关注");
        fetchList();
      } catch {
        // ignore
      }
    },
    [fetchList],
  );

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  const columns: ColumnsType<FollowFund> = [
    {
      title: "基金名称",
      width: 290,
      fixed: "left",
      render: (_, record) => {
        const info = record.fund_info;
        if (!info) return "-";
        const latestDate = info.latest?.data_date ?? info.last_seen_data_date;
        return (
          <Link
            to={`/fund/detail/${info.code ?? ""}`}
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
              {info.name ?? "-"}
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
              {info.code ? (
                <span style={{ color: "#1677ff" }}>{info.code}</span>
              ) : null}
              {info.type ? (
                <Tag style={{ margin: 0, fontSize: 12, padding: "0 6px" }}>
                  {info.type}
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
        const v = record.fund_info?.latest?.unit_nav;
        return v != null ? (
          <Tooltip
            title={
              record.fund_info?.latest?.data_date
                ? `净值日期：${record.fund_info.latest.data_date}`
                : undefined
            }
          >
            <span style={{ fontWeight: 600, color: "#000" }}>
              {v.toFixed(4)}
            </span>
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
        const v = record.fund_info?.latest?.accumulated_nav;
        return v != null ? v.toFixed(4) : "-";
      },
    },
    {
      title: "日增长",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.fund_info?.latest?.daily_growth_pct),
    },
    {
      title: "近一周",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.fund_info?.latest?.return_1w_pct),
    },
    {
      title: "近一月",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.fund_info?.latest?.return_1m_pct),
    },
    {
      title: "近三月",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.fund_info?.latest?.return_3m_pct),
    },
    {
      title: "近六月",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.fund_info?.latest?.return_6m_pct),
    },
    {
      title: "近一年",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.fund_info?.latest?.return_1y_pct),
    },
    {
      title: "今年以来",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.fund_info?.latest?.return_ytd_pct),
    },
    {
      title: "成立来",
      width: 120,
      render: (_, record) =>
        renderGrowth(record.fund_info?.latest?.return_since_inception_pct),
    },
    { title: "备注", width: 140, dataIndex: "remark" },
    {
      title: "操作",
      key: "action",
      width: 110,
      fixed: "right",
      render: (_, record) => (
        <Button
          type="link"
          danger
          size="small"
          onClick={() => handleUnfollow(record.fund_code)}
        >
          取消关注
        </Button>
      ),
    },
  ];

  return (
    <Card title="我的关注" bodyStyle={{ padding: 16 }}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={list}
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 1800, y: "72vh" }}
        size="small"
        locale={{
          emptyText: (
            <div
              style={{
                height: "72vh",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#8c8c8c",
                fontSize: 14,
              }}
            >
              暂无关注的基金
            </div>
          ),
        }}
      />
    </Card>
  );
};

export default MyFollows;
