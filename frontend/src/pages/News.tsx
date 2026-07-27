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
import type { NewsItem } from "@/types/news";
import dayjs from "dayjs";

const { Text, Link } = Typography;

const News: React.FC = () => {
  const [flashNews, setFlashNews] = useState<NewsItem[]>([]);
  const [newsList, setNewsList] = useState<NewsItem[]>([]);
  const [flashLoading, setFlashLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(dayjs());
  const [onlyImportant, setOnlyImportant] = useState(false);

  // 快讯分页状态
  const [flashPage, setFlashPage] = useState(1);
  const [flashHasMore, setFlashHasMore] = useState(true);
  const flashScrollRef = useRef<HTMLDivElement>(null);

  // 新闻分页状态
  const [newsPage, setNewsPage] = useState(1);
  const [newsHasMore, setNewsHasMore] = useState(true);
  const newsScrollRef = useRef<HTMLDivElement>(null);

  // 用于避免 useEffect 依赖项问题的 refs
  const flashLoadingRef = useRef(flashLoading);
  const newsLoadingRef = useRef(newsLoading);
  const fetchFlashRef = useRef<typeof fetchFlash>();
  const fetchNewsRef = useRef<typeof fetchNews>();

  // 同步状态到 ref
  useEffect(() => {
    flashLoadingRef.current = flashLoading;
    newsLoadingRef.current = newsLoading;
    fetchFlashRef.current = fetchFlash;
    fetchNewsRef.current = fetchNews;
  });

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
      if (flashLoadingRef.current) return;
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
          setFlashPage(1);
          setFlashHasMore(data.length > 0);
        } else {
          setFlashNews((prev) => [...prev, ...data]);
          if (data.length === 0) {
            setFlashHasMore(false);
          }
        }
      } catch {
        // ignore
      } finally {
        setFlashLoading(false);
      }
    },
    [], // 依赖项现在是空的，用 ref 读 loading
  );

  // 获取普通新闻数据
  const fetchNews = useCallback(
    async (pageNum: number, isRefresh = false) => {
      if (newsLoadingRef.current) return;
      setNewsLoading(true);
      try {
        const res = await getNewsList({ count: 20, page: pageNum });
        const data = res.data || [];
        console.log(res);

        if (isRefresh) {
          setNewsList(data);
          setNewsPage(1);
          setNewsHasMore(data.length > 0);
        } else {
          setNewsList((prev) => [...prev, ...data]);
          if (data.length === 0) {
            setNewsHasMore(false);
          }
        }
      } catch {
        // ignore
      } finally {
        setNewsLoading(false);
      }
    },
    [], // 依赖项现在是空的
  );

  useEffect(() => {
    fetchFlash(1, true);
    fetchNews(1, true);
  }, [fetchFlash, fetchNews]); // 目前可以安全地依赖了

  // SSE 实时监听新快讯
  useEffect(() => {
    // 使用代理路径：http://localhost:3000/api/v1/news/stream -> http://localhost:8000/api/v1/news/stream
    const eventSource = new EventSource("/api/v1/news/stream");

    eventSource.onmessage = (event) => {
      console.log("SSE 收到消息:", event.data);
      if (event.data === "refresh" || event.data) {
        fetchFlashRef.current?.(1, true);
        fetchNewsRef.current?.(1, true);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE 连接错误:", error);
    };

    return () => {
      eventSource.close();
    };
  }, []); // 保持依赖项为空，因为我们用 ref 调用函数

  // 快讯触底加载逻辑
  const handleFlashScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    if (target.scrollHeight - target.scrollTop - target.clientHeight < 50) {
      if (flashHasMore && !flashLoading) {
        const nextPage = flashPage + 1;
        setFlashPage(nextPage);
        fetchFlash(nextPage);
      }
    }
  };

  // 新闻触底加载逻辑
  const handleNewsScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    if (target.scrollHeight - target.scrollTop - target.clientHeight < 50) {
      if (newsHasMore && !newsLoading) {
        const nextPage = newsPage + 1;
        setNewsPage(nextPage);
        fetchNews(nextPage);
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
      ref={flashScrollRef}
      onScroll={handleFlashScroll}
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
      {!flashHasMore && flashNews.length > 0 && (
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
          ref={newsScrollRef}
          onScroll={handleNewsScroll}
          style={{
            padding: "0 16px",
            height: "calc(100vh - 200px)",
            overflowY: "auto",
          }}
        >
          <List
            dataSource={newsList}
            split={false}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    item.url ? (
                      <Link href={item.url} target="_blank" rel="noreferrer">
                        {item.title}
                      </Link>
                    ) : (
                      item.title
                    )
                  }
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
          {newsLoading && (
            <div style={{ textAlign: "center", padding: "16px 0" }}>
              <Spin size="small" tip="加载中..." />
            </div>
          )}
          {!newsHasMore && newsList.length > 0 && (
            <div
              style={{
                textAlign: "center",
                padding: "24px 0",
                color: "#bfbfbf",
              }}
            >
              当前已是最后一页
            </div>
          )}
          {!newsLoading && newsList.length === 0 && (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
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
