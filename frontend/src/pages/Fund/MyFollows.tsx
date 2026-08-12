// src/pages/Fund/MyFollows.tsx
import React, { useState, useEffect, useCallback } from "react";
import { Card, Table, Tag, Button, message } from "antd";
import { Link } from "react-router-dom";
import type { ColumnsType } from "antd/es/table";
import type { FollowFund } from "@/types/fund";
import { getFollowedFunds, unfollowFund } from "@/api/fund";

const TABLE_SCROLL_Y = "calc(100vh - 200px)";

/**
 * 格式化增长率显示
 * @param v 增长率值
 * @returns 格式化后的显示文本
 */
const renderGrowth = (v: string | number | null | undefined) => {
  if (v == null || v === "") return "-";
  const num = typeof v === "string" ? parseFloat(v) : v;
  if (isNaN(num)) return "-";
  return (
    <span style={{ color: num >= 0 ? "#f5222d" : "#52c41a", fontWeight: 600 }}>
      {num >= 0 ? "+" : ""}
      {num.toFixed(2)}%
    </span>
  );
};

/**
 * 我的关注页面
 * 展示用户已关注的基金列表，支持取消关注
 */
const MyFollows: React.FC = () => {
  // 关注列表数据
  const [list, setList] = useState<FollowFund[]>([]);
  // 加载状态
  const [loading, setLoading] = useState(false);

  /**
   * 获取关注列表
   */
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

  /**
   * 取消关注
   * @param fundCode 基金代码
   */
  const handleUnfollow = useCallback(
    async (fundCode: string) => {
      try {
        await unfollowFund(fundCode);
        message.success("已取消关注");
        // 重新获取列表
        fetchList();
      } catch {
        // ignore
      }
    },
    [fetchList],
  );

  // 页面加载时获取关注列表
  useEffect(() => {
    fetchList();
  }, [fetchList]);

  /**
   * 表格列配置
   */
  const columns: ColumnsType<FollowFund> = [
    {
      title: "基金代码",
      width: 90,
      render: (_, record) =>
        record.fund_info?.code ? (
          <Link
            to={`/fund/detail/${record.fund_info.code}`}
            style={{ color: "#1677ff" }}
          >
            {record.fund_info.code}
          </Link>
        ) : (
          "-"
        ),
    },
    {
      title: "基金名称",
      width: 170,
      ellipsis: true,
      render: (_, record) =>
        record.fund_info?.name ? (
          <Link
            to={`/fund/detail/${record.fund_info.code}`}
            style={{ color: "#000" }}
          >
            {record.fund_info.name}
          </Link>
        ) : (
          "-"
        ),
    },
    {
      title: "类型",
      width: 100,
      render: (_, record) =>
        record.fund_info?.type ? <Tag>{record.fund_info.type}</Tag> : "-",
    },
    {
      title: "净值",
      width: 100,
      render: (_, record) =>
        record.fund_info?.nav != null ? record.fund_info.nav.toFixed(4) : "-",
    },
    {
      title: "累计净值",
      width: 100,
      render: (_, record) =>
        record.fund_info?.acc_nav != null
          ? record.fund_info.acc_nav.toFixed(4)
          : "-",
    },
    {
      title: "日增长",
      width: 100,
      render: (_, record) => renderGrowth(record.fund_info?.day_growth),
    },
    {
      title: "近一周",
      width: 100,
      render: (_, record) => renderGrowth(record.fund_info?.week_growth),
    },
    {
      title: "近一月",
      width: 100,
      render: (_, record) => renderGrowth(record.fund_info?.month_growth),
    },
    {
      title: "近三月",
      width: 100,
      render: (_, record) => renderGrowth(record.fund_info?.three_month_growth),
    },
    {
      title: "近六月",
      width: 100,
      render: (_, record) => renderGrowth(record.fund_info?.six_month_growth),
    },
    {
      title: "今年",
      width: 100,
      render: (_, record) =>
        renderGrowth(record.fund_info?.current_year_growth),
    },
    { title: "备注", width: 100, dataIndex: "remark" },
    {
      title: "操作",
      key: "action",
      width: 100,
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
        scroll={{ x: 1600, y: TABLE_SCROLL_Y }}
        size="small"
      />
    </Card>
  );
};

export default MyFollows;
