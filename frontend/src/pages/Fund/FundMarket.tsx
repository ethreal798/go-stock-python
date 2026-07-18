// src/pages/Fund/FundMarket.tsx
import React, { useState, useCallback } from "react";
import { Card, Table, Tag, Button, Input, Space, message } from "antd";
import { ReloadOutlined, PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import type { SearchFund } from "@/types";
import { searchFund, followFund } from "@/api/fund";
import FollowModal from "./components/FollowModal";

const { Search } = Input;

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
      {num >= 0 ? "+" : ""}{num.toFixed(2)}%
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
  // 搜索结果列表
  const [list, setList] = useState<SearchFund[]>([]);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 搜索关键词
  const [searchKeyword, setSearchKeyword] = useState("");
  // 当前页码
  const [currentPage, setCurrentPage] = useState(1);

  // 弹窗相关状态
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedFund, setSelectedFund] = useState<SearchFund | null>(null);
  const [followLoading, setFollowLoading] = useState(false);

  /**
   * 搜索基金
   * @param keyword 搜索关键词
   * @param page 页码，默认第1页
   */
  const handleSearch = useCallback(
    async (keyword: string, page: number = 1) => {
      if (!keyword.trim()) {
        setList([]);
        return;
      }
      setLoading(true);
      try {
        const res = await searchFund({ keyword, page, limit: 20 });
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
    []
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
          item.code === selectedFund.code ? { ...item, is_followed: true } : item
        )
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

  /**
   * 表格列配置
   */
  const columns: ColumnsType<SearchFund> = [
    { title: "基金代码", dataIndex: "code", width: 80 },
    { title: "基金名称", dataIndex: "name", width: 150, ellipsis: true },
    { title: "类型", dataIndex: "type", width: 100, render: (v) => v ? <Tag>{v}</Tag> : "-" },
    { title: "净值", dataIndex: "nav", width: 100, render: (v) => v != null ? v.toFixed(4) : "-" },
    { title: "累计净值", dataIndex: "acc_nav", width: 100, render: (v) => v != null ? v.toFixed(4) : "-" },
    { title: "日增长", dataIndex: "day_growth", width: 100, render: renderGrowth },
    { title: "近一月", dataIndex: "month_growth", width: 100, render: renderGrowth },
    { title: "近三月", dataIndex: "three_month_growth", width: 100, render: renderGrowth },
    { title: "近六月", dataIndex: "six_month_growth", width: 100, render: renderGrowth },
    { title: "今年", dataIndex: "current_year_growth", width: 100, render: renderGrowth },
    {
      title: "操作", key: "action", width: 100, fixed: "right",
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
        title="基金市场"
        bodyStyle={{ padding: 16 }}
        extra={
          <Space>
            <Search
              placeholder="搜索基金代码/名称"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onSearch={(v) => handleSearch(v, 1)}
              style={{ width: 300 }}
              enterButton
            />
            <Button icon={<ReloadOutlined />} onClick={() => handleSearch(searchKeyword, 1)}>
              刷新
            </Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={list}
          loading={loading}
          pagination={{
            pageSize: 20,
            current: currentPage,
            showQuickJumper: true,
            onChange: (page) => handleSearch(searchKeyword, page),
          }}
          scroll={{ x: 1400, y: TABLE_SCROLL_Y }}
          size="small"
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