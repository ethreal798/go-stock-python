import React from "react";
import { RocketOutlined } from "@ant-design/icons";

const DevelopingPlaceholder: React.FC<{ text?: string }> = ({
  text = "当前功能正在火速开发中！！！",
}) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        height: "60vh",
        gap: "20px",
      }}
    >
      <div className="rocket-container">
        <RocketOutlined className="rocket-icon" />
      </div>
      <span className="rocket-text">{text}</span>
    </div>
  );
};

export default DevelopingPlaceholder;
