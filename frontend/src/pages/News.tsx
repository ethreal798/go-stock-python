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
  Divider,
  Select,
  Segmented,
  Dropdown,
} from "antd";
import { ReloadOutlined, DownOutlined } from "@ant-design/icons";
import { getNewsList } from "@/api/market";
import {
  getFlashList,
  getFlashOverview,
  getFlashUpdates,
  getNewsSources,
} from "@/api/news";
import type { NewsFlashItem, NewsItem } from "@/types/news";
import dayjs from "dayjs";
import { useLocation } from "react-router-dom";

const { Text, Link } = Typography;

const News: React.FC = () => {
  const location = useLocation();
  const isFlashPage = location.pathname === "/news/flash";
  const isFlashPageRef = useRef(isFlashPage);
  const [flashNews, setFlashNews] = useState<NewsFlashItem[]>([]);
  const [newsList, setNewsList] = useState<NewsItem[]>([]);
  const [flashLoading, setFlashLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(dayjs());
  const [onlyImportant, setOnlyImportant] = useState(false);
  const [newsSources, setNewsSources] = useState<
    { value: string; label: string }[]
  >([]);
  const [flashSource, setFlashSource] = useState<string>("cls");
  const [flashPeriod, setFlashPeriod] = useState<"today" | "week" | "all">(
    "today",
  );
  const [overview, setOverview] = useState<{
    total_count: number;
    important_count: number;
    top_topics: { name: string; news_count: number }[];
  } | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [activeTopic, setActiveTopic] = useState<string | null>(null);

  // 快讯分页状态
  const [flashHasMore, setFlashHasMore] = useState(true);
  const [flashCursor, setFlashCursor] = useState<{
    cursor_id: number;
    cursor_time: string;
  } | null>(null);
  const flashCursorRef = useRef<{
    cursor_id: number;
    cursor_time: string;
  } | null>(null);
  const [flashSyncId, setFlashSyncId] = useState(0);
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
  const pullFlashUpdatesRef = useRef<() => void>();

  // 同步状态到 ref
  useEffect(() => {
    isFlashPageRef.current = isFlashPage;
    flashLoadingRef.current = flashLoading;
    newsLoadingRef.current = newsLoading;
    fetchFlashRef.current = fetchFlash;
    fetchNewsRef.current = fetchNews;
    pullFlashUpdatesRef.current = () => {
      void pullFlashUpdates();
    };
    flashCursorRef.current = flashCursor;
  });

  // 更新实时时间
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(dayjs());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleSelectTopic = useCallback((topicName: string | null) => {
    setActiveTopic((prev) => (prev === topicName ? null : topicName));
  }, []);

  // 获取快讯数据
  const fetchFlash = useCallback(
    async (isRefresh = false) => {
      if (flashLoadingRef.current) return;
      setFlashLoading(true);
      try {
        const cursor = isRefresh ? null : flashCursorRef.current;
        const cursorId = cursor?.cursor_id ?? Number.MAX_SAFE_INTEGER;
        const cursorTime = cursor?.cursor_time ?? new Date().toISOString();
        const res = await getFlashList({
          source: flashSource,
          period: flashPeriod,
          important_only: onlyImportant,
          topic_name: activeTopic ?? undefined,
          limit: 20,
          cursor_id: cursorId,
          cursor_time: cursorTime,
        });
        const data = res.data;
        const items = data.items ?? [];
        const nextCursor = data.next_cursor ?? null;

        setFlashHasMore(Boolean(data.has_more));
        setFlashCursor(nextCursor);

        setFlashNews((prev) => {
          const map = new Map<number, NewsFlashItem>();
          if (!isRefresh) {
            for (const x of prev) map.set(x.id, x);
          }
          for (const x of items) map.set(x.id, x);
          const merged = Array.from(map.values());
          merged.sort(
            (a, b) =>
              dayjs(b.published_at).valueOf() - dayjs(a.published_at).valueOf(),
          );
          return merged;
        });

        if (isRefresh) {
          const nextSyncId = items.reduce((max, x) => Math.max(max, x.id), 0);
          setFlashSyncId(nextSyncId);
        }
      } catch {
      } finally {
        setFlashLoading(false);
      }
    },
    [flashPeriod, flashSource, onlyImportant, activeTopic],
  );

  const pullFlashUpdates = useCallback(async () => {
    if (!isFlashPageRef.current) return;
    if (flashLoadingRef.current) return;

    let afterId = flashSyncId;
    for (let i = 0; i < 3; i += 1) {
      try {
        const res = await getFlashUpdates({
          after_id: afterId,
          source: flashSource,
          period: flashPeriod,
          important_only: onlyImportant,
          topic_name: activeTopic ?? undefined,
          limit: 20,
        });
        const data = res.data;
        const items = data.items ?? [];
        if (items.length > 0) {
          setFlashNews((prev) => {
            const map = new Map<number, NewsFlashItem>();
            for (const x of prev) map.set(x.id, x);
            for (const x of items) map.set(x.id, x);
            const merged = Array.from(map.values());
            merged.sort(
              (a, b) =>
                dayjs(b.published_at).valueOf() -
                dayjs(a.published_at).valueOf(),
            );
            return merged;
          });
        }
        afterId = data.sync_id ?? afterId;
        setFlashSyncId(afterId);
        if (!data.has_more) {
          break;
        }
      } catch {
        break;
      }
    }
  }, [flashPeriod, flashSource, flashSyncId, onlyImportant, activeTopic]);

  // 获取普通新闻数据
  const fetchNews = useCallback(
    async (pageNum: number, isRefresh = false) => {
      if (newsLoadingRef.current) return;
      setNewsLoading(true);
      try {
        const res = await getNewsList({ count: 20, page: pageNum });
        const data = res.data || [];

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
    if (!isFlashPage) return;
    setFlashCursor(null);
    setFlashHasMore(true);
    setFlashNews([]);
    setFlashSyncId(0);
    void fetchFlash(true);
  }, [
    fetchFlash,
    flashPeriod,
    flashSource,
    isFlashPage,
    onlyImportant,
    activeTopic,
  ]);

  useEffect(() => {
    if (isFlashPage) return;
    fetchNews(1, true);
  }, [fetchNews, isFlashPage]);

  // SSE 实时监听新快讯
  useEffect(() => {
    // 使用代理路径：http://localhost:3000/api/v1/news/stream -> http://localhost:8000/api/v1/news/stream
    const eventSource = new EventSource("/api/v1/news/stream");

    eventSource.onmessage = (event) => {
      if (event.data === "refresh" || event.data) {
        if (isFlashPageRef.current) {
          pullFlashUpdatesRef.current?.();
          return;
        }
        fetchNewsRef.current?.(1, true);
      }
    };

    eventSource.onerror = (error) => {
      void error;
    };

    return () => {
      eventSource.close();
    };
  }, []); // 保持依赖项为空，因为我们用 ref 调用函数

  useEffect(() => {
    if (!isFlashPage) return;
    let mounted = true;
    const run = async () => {
      try {
        const res = await getNewsSources();
        const options = (res.data ?? []).map((x) => ({
          value: x.code,
          label: x.name,
        }));
        if (mounted) {
          setNewsSources(options);
          if (options.length > 0) {
            const exists = options.some((x) => x.value === flashSource);
            if (!exists) {
              setFlashSource(options[0].value);
            }
          }
        }
      } catch {}
    };
    run();
    return () => {
      mounted = false;
    };
  }, [isFlashPage]);

  useEffect(() => {
    if (!isFlashPage) return;
    setOverviewLoading(true);
    getFlashOverview({
      period: flashPeriod,
      source: flashSource,
      topic_limit: 10,
    })
      .then((res) => {
        setOverview(res.data);
      })
      .catch(() => {
        setOverview(null);
      })
      .finally(() => {
        setOverviewLoading(false);
      });
  }, [isFlashPage, flashPeriod, flashSource]);

  // 快讯触底加载逻辑
  const handleFlashScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    if (target.scrollHeight - target.scrollTop - target.clientHeight < 50) {
      if (flashHasMore && !flashLoading) {
        fetchFlash(false);
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
  const filteredFlash = flashNews;

  // 渲染单条快讯或日期分隔符
  const renderFlashItem = (item: NewsFlashItem, index: number) => {
    const currentDate = dayjs(item.published_at).format("MM月DD日");
    const prevItem = index > 0 ? filteredFlash[index - 1] : null;
    const prevDate = prevItem
      ? dayjs(prevItem.published_at).format("MM月DD日")
      : null;
    const showDateSeparator = currentDate !== prevDate;
    const timeText = dayjs(item.published_at).format("HH:mm:ss");
    const important = item.is_source_important;

    return (
      <React.Fragment key={item.id}>
        {showDateSeparator && (
          <div
            style={{
              padding: "20px 0 10px 10px",
              color: "rgba(0, 0, 0, 0.74)",
              fontSize: "15px",
              fontWeight: 600,
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
              {timeText}
            </div>
            <div
              style={{
                flex: 1,
                fontSize: "14px",
                lineHeight: "1.6",
                color: important ? "#8b0000" : "rgba(0, 0, 0, 0.88)",
                fontWeight: important ? 500 : 400,
              }}
            >
              <div>{item.content}</div>
              <div style={{ marginTop: 8 }}>
                <Space size={8} wrap>
                  <Tag>{item.source?.name ?? item.source?.code}</Tag>
                  {(item.topics ?? []).map((t) => (
                    <Tag key={t.name} color="processing">
                      {t.name}
                    </Tag>
                  ))}
                  {(item.entities ?? []).map((x) => (
                    <Tag key={`${x.type}:${x.symbol ?? x.name}`}>
                      {x.symbol ? `${x.name} ${x.symbol}` : x.name}
                    </Tag>
                  ))}
                </Space>
              </div>
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
        height: "calc(100vh - 140px )",
        minHeight: "400px",
        overflowY: "auto",
        padding: "0 16px 20px 16px",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          padding: "12px 0",
          borderBottom: "1px solid #f0f0f0",
          flexWrap: "wrap",
        }}
      >
        <Space size={12} align="center" wrap>
          <Segmented
            value={flashPeriod}
            options={[
              { label: "今天", value: "today" },
              { label: "近7天", value: "week" },
              { label: "全部", value: "all" },
            ]}
            onChange={(v) => {
              setFlashPeriod(v as "today" | "week" | "all");
              setActiveTopic(null);
            }}
          />
          {overviewLoading ? (
            <Spin size="small" />
          ) : overview ? (
            <Space size={8} wrap>
              <Text>
                {flashPeriod === "today"
                  ? "今日"
                  : flashPeriod === "week"
                    ? "近7天"
                    : "全部"}{" "}
                {overview.total_count} 条
              </Text>
              <Text>·</Text>
              <Text>重要 {overview.important_count} 条</Text>
            </Space>
          ) : null}
        </Space>
        <Space size={12} wrap>
          {activeTopic ? (
            <Tag
              closable
              color="blue"
              onClose={() => setActiveTopic(null)}
              style={{ marginInlineEnd: 0 }}
            >
              主题：{activeTopic}
            </Tag>
          ) : null}
          <Select
            value={flashSource}
            options={newsSources}
            style={{ width: 140 }}
            onChange={(v) => {
              setFlashSource(v);
              setActiveTopic(null);
            }}
          />
          <Checkbox
            checked={onlyImportant}
            onChange={(e) => {
              setOnlyImportant(e.target.checked);
              setActiveTopic(null);
            }}
          >
            只看重要
          </Checkbox>
        </Space>
      </div>

      {overview?.top_topics?.length ? (
        <div style={{ padding: "12px 0" }}>
          <Space size={8} wrap>
            <Text type="secondary">热门主题：</Text>
            {(() => {
              const topics = overview.top_topics ?? [];
              const visible = topics.slice(0, 8);
              const rest = topics.slice(8);
              return (
                <>
                  {visible.map((t) => (
                    <Tag
                      key={t.name}
                      color={activeTopic === t.name ? "blue" : undefined}
                      style={{ cursor: "pointer" }}
                      onClick={() => handleSelectTopic(t.name)}
                    >
                      {t.name} {t.news_count}
                    </Tag>
                  ))}
                  {rest.length > 0 && (
                    <Dropdown
                      menu={{
                        items: rest.map((t) => ({
                          key: t.name,
                          label: `${t.name} ${t.news_count}`,
                          onClick: () => handleSelectTopic(t.name),
                        })),
                      }}
                      trigger={["click"]}
                    >
                      <Button size="small" type="link">
                        更多 <DownOutlined />
                      </Button>
                    </Dropdown>
                  )}
                </>
              );
            })()}
          </Space>
        </div>
      ) : null}

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

  const newsContent = (
    <div
      ref={newsScrollRef}
      onScroll={handleNewsScroll}
      style={{
        padding: "0 16px 20px 16px",
        height: "calc(100vh - 200px - 20px)",
        minHeight: "400px",
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
  );

  return (
    <Card
      title={
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Text style={{ fontSize: "14px" }}>
            {isFlashPage ? "快讯" : "新闻"}
          </Text>
          {isFlashPage && (
            <>
              <Divider type="vertical" />
              <Text type="secondary" style={{ fontSize: 14 }}>
                {currentTime.format("YYYY-MM-DD dddd HH:mm:ss")}
              </Text>
            </>
          )}
        </div>
      }
      bodyStyle={{ padding: 0 }}
    >
      {isFlashPage ? flashContent : newsContent}
    </Card>
  );
};

export default News;
