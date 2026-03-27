import React, { useEffect, useState, useCallback } from 'react'
import {
  Card, Row, Col, Table, Select, Button, Tag, Space, Typography,
  Statistic, Spin, message, Modal, Form, Input, InputNumber,
  Progress, Alert, Tabs
} from 'antd'
import {
  SunOutlined, ThunderboltOutlined, ReloadOutlined, ExperimentOutlined
} from '@ant-design/icons'
import {
  Line, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip,
  ResponsiveContainer, Legend, BarChart, Bar, ComposedChart, Area
} from 'recharts'
import dayjs from 'dayjs'
import { forecastApi } from '../api/client'
import type { ForecastRecord } from '../types/api'

const { Title, Text } = Typography

const DEMO_RECORDS: ForecastRecord[] = [
  { id: 1, plant_id: 'GD-PV-001', plant_type: '光伏', province: '广东', forecast_time: dayjs().subtract(1,'hour').toISOString(), predicted_power_mw: 45.2, actual_power_mw: 43.8, weather_condition: '晴', irradiance: 820, confidence: 0.92, created_at: dayjs().subtract(1,'hour').toISOString() },
  { id: 2, plant_id: 'GD-PV-001', plant_type: '光伏', province: '广东', forecast_time: dayjs().subtract(2,'hour').toISOString(), predicted_power_mw: 52.1, actual_power_mw: 51.5, weather_condition: '晴', irradiance: 875, confidence: 0.94, created_at: dayjs().subtract(2,'hour').toISOString() },
  { id: 4, plant_id: 'SD-WT-003', plant_type: '风电', province: '山东', forecast_time: dayjs().subtract(1,'hour').toISOString(), predicted_power_mw: 68.4, actual_power_mw: 65.1, weather_condition: '晴', wind_speed: 8.2, confidence: 0.85, created_at: dayjs().subtract(1,'hour').toISOString() },
  { id: 5, plant_id: 'SD-WT-003', plant_type: '风电', province: '山东', forecast_time: dayjs().subtract(2,'hour').toISOString(), predicted_power_mw: 71.2, actual_power_mw: 72.8, weather_condition: '晴', wind_speed: 9.1, confidence: 0.87, created_at: dayjs().subtract(2,'hour').toISOString() },
  { id: 6, plant_id: 'JS-PV-005', plant_type: '光伏', province: '江苏', forecast_time: dayjs().subtract(1,'hour').toISOString(), predicted_power_mw: 33.6, actual_power_mw: 34.1, weather_condition: '阴', irradiance: 380, confidence: 0.78, created_at: dayjs().subtract(1,'hour').toISOString() },
]

// 模拟24小时光伏预测曲线（白天有电，夜间为0）
const DEMO_CHART_DATA = Array.from({ length: 24 }, (_, i) => {
  const solarHour = i >= 6 && i <= 18
  const basePower = solarHour ? 40 + 35 * Math.sin((i - 6) / 12 * Math.PI) : 0
  return {
    hour: `${String(i).padStart(2,'0')}:00`,
    predicted: solarHour ? Math.round((basePower + (Math.random() - 0.5) * 8) * 10) / 10 : 0,
    actual: i < new Date().getHours() && solarHour
      ? Math.round((basePower + (Math.random() - 0.5) * 6) * 10) / 10 : null,
  }
})

interface ModelInfo {
  loaded: boolean
  model_type: string
  report?: {
    plant_type: string
    test_mae: number
    test_mape: number
    test_r2: number
    cv_mae_mean: number
    cv_mae_std: number
    n_trees: number
    n_features: number
  }
}

