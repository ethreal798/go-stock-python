import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  Card,
  List,
  Tag,
  Space,
  Typography,
  Button,
  Checkbox,
  Spin,
  Empty,
  Tabs,
  Divider,
} from "antd";
import {
  ReloadOutlined,
  ThunderboltOutlined,
  ReadOutlined,
} from "@ant-design/icons";
import { getFlashNews, getNewsList } from "@/api/market";
import type { NewsItem } from "@/types";
import dayjs from "dayjs";

const { Text } = Typography;

const News: React.FC = () => {
  const [flashNews, setFlashNews] = useState<NewsItem[]>([]);
  const [newsList, setNewsList] = useState<NewsItem[]>([]);
  const [flashLoading, setFlashLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(dayjs());
  const [onlyImportant, setOnlyImportant] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 更新实时时间
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(dayjs());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 获取快讯数据
  const fetchFlash = useCallback(
    async (pageNum: number, isRefresh = false) => {
      if (flashLoading) return;
      setFlashLoading(true);
      try {
        const res = await getFlashNews({
          count: 20,
          page: pageNum,
          source: "all",
        });
        const data = res.data || [];
        console.log(data);

        if (isRefresh) {
          setFlashNews(data);
          setPage(1);
          setHasMore(data.length > 0);
        } else {
          setFlashNews((prev) => [...prev, ...data]);
          if (data.length === 0) {
            setHasMore(false);
          }
        }
      } catch {
        // ignore
      } finally {
        setFlashLoading(false);
      }
    },
    [flashLoading],
  );

  // 获取普通新闻
  const fetchNews = useCallback(async () => {
    setNewsLoading(true);
    try {
      const res = await getNewsList({ count: 20, page: 1, source: "all" });
      const data = res.data || [];
      setNewsList(data);
    } catch {
      // ignore
    } finally {
      setNewsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFlash(1, true);
    fetchNews();
  }, []);

  // 触底加载逻辑
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    // 距离底部 50px 时加载更多
    if (target.scrollHeight - target.scrollTop - target.clientHeight < 50) {
      if (hasMore && !flashLoading) {
        const nextPage = page + 1;
        setPage(nextPage);
        fetchFlash(nextPage);
      }
    }
  };

  // 过滤重要快讯
  const filteredFlash = onlyImportant
    ? flashNews.filter((item) => item.is_red)
    : flashNews;

  // 渲染单条快讯或日期分隔符
  const renderFlashItem = (item: NewsItem, index: number) => {
    const currentDate = dayjs(item.data_time).format("MM月DD日，dddd");
    const prevItem = index > 0 ? filteredFlash[index - 1] : null;
    const prevDate = prevItem
      ? dayjs(prevItem.data_time).format("MM月DD日，dddd")
      : null;
    const showDateSeparator = currentDate !== prevDate;

    return (
      <React.Fragment key={item.id}>
        {showDateSeparator && (
          <div
            style={{
              padding: "20px 0 10px 76px",
              color: "rgba(0, 0, 0, 0.45)",
              fontSize: "14px",
              fontWeight: 500,
              background: "#fff",
            }}
          >
            {currentDate}
          </div>
        )}
        <List.Item
          style={{ borderBottom: "1px solid #f0f0f0", padding: "16px 0" }}
        >
          <div style={{ display: "flex", width: "100%", gap: 16 }}>
            <div
              style={{
                flexShrink: 0,
                width: 60,
                color: "#8c8c8c",
                fontSize: "14px",
                paddingTop: "2px",
                textAlign: "right",
              }}
            >
              {item.time}
            </div>
            <div
              style={{
                flex: 1,
                fontSize: "14px",
                lineHeight: "1.6",
                color: item.is_red ? "#8b0000" : "rgba(0, 0, 0, 0.88)",
                fontWeight: item.is_red ? 500 : 400,
              }}
            >
              {item.content}
            </div>
          </div>
        </List.Item>
      </React.Fragment>
    );
  };

  // 快讯列表内容
  const flashContent = (
    <div
      ref={scrollRef}
      onScroll={handleScroll}
      style={{
        height: "calc(100vh - 200px)",
        minHeight: "400px",
        overflowY: "auto",
        padding: "0 16px",
      }}
    >
      <List
        dataSource={filteredFlash}
        split={false}
        renderItem={(item, index) => renderFlashItem(item, index)}
      />
      {flashLoading && (
        <div style={{ textAlign: "center", padding: "16px 0" }}>
          <Spin size="small" tip="加载中..." />
        </div>
      )}
      {!hasMore && flashNews.length > 0 && (
        <div
          style={{ textAlign: "center", padding: "24px 0", color: "#bfbfbf" }}
        >
          当前已是最后一页
        </div>
      )}
      {!flashLoading && flashNews.length === 0 && (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </div>
  );

  const tabItems = [
    {
      key: "flash",
      label: (
        <span>
          <ThunderboltOutlined style={{ color: "#faad14" }} />
          快讯
        </span>
      ),
      children: flashContent,
    },
    {
      key: "news",
      label: (
        <span>
          <ReadOutlined />
          新闻
        </span>
      ),
      children: (
        <div
          style={{
            padding: "0 16px",
            height: "calc(100vh - 200px)",
            overflowY: "auto",
          }}
        >
          <List
            loading={newsLoading}
            dataSource={newsList}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={item.title}
                  description={
                    <Space>
                      <Tag>{item.source}</Tag>
                      <Text type="secondary">
                        {dayjs(item.data_time).format("YYYY-MM-DD HH:mm")}
                      </Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </div>
      ),
    },
  ];

  return (
    <Card
      title={
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Text style={{ fontSize: "14px" }}>
            {currentTime.format("MM月DD日，dddd，HH:mm:ss")}
          </Text>
          <Divider type="vertical" />
          <Checkbox
            checked={onlyImportant}
            onChange={(e) => setOnlyImportant(e.target.checked)}
          >
            只看重要的
          </Checkbox>
        </div>
      }
      extra={
        <Button icon={<ReloadOutlined />} onClick={() => fetchFlash(1, true)}>
          刷新
        </Button>
      }
      bodyStyle={{ padding: 0 }}
    >
      <Tabs
        items={tabItems}
        tabBarStyle={{ padding: "0 16px", marginBottom: 0 }}
      />
    </Card>
  );
};

export default News;
