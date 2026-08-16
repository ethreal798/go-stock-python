// src/pages/Fund/MyFollows.tsx
import React, { useState, useEffect, useCallback } from "react";
import { Card, message } from "antd";
import FundTable from "./components/FundTable";
import type { FundTableRow, FollowFund } from "@/types/fund";
import { getFollowedFunds, unfollowFund } from "@/api/fund";

/**
 * 将 FollowFund 转换为 FundTableRow
 */
const toFundTableRow = (record: FollowFund): FundTableRow => {
  const info = record.fund_info;
  return {
    id: record.id,
    code: info?.code ?? record.fund_code,
    name: info?.name ?? "-",
    type: info?.type ?? "-",
    remark: record.remark,
    is_followed: true,
    latest: info?.latest,
    last_seen_data_date: info?.last_seen_data_date,
  };
};

const MyFollows: React.FC = () => {
  const [list, setList] = useState<FundTableRow[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchList = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getFollowedFunds();
      const data = (res.data || []).map(toFundTableRow);
      setList(data);
    } catch {
      // 网络错误统一由 api/index.ts 处理
    } finally {
      setLoading(false);
    }
  }, []);

  const handleUnfollow = useCallback(
    async (record: FundTableRow) => {
      try {
        await unfollowFund(record.code);
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

  return (
    <Card title="我的关注" bodyStyle={{ padding: 16 }}>
      <FundTable
        data={list}
        loading={loading}
        showRemark={true}
        showAction={true}
        onUnfollow={handleUnfollow}
        emptyText="暂无关注的基金"
        pagination={{ pageSize: 20 }}
      />
    </Card>
  );
};

export default MyFollows;