const ForecastPage: React.FC = () => {
  const [records, setRecords] = useState<ForecastRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [filterProvince, setFilterProvince] = useState<string>('')
  const [filterType, setFilterType] = useState<string>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [triggering, setTriggering] = useState(false)
  const [activeTab, setActiveTab] = useState('curve')
  const [modelInfo, setModelInfo] = useState<{pv?: ModelInfo; wind?: ModelInfo} | null>(null)
  const [chartData] = useState(DEMO_CHART_DATA)
  const [form] = Form.useForm()

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [r, mi] = await Promise.all([
        forecastApi.list({ limit: 100 }),
        forecastApi.modelInfo().catch(() => null),
      ])
      setRecords(r.length > 0 ? r : DEMO_RECORDS)
      if (mi) setModelInfo(mi)
    } catch {
      setRecords(DEMO_RECORDS)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const filtered = records.filter(r => {
    if (filterProvince && r.province !== filterProvince) return false
    if (filterType && r.plant_type !== filterType) return false
    return true
  })

  const latestMap = new Map<string, ForecastRecord>()
  filtered.forEach(r => {
    if (!latestMap.has(r.plant_id) || dayjs(r.forecast_time).isAfter(dayjs(latestMap.get(r.plant_id)!.forecast_time))) {
      latestMap.set(r.plant_id, r)
    }
  })
  const latest = Array.from(latestMap.values())

  const totalPower = latest.reduce((s, r) => s + r.predicted_power_mw, 0)
  const pvCount = latest.filter(r => r.plant_type === '光伏').length
  const wtCount = latest.filter(r => r.plant_type === '风电').length
  const avgConf = latest.length ? latest.reduce((s, r) => s + (r.confidence || 0), 0) / latest.length : 0

  const handleTrigger = async (values: { plant_id: string; plant_type?: string; latitude?: number; longitude?: number; capacity_mw?: number }) => {
    setTriggering(true)
    try {
      await forecastApi.trigger(
        values.plant_id,
        values.plant_type || '光伏',
        values.latitude || 30.0,
        values.longitude || 120.0,
        values.capacity_mw || 100.0,
      )
      message.success('预测已完成！结果已存入数据库')
      setModalOpen(false)
      form.resetFields()
      setTimeout(fetchData, 800)
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '触发预测失败')
    } finally {
      setTriggering(false)
    }
  }

  const columns = [
    { title: '电站ID', dataIndex: 'plant_id', key: 'plant_id', render: (v: string) => <Text code style={{ fontSize: 11 }}>{v}</Text> },
    {
      title: '类型', dataIndex: 'plant_type', key: 'plant_type',
      render: (v: string) => (
        <Tag icon={v === '光伏' ? <SunOutlined /> : <ThunderboltOutlined />} color={v === '光伏' ? 'orange' : 'blue'}>{v}</Tag>
      ),
    },
    { title: '省份', dataIndex: 'province', key: 'province' },
    { title: '预测时间', dataIndex: 'forecast_time', key: 'forecast_time', render: (v: string) => dayjs(v).format('MM-DD HH:mm') },
    {
      title: '预测功率 (MW)', dataIndex: 'predicted_power_mw', key: 'predicted_power_mw',
      render: (v: number) => <Text strong>{v.toFixed(1)}</Text>,
    },
    {
      title: '实际功率', dataIndex: 'actual_power_mw', key: 'actual_power_mw',
      render: (v?: number) => v != null ? <Text type="success">{v.toFixed(1)}</Text> : <Text type="secondary">待填入</Text>,
    },
    { title: '天气', dataIndex: 'weather_condition', key: 'weather_condition', render: (v: string) => <Tag>{v}</Tag> },
    {
      title: '辐照/风速', key: 'env',
      render: (_: any, r: ForecastRecord) => {
        if (r.plant_type === '光伏') return r.irradiance != null ? `${r.irradiance} W/m²` : '-'
        if (r.plant_type === '风电') return r.wind_speed != null ? `${r.wind_speed} m/s` : '-'
        return '-'
      },
    },
    {
      title: '置信度', dataIndex: 'confidence', key: 'confidence',
      render: (v?: number) => {
        if (!v) return '-'
        const pct = Math.round(v * 100)
        return (
          <Progress
            percent={pct}
            size="small"
            strokeColor={pct >= 90 ? '#52c41a' : pct >= 75 ? '#1890ff' : '#ff4d4f'}
            style={{ width: 80 }}
          />
        )
      },
      width: 110,
    },
  ]

  if (loading) return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 100 }} />

  const showModelAlert = modelInfo && (modelInfo.pv?.loaded || modelInfo.wind?.loaded)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>🔮 功率预测</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
          <Button type="primary" icon={<ThunderboltOutlined />} onClick={() => setModalOpen(true)}>触发预测</Button>
        </Space>
      </div>

      {/* 模型状态 */}
      {showModelAlert && (
        <Alert
          message={
            <Space>
              <ExperimentOutlined />
              <span>🧠 AI 模型已就绪：</span>
              {modelInfo?.pv?.loaded && (
                <Tag color="green">
                  光伏 LightGBM MAE={modelInfo.pv.report?.test_mae?.toFixed(1)}MW MAPE={modelInfo.pv.report?.test_mape?.toFixed(1)}%
                </Tag>
              )}
              {modelInfo?.wind?.loaded && (
                <Tag color="blue">
                  风电 LightGBM MAE={modelInfo.wind.report?.test_mae?.toFixed(1)}MW MAPE={modelInfo.wind.report?.test_mape?.toFixed(1)}%
                </Tag>
              )}
            </Space>
          }
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 统计卡片 */}
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#fff7e6' }}>
            <Statistic title="光伏电站" value={pvCount} suffix="座" prefix={<SunOutlined style={{ color: '#fa8c16' }} />} valueStyle={{ fontSize: 20 }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#e6f7ff' }}>
            <Statistic title="风电场" value={wtCount} suffix="座" prefix={<ThunderboltOutlined style={{ color: '#1890ff' }} />} valueStyle={{ fontSize: 20 }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Statistic title="总预测功率" value={totalPower.toFixed(1)} suffix="MW" valueStyle={{ fontSize: 20 }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="平均置信度"
              value={(avgConf * 100).toFixed(1)}
              suffix="%"
              valueStyle={{ fontSize: 20, color: avgConf >= 0.9 ? '#52c41a' : '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 预测曲线 */}
      <Card title="📊 预测出力曲线（典型日模式）" style={{ marginBottom: 16 }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'curve',
              label: '出力曲线',
              children: (
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={3} />
                    <YAxis tick={{ fontSize: 11 }} unit=" MW" domain={[0, 'auto']} />
                    <ReTooltip formatter={(v: any, name: string) => [v != null ? `${Number(v).toFixed(1)} MW` : '-', name === 'actual' ? '实际出力' : '预测出力']} />
                    <Legend />
                    <Area type="monotone" dataKey="predicted" name="预测出力" fill="#fa8c1630" stroke="#fa8c16" strokeWidth={2} />
                    <Line type="monotone" dataKey="actual" name="实际出力" stroke="#1890ff" strokeWidth={2} dot={false} connectNulls />
                  </ComposedChart>
                </ResponsiveContainer>
              ),
            },
            {
              key: 'bar',
              label: '对比柱状图',
              children: (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData.filter((_, i) => i % 3 === 0)} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} unit=" MW" />
                    <ReTooltip />
                    <Legend />
                    <Bar dataKey="predicted" name="预测" fill="#fa8c16" radius={[4,4,0,0]} />
                    <Bar dataKey="actual" name="实际" fill="#1890ff" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              ),
            },
          ]}
        />
      </Card>

      {/* 预测记录表 */}
      <Card
        title="📋 预测记录"
        extra={
          <Space>
            <Select allowClear placeholder="电站类型" value={filterType || undefined}
              onChange={v => setFilterType(v || '')} style={{ width: 100 }}>
              <Select.Option value="光伏">光伏</Select.Option>
              <Select.Option value="风电">风电</Select.Option>
            </Select>
            <Select allowClear placeholder="省份" value={filterProvince || undefined}
              onChange={v => setFilterProvince(v || '')} style={{ width: 110 }}>
              {['广东','山东','江苏','浙江','山西','四川','福建','河南','云南'].map(p =>
                <Select.Option key={p} value={p}>{p}</Select.Option>)}
            </Select>
          </Space>
        }
      >
        {!showModelAlert && (
          <Alert
            message="当前显示示例数据。触发预测后，LightGBM AI 模型将自动接入，获取真实气象数据并计算。"
            type="info" showIcon style={{ marginBottom: 12 }}
          />
        )}
        <Table dataSource={filtered} columns={columns} rowKey="id" size="small"
          pagination={{ pageSize: 10, showSizeChanger: true }} />
      </Card>

      {/* 触发预测弹窗 */}
      <Modal
        title="⚡ 触发功率预测（调用 LightGBM AI 模型）"
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()} confirmLoading={triggering}
        width={520}
      >
        <Form form={form} layout="vertical" onFinish={handleTrigger} initialValues={{ plant_type: '光伏', latitude: 30.0, longitude: 120.0, capacity_mw: 100 }}>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="plant_id" label="电站ID" rules={[{ required: true }]}>
                <Input placeholder="如：GD-PV-001" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="plant_type" label="电站类型">
                <Select>
                  <Select.Option value="光伏">🌞 光伏</Select.Option>
                  <Select.Option value="风电">🌀 风电</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={8}>
              <Form.Item name="latitude" label="纬度">
                <InputNumber min={10} max={55} step={0.1} style={{ width: '100%' }} placeholder="如：30.0" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="longitude" label="经度">
                <InputNumber min={73} max={136} step={0.1} style={{ width: '100%' }} placeholder="如：120.0" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="capacity_mw" label="装机容量 (MW)">
                <InputNumber min={1} max={5000} step={1} style={{ width: '100%' }} placeholder="如：100" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

export default ForecastPage
