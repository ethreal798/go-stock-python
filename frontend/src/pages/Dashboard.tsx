import React, { useEffect, useState, useCallback } from "react";
import {
  Card,
  Button,
  Input,
  Space,
  Tag,
  Tooltip,
  Modal,
  Form,
  Select,
  message,
  Segmented,
} from "antd";
import { PlusOutlined, ReloadOutlined, StarOutlined } from "@ant-design/icons";
import { useStockStore } from "@/stores/stockStore";
import { useAuthStore } from "@/stores/authStore";
import {
  getStockList,
  addStock,
  deleteStock,
  getStockPrices,
} from "@/api/stock";
import StockTable from "@/components/StockTable";
import type { Stock, StockPrice } from "@/types/stock";

const Dashboard: React.FC = () => {
  const {
    stocks,
    prices,
    selectedGroup,
    setStocks,
    addStock: addToStore,
    removeStock,
    setLoading,
    loading,
    setSelectedGroup,
    updatePrices,
  } = useStockStore();
  const isGuestMode = useAuthStore((state) => state.isGuestMode);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [groups, setGroups] = useState<string[]>(["全部"]);

  const fetchStocks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getStockList();
      const list: Stock[] =
        (res.data as { data?: Stock[]; list?: Stock[] })?.data ??
        (res.data as { data?: Stock[]; list?: Stock[] })?.list ??
        [];
      setStocks(list);
      const grpSet = new Set<string>(["全部"]);
      list.forEach((s) => s.group && grpSet.add(s.group));
      setGroups(Array.from(grpSet));

      if (list.length > 0) {
        const codes = list.map((s) => s.code);
        const priceRes = await getStockPrices(codes);
        const priceList =
          (priceRes.data as { data?: StockPrice[] })?.data ?? [];
        updatePrices(priceList);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [setStocks, setLoading, updatePrices]);

  useEffect(() => {
    fetchStocks();
  }, [fetchStocks]);

  const handleAddStock = async () => {
    try {
      const values = await form.validateFields();
      await addStock(values);
      addToStore({
        code: values.code,
        name: values.name,
        market: values.market,
        group: values.group,
      });
      message.success("添加成功");
      setAddModalOpen(false);
      form.resetFields();
      fetchStocks();
    } catch {
      // ignore
    }
  };

  const handleDelete = async (code: string) => {
    try {
      await deleteStock(code);
      removeStock(code);
      message.success("删除成功");
    } catch {
      // ignore
    }
  };

  const filteredStocks =
    selectedGroup === "全部"
      ? stocks
      : stocks.filter((s) => s.group === selectedGroup);

  return (
    <div>
      <Card
        title={
          <Space>
            <StarOutlined style={{ color: "#faad14" }} />
            <span>自选股</span>
            <Tag color="blue">{stocks.length}</Tag>
          </Space>
        }
        extra={
          <Space>
            <Segmented
              options={groups}
              value={selectedGroup}
              onChange={(v) => setSelectedGroup(String(v))}
            />
            <Tooltip title="刷新行情">
              <Button icon={<ReloadOutlined />} onClick={fetchStocks} loading={loading} />
            </Tooltip>
            <Tooltip title={isGuestMode ? "请登录后使用添加功能" : ""}>
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => setAddModalOpen(true)}
                disabled={isGuestMode}
              >
                添加股票
              </Button>
            </Tooltip>
          </Space>
        }
        bodyStyle={{ padding: 0 }}
      >
        <StockTable
          stocks={filteredStocks}
          prices={prices}
          loading={loading}
          onDelete={handleDelete}
          isGuestMode={isGuestMode}
        />
      </Card>

      <Modal
        title="添加自选股"
        open={addModalOpen}
        onOk={handleAddStock}
        onCancel={() => {
          setAddModalOpen(false);
          form.resetFields();
        }}
        okText="添加"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="股票代码"
            name="code"
            rules={[{ required: true, message: "请输入股票代码" }]}
          >
            <Input placeholder="如: 000001 / 600036" />
          </Form.Item>
          <Form.Item label="股票名称" name="name">
            <Input placeholder="可选，自动识别" />
          </Form.Item>
          <Form.Item label="市场" name="market" initialValue="SZ">
            <Select
              options={[
                { label: "深圳 (SZ)", value: "SZ" },
                { label: "上海 (SH)", value: "SH" },
                { label: "北交所 (BJ)", value: "BJ" },
              ]}
            />
          </Form.Item>
          <Form.Item label="分组" name="group">
            <Input placeholder="可选，如: 科技、医药" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Dashboard;
