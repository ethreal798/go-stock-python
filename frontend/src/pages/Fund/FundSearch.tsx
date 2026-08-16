// src/pages/Fund/FundSearch.tsx
import React, { useState, useCallback } from "react";
import { Card, Input, Space, Button, message } from "antd";
import { ReloadOutlined, ArrowLeftOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import FundTable from "./components/FundTable";
import type { FundTableRow, FollowFundInfo } from "@/types/fund";
import { searchFund, followFund } from "@/api/fund";

const { Search } = Input;

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

const FundSearch: React.FC = () => {
  const navigate = useNavigate();

  const [list, setList] = useState<FundTableRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(
    async (keyword: string, page: number = 1) => {
      if (!keyword.trim()) {
        setList([]);
        setHasSearched(false);
        return;
      }
      setLoading(true);
      setHasSearched(true);
      try {
        const res = await searchFund({
          keyword,
          page,
          limit: 20,
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
    [],
  );

  const handleFollow = useCallback(
    async (record: FundTableRow) => {
      try {
        await followFund({ fund_code: record.code });
        setList((prev) =>
          prev.map((item) =>
            item.code === record.code
              ? { ...item, is_followed: true }
              : item,
          ),
        );
        message.success("关注成功");
      } catch {
        // ignore
      }
    },
    [],
  );

  const handleBack = () => {
    navigate(-1);
  };

  return (
    <>
      <Card
        bodyStyle={{ padding: 16 }}
        title={
          <Space>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={handleBack}
              type="text"
            />
            <span style={{ fontSize: 16, fontWeight: 600 }}>搜索基金</span>
          </Space>
        }
        extra={
          <Space size={12} wrap>
            <Search
              placeholder="搜索基金代码/名称"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onSearch={(v) => handleSearch(v, 1)}
              style={{ width: 300 }}
              enterButton
              autoFocus
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={() => handleSearch(searchKeyword, 1)}
              disabled={!searchKeyword.trim()}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <FundTable
          data={list}
          loading={loading}
          showRemark={false}
          showAction={true}
          onFollow={handleFollow}
          emptyText={
            hasSearched && searchKeyword.trim()
              ? `未找到与「${searchKeyword}」相关的基金`
              : "请输入基金代码或名称搜索"
          }
          pagination={{
            pageSize: 20,
            current: currentPage,
            showQuickJumper: true,
            onChange: (page) => handleSearch(searchKeyword, page),
          }}
        />
      </Card>
    </>
  );
};

export default FundSearch;