import React, { useState } from "react";
import { useLocation } from "react-router-dom";
import MyFollows from "./MyFollows";
import FundMarket from "./FundMarket";

const FundRouter: React.FC = () => {
  // 获取当前路由路径
  const location = useLocation();
  
  // 判断是否在基金市场页面
  const isMarketPage = location.pathname === "/fund/market";
  
  // 刷新键：用于强制重新渲染 MyFollows 组件
  // 当关注/取关操作成功后，改变此值触发组件重新请求数据
  const [refreshKey, setRefreshKey] = useState(0);

  /**
   * 关注成功后的回调函数
   * 由子组件（FundMarket）在关注/取关操作成功后调用
   * 通过更新 refreshKey 触发 MyFollows 重新获取最新数据
   */
  const handleFollowSuccess = () => {
    setRefreshKey((prev) => prev + 1);
  };

  // 根据路径渲染不同页面
  if (isMarketPage) {
    return <FundMarket onFollowSuccess={handleFollowSuccess} />;
  }

  // key 变化时强制重新挂载组件，触发重新请求
  return <MyFollows key={refreshKey} />;
};

export default FundRouter;