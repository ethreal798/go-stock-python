// src/pages/Fund/components/FollowModal.tsx
import React from "react";
import { Modal, Form, Input, Typography } from "antd";

const { Text } = Typography;

/**
 * 基金基础信息接口 - 兼容 SearchFund 和 FundTableRow
 */
export interface FundBasicInfo {
  code: string;
  name: string;
}

/**
 * 关注弹窗组件属性
 */
interface FollowModalProps {
  /** 弹窗是否可见 */
  visible: boolean;
  /** 要关注的基金信息 */
  fund: FundBasicInfo | null;
  /** 确认关注回调，传入备注 */
  onOk: (remark: string) => void;
  /** 取消回调 */
  onCancel: () => void;
  /** 是否正在加载 */
  loading?: boolean;
}

/**
 * 基金关注弹窗
 * 用于在基金市场中添加关注时填写备注
 */
const FollowModal: React.FC<FollowModalProps> = ({
  visible,
  fund,
  onOk,
  onCancel,
  loading,
}) => {
  const [form] = Form.useForm();

  /**
   * 确认关注操作
   * 验证表单并调用父组件回调
   */
  const handleOk = () => {
    form.validateFields()
      .then((values) => {
        onOk(values.remark);
        form.resetFields();
      });
  };

  /**
   * 取消操作
   * 关闭弹窗并重置表单
   */
  const handleCancel = () => {
    onCancel();
    form.resetFields();
  };

  // 弹窗打开时，如果有基金信息，自动填充备注为基金名称
  React.useEffect(() => {
    if (visible && fund) {
      form.setFieldsValue({ remark: fund.name });
    }
  }, [visible, fund, form]);

  return (
    <Modal
      title="添加关注"
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      okText="确认关注"
      cancelText="取消"
      confirmLoading={loading}
      width={450}
    >
      <Form form={form} layout="vertical">
        {/* 展示基金基础信息 */}
        {fund && (
          <div
            style={{
              marginBottom: 16,
              padding: 12,
              background: "#f5f5f5",
              borderRadius: 4,
            }}
          >
            <Text type="secondary">
              <div>
                基金代码：<Text strong>{fund.code}</Text>
              </div>
              <div>
                基金名称：<Text strong>{fund.name}</Text>
              </div>
            </Text>
          </div>
        )}
        {/* 备注输入框 */}
        <Form.Item
          label="备注"
          name="remark"
          rules={[{ required: true, message: "请输入备注" }]}
        >
          <Input placeholder="给这支基金加个备注，方便以后查找" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default FollowModal;