import React, { useState } from "react";
import { useLocation } from "react-router-dom";
import MyFollows from "./MyFollows";
import FundMarket from "./FundMarket";
import FundDetail from "./FundDetail";
import FundSearch from "./FundSearch";

const FundRouter: React.FC = () => {
  const location = useLocation();

  const isDetailPage = location.pathname.startsWith("/fund/detail/");
  const isMarketPage = location.pathname === "/fund/market";
  const isSearchPage = location.pathname === "/fund/search";

  const [refreshKey, setRefreshKey] = useState(0);

  const handleFollowSuccess = () => {
    setRefreshKey((prev) => prev + 1);
  };

  if (isDetailPage) {
    return <FundDetail />;
  }

  if (isMarketPage) {
    return <FundMarket onFollowSuccess={handleFollowSuccess} />;
  }

  if (isSearchPage) {
    return <FundSearch />;
  }

  return <MyFollows key={refreshKey} />;
};

export default FundRouter;