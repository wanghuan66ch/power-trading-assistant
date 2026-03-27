import React, { useEffect, useState, useCallback } from 'react'
import {
  Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber,
  Select, DatePicker, Row, Col, Statistic, Typography, Popconfirm,
  message, Tabs
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, ReloadOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { tradeApi } from '../api/client'
import type { TradeRecord, TradeRecordCreate, TradeStatistics } from '../types/api'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { TextArea } = Input

const PROVINCES = [
  '广东','山东','江苏','浙江','山西','四川','安徽','福建','河南','湖北',
  '湖南','江西','陕西','甘肃','新疆','云南','贵州','上海','北京','天津','蒙西'
]

const STATUS_COLORS: Record<string, string> = {
  active: 'green', completed: 'blue', cancelled: 'default',
}
const STATUS_TEXT: Record<string, string> = {
  active: '执行中', completed: '已完成', cancelled: '已取消',
}

const TradePage: React.FC = () => {
  const [records, setRecords] = useState<TradeRecord[]>([])
  const [stats, setStats] = useState<TradeStatistics | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [form] = Form.useForm<TradeRecordCreate>()
  const [activeTab, setActiveTab] = useState('all')

  const fetchData = useCallback(async () => {
    try {
      const [r, s] = await Promise.all([
        tradeApi.list({ limit: 200 }),
        tradeApi.stats(),
      ])
      setRecords(r)
      setStats(s)
    } catch {
      message.error('获取交易记录失败')
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  // 新增
  const handleCreate = async (values: TradeRecordCreate) => {
    setSubmitting(true)
    try {
      await tradeApi.create({
        ...values,
        start_date: values.start_date as any,
        end_date: values.end_date as any,
      } as any)
      message.success('交易记录已创建')
      setModalOpen(false)
      form.resetFields()
      fetchData()
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '创建失败')
    } finally {
      setSubmitting(false)
    }
  }

  // 更新状态
  const handleStatusChange = async (id: number, status: string) => {
    try {
      await tradeApi.update(id, { status })
      message.success(`已标记为「${STATUS_TEXT[status]}」`)
      fetchData()
    } catch { message.error('更新失败') }
  }

  // 删除
  const handleDelete = async (id: number) => {
    try {
      await tradeApi.delete(id)
      message.success('已删除')
      fetchData()
    } catch { message.error('删除失败') }
  }

  const columns = [
    {
      title: '交易编号',
      dataIndex: 'trade_no',
      key: 'trade_no',
      render: (v: string) => <Text code style={{ fontSize: 11 }}>{v}</Text>,
      width: 220,
    },
    {
      title: '类型',
      dataIndex: 'trade_type',
      key: 'trade_type',
      render: (v: string) => (
        <Tag color={v === '购电' ? 'blue' : 'orange'}>{v}</Tag>
      ),
      width: 80,
    },
    {
      title: '省份',
      dataIndex: 'province',
      key: 'province',
      width: 90,
    },
    {
      title: '对手方',
      dataIndex: 'counterparty',
      key: 'counterparty',
      ellipsis: true,
    },
    {
      title: '容量 (MW)',
      dataIndex: 'capacity_mw',
      key: 'capacity_mw',
      render: (v: number) => v.toLocaleString('zh-CN', { maximumFractionDigits: 0 }),
      sorter: (a: TradeRecord, b: TradeRecord) => a.capacity_mw - b.capacity_mw,
      width: 110,
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (v: number) => <Text strong>{v.toFixed(2)} 元/MWh</Text>,
      sorter: (a: TradeRecord, b: TradeRecord) => a.price - b.price,
      width: 130,
    },
    {
      title: '交易金额',
      key: 'amount',
      render: (_: any, r: TradeRecord) => {
        const days = dayjs(r.end_date).diff(dayjs(r.start_date), 'day') + 1
        const amount = r.capacity_mw * r.price * 24 * days / 1000 // 元 -> 万元
        return <Text>{amount.toFixed(0)} 元</Text>
      },
      width: 120,
    },
    {
      title: '合约期限',
      key: 'period',
      render: (_: any, r: TradeRecord) => (
        <Text type="secondary" style={{ fontSize: 12 }}>
          {dayjs(r.start_date).format('YYYY-MM-DD')} ~ {dayjs(r.end_date).format('YYYY-MM-DD')}
        </Text>
      ),
      width: 200,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => (
        <Tag color={STATUS_COLORS[v] || 'default'}>{STATUS_TEXT[v] || v}</Tag>
      ),
      width: 90,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, r: TradeRecord) => (
        <Space size="small">
          {r.status === 'active' && (
            <Button size="small" type="link" onClick={() => handleStatusChange(r.id, 'completed')}>
              完成
            </Button>
          )}
          {r.status === 'active' && (
            <Button size="small" type="link" danger onClick={() => handleStatusChange(r.id, 'cancelled')}>
              取消
            </Button>
          )}
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
      width: 160,
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>📝 交易管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新增交易
        </Button>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#e6f7ff' }}>
            <Statistic title="总交易笔数" value={stats?.total_trades ?? 0} suffix="笔" valueStyle={{ fontSize: 20 }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#f6ffed' }}>
            <Statistic title="总成交容量" value={(stats?.total_capacity_mw ?? 0).toLocaleString()} suffix="MW" valueStyle={{ fontSize: 20 }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#fff7e6' }}>
            <Statistic title="平均电价" value={stats?.avg_price ?? 0} suffix="元/MWh" precision={2} valueStyle={{ fontSize: 20 }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#f9f0ff' }}>
            <Statistic title="执行中" value={stats?.active_trades ?? 0} suffix="笔" valueStyle={{ fontSize: 20, color: '#52c41a' }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#e6f7ff' }}>
            <Statistic title="已完成" value={stats?.completed_trades ?? 0} suffix="笔" valueStyle={{ fontSize: 20, color: '#1890ff' }} />
          </Card>
        </Col>
      </Row>

      {/* 交易记录表 */}
      <Card
        title="📋 交易记录"
        extra={<Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>}
      >
        <Tabs
          activeKey={activeTab}
          onChange={(k) => setActiveTab(k)}
          items={[
            {
              key: 'all', label: `全部 (${records.length})`,
              children: <Table dataSource={records} columns={columns} rowKey="id" size="small" pagination={{ pageSize: 10, showSizeChanger: true, showTotal: t => `共 ${t} 条` }} scroll={{ x: 1200 }} locale={{ emptyText: '暂无交易记录' }} />
            },
            {
              key: 'active', label: `执行中 (${records.filter(r => r.status === 'active').length})`,
              children: <Table dataSource={records.filter(r => r.status === 'active')} columns={columns} rowKey="id" size="small" pagination={{ pageSize: 10, showSizeChanger: true, showTotal: t => `共 ${t} 条` }} scroll={{ x: 1200 }} locale={{ emptyText: '无执行中交易' }} />
            },
            {
              key: 'completed', label: `已完成 (${records.filter(r => r.status === 'completed').length})`,
              children: <Table dataSource={records.filter(r => r.status === 'completed')} columns={columns} rowKey="id" size="small" pagination={{ pageSize: 10, showSizeChanger: true, showTotal: t => `共 ${t} 条` }} scroll={{ x: 1200 }} locale={{ emptyText: '无已完成交易' }} />
            },
            {
              key: 'cancelled', label: `已取消 (${records.filter(r => r.status === 'cancelled').length})`,
              children: <Table dataSource={records.filter(r => r.status === 'cancelled')} columns={columns} rowKey="id" size="small" pagination={{ pageSize: 10, showSizeChanger: true, showTotal: t => `共 ${t} 条` }} scroll={{ x: 1200 }} locale={{ emptyText: '无已取消交易' }} />
            },
          ]}
        />
      </Card>

      {/* 新增交易弹窗 */}
      <Modal
        title="➕ 新增交易记录"
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={submitting}
        width={560}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{ trade_type: '购电' }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="trade_type" label="交易类型" rules={[{ required: true }]}>
                <Select>
                  <Select.Option value="购电">购电</Select.Option>
                  <Select.Option value="售电">售电</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="province" label="省份" rules={[{ required: true }]}>
                <Select placeholder="选择省份" showSearch>
                  {PROVINCES.map(p => <Select.Option key={p} value={p}>{p}</Select.Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="counterparty" label="交易对方" rules={[{ required: true, message: '请输入对方名称' }]}>
            <Input placeholder="如：华能电力广东分公司" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="capacity_mw" label="成交容量 (MW)" rules={[{ required: true, message: '请输入容量' }]}>
                <InputNumber min={1} style={{ width: '100%' }} placeholder="如：100" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="price" label="成交价格 (元/MWh)" rules={[{ required: true, message: '请输入价格' }]}>
                <InputNumber min={0} step={0.01} style={{ width: '100%' }} placeholder="如：380.50" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="period" label="合约期限" rules={[{ required: true, message: '请选择合约期限' }]}>
                <RangePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="备注">
            <TextArea rows={2} placeholder="可选备注信息..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TradePage
