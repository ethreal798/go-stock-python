import React, { useEffect, useState, useCallback } from "react";
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Switch,
  Space,
  Tag,
  Popconfirm,
  message,
  Badge,
  Tooltip,
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import request from "@/api/index";
import { useAuthStore } from "@/stores/authStore";
import type { CronTask } from "@/types/cron";

const CronTasks: React.FC = () => {
  const isGuestMode = useAuthStore((state) => state.isGuestMode);
  const [tasks, setTasks] = useState<CronTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<CronTask | null>(null);
  const [form] = Form.useForm();

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await request.get<{ data?: CronTask[] }>("/cron-tasks");
      const data = (res.data as { data?: CronTask[] })?.data ?? [];
      setTasks(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingTask) {
        await request.put(`/cron-tasks/${editingTask.id}`, values);
        message.success("修改成功");
      } else {
        await request.post("/cron-tasks", values);
        message.success("创建成功");
      }
      setModalOpen(false);
      form.resetFields();
      setEditingTask(null);
      fetchTasks();
    } catch {
      // ignore
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await request.delete(`/cron-tasks/${id}`);
      setTasks((prev) => prev.filter((t) => t.id !== id));
      message.success("删除成功");
    } catch {
      // ignore
    }
  };

  const handleToggle = async (task: CronTask) => {
    try {
      await request.put(`/cron-tasks/${task.id}`, { enabled: !task.enabled });
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, enabled: !t.enabled } : t)),
      );
    } catch {
      // ignore
    }
  };

  const handleRun = async (id: number) => {
    try {
      await request.post(`/cron-tasks/${id}/run`);
      message.success("已触发执行");
    } catch {
      // ignore
    }
  };

  const openEdit = (task: CronTask) => {
    setEditingTask(task);
    form.setFieldsValue(task);
    setModalOpen(true);
  };

  const statusMap: Record<
    string,
    { status: "processing" | "default" | "error"; text: string }
  > = {
    running: { status: "processing", text: "执行中" },
    idle: { status: "default", text: "空闲" },
    error: { status: "error", text: "错误" },
  };

  const columns: ColumnsType<CronTask> = [
    { title: "ID", dataIndex: "id", width: 60 },
    { title: "任务名称", dataIndex: "name", ellipsis: true },
    {
      title: "Cron表达式",
      dataIndex: "cronExpr",
      width: 140,
      render: (v: string) => (
        <code
          style={{ background: "#f5f5f5", padding: "2px 6px", borderRadius: 3 }}
        >
          {v}
        </code>
      ),
    },
    {
      title: "任务类型",
      dataIndex: "taskType",
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 80,
      render: (v: string) => {
        const s = statusMap[v] ?? { status: "default", text: "未知" };
        return <Badge status={s.status} text={s.text} />;
      },
    },
    {
      title: "启用",
      dataIndex: "enabled",
      width: 70,
      render: (v: boolean, record) => (
        <Switch
          checked={v}
          size="small"
          onChange={() => handleToggle(record)}
          disabled={isGuestMode}
        />
      ),
    },
    { title: "上次执行", dataIndex: "lastRun", width: 150, ellipsis: true },
    { title: "下次执行", dataIndex: "nextRun", width: 150, ellipsis: true },
    { title: "备注", dataIndex: "remark", ellipsis: true },
    {
      title: "操作",
      width: 150,
      render: (_, record) => (
        <Space size={4}>
          <Button
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => handleRun(record.id)}
            disabled={isGuestMode}
          >
            执行
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEdit(record)}
            disabled={isGuestMode}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此任务？"
            onConfirm={() => handleDelete(record.id)}
            disabled={isGuestMode}
          >
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              disabled={isGuestMode}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="定时任务管理"
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchTasks}>
            刷新
          </Button>
          <Tooltip title={isGuestMode ? "请登录后使用新建功能" : ""}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingTask(null);
                form.resetFields();
                setModalOpen(true);
              }}
              disabled={isGuestMode}
            >
              新建任务
            </Button>
          </Tooltip>
        </Space>
      }
      bodyStyle={{ padding: 0 }}
    >
      <Table
        rowKey="id"
        columns={columns}
        dataSource={tasks}
        loading={loading}
        pagination={{ pageSize: 20 }}
        size="small"
        scroll={{ x: 1100 }}
      />

      <Modal
        title={editingTask ? "编辑任务" : "新建任务"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => {
          setModalOpen(false);
          form.resetFields();
          setEditingTask(null);
        }}
        okText="保存"
        cancelText="取消"
        width={520}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="任务名称"
            name="name"
            rules={[{ required: true, message: "请输入任务名称" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="Cron表达式"
            name="cronExpr"
            rules={[{ required: true, message: "请输入Cron表达式" }]}
          >
            <Input placeholder="如: 0 9 * * 1-5 （工作日9点）" />
          </Form.Item>
          <Form.Item
            label="任务类型"
            name="taskType"
            rules={[{ required: true, message: "请输入任务类型" }]}
          >
            <Input placeholder="如: fetch_stock_data" />
          </Form.Item>
          <Form.Item label="备注" name="remark">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item
            label="启用"
            name="enabled"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default CronTasks;
