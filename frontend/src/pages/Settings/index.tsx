import React from "react";
import { useLocation } from "react-router-dom";
import AISettings from "./AISettings";
import NotifySettings from "./NotifySettings";
import DataSourceSettings from "./DataSourceSettings";

const SettingsRouter: React.FC = () => {
  const location = useLocation();

  if (location.pathname === "/settings/notify") {
    return <NotifySettings />;
  }

  if (location.pathname === "/settings/datasource") {
    return <DataSourceSettings />;
  }

  return <AISettings />;
};

export default SettingsRouter;
