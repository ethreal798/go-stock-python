import React, { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import { Spin } from "antd";

const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Market = lazy(() => import("@/pages/Market"));
const Agent = lazy(() => import("@/pages/Agent"));
const News = lazy(() => import("@/pages/News"));
const Fund = lazy(() => import("@/pages/Fund/index")); 
const CronTasks = lazy(() => import("@/pages/CronTasks"));
const Settings = lazy(() => import("@/pages/Settings"));
const About = lazy(() => import("@/pages/About"));

import AuthGuard from "@/components/AuthGuard";

const LoadingFallback = () => (
  <div
    style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      height: "60vh",
    }}
  >
    <Spin size="large" tip="加载中..." />
  </div>
);

const AppRouter: React.FC = () => {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <AuthGuard>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/market" element={<Market />} />
          <Route path="/agent" element={<Agent />} />
          <Route path="/news" element={<News />} />
          <Route path="/fund" element={<Fund />} />
          <Route path="/fund/market" element={<Fund />} />
          <Route path="/cron-tasks" element={<CronTasks />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </AuthGuard>
    </Suspense>
  );
};

export default AppRouter;