import React, { useEffect, useState, useCallback } from 'react'
import {
  Card, Row, Col, Table, Tag, Space, Typography, Spin,
  Button, Select, Empty
} from 'antd'
import {
  BulbOutlined, ThunderboltOutlined, ReloadOutlined,
  ArrowUpOutlined, ArrowDownOutlined
} from '@ant-design/icons'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts'
import dayjs from 'dayjs'
import axios from 'axios'
import { useAuth } from '../hooks/useAuth'
import type { StrategyRecommendation, PriceTrend } from '../types/api'

const { Title, Text } = Typography

const API_BASE = '/api/v1'

const urgencyColor: Record<string, string> = { '高': 'red', '中': 'orange', '低': 'green' }

const StrategyPage: React.FC = () => {
  const { token } = useAuth()
  const [strategies, setStrategies] = useState<StrategyRecommendation[]>([])
  const [trends, setTrends] = useState<PriceTrend[]>([])
  const [loading, setLoading] = useState(true)
  const [filterProvince, setFilterProvince] = useState<string>('')
  const [filterType, setFilterType] = useState<string>('')

  const authHeaders = () => ({ headers: { Authorization: `Bearer ${token}` } })

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [s, t] = await Promise.all([
        axios.get(`${API_BASE}/strategy/recommend`, authHeaders()).then(r => r.data),
        axios.get(`${API_BASE}/price/trend`, authHeaders()).catch(() => []),
      ])
      setStrategies(Array.isArray(s) ? s : [])
      setTrends(Array.isArray(t) ? t : [])
    } catch {
      setStrategies([])
      setTrends([])
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { fetchData() }, [fetchData])

  const filtered = strategies.filter(s => {
    if (filterProvince && s.target_province !== filterProvince) return false
    if (filterType && s.strategy_type !== filterType) return false
    return true
  })

  const highUrgency = strategies.filter(s => s.urgency === '高').length
  const buyRecommendations = strategies.filter(s => s.strategy_type === '购电推荐').length
  const sellRecommendations = strategies.filter(s => s.strategy_type === '售电推荐').length

  const priceRank = [...trends]
    .filter(t => t.current_price > 0)
    .sort((a, b) => b.current_price - a.current_price)

  const chartData = filtered.slice(0, 8).map(s => ({
    province: s.target_province,
    min: s.suggested_price_range_min,
    max: s.suggested_price_range_max,
  }))

  const columns = [
    {
      title: '策略类型',
      dataIndex: 'strategy_type',
      key: 'strategy_type',
      render: (v: string) => {
        const map: Record<string, { text: string; color: string }> = {
          '购电推荐': { text: '📥 购电推荐', color: 'blue' },
          '售电推荐': { text: '📤 售电推荐', color: 'orange' },
          '观望': { text: '⏸️ 观望', color: 'default' },
        }
        const m = map[v] || { text: v, color: 'default' }
        return <Tag color={m.color}>{m.text}</Tag>
      },
      width: 120,
    },
    {
      title: '紧急度',
      dataIndex: 'urgency',
      key: 'urgency',
      render: (v: string) => (
        <Tag icon={v === '高' ? <ArrowUpOutlined /> : v === '中' ? <ThunderboltOutlined /> : <ArrowDownOutlined />}
          color={urgencyColor[v]}>{v}</Tag>
      ),
      width: 90,
    },
    {
      title: '目标省份',
      dataIndex: 'target_province',
      key: 'target_province',
      render: (v: string) => <Text strong>{v}</Text>,
      width: 100,
    },
    {
      title: '推荐价格区间',
      key: 'price_range',
      render: (_: any, r: StrategyRecommendation) => (
        <Text>
          <Text strong style={{ color: '#f5222d' }}>{r.suggested_price_range_min.toFixed(1)}</Text>
          {' ~ '}
          <Text strong style={{ color: '#f5222d' }}>{r.suggested_price_range_max.toFixed(1)}</Text>
          {' 元/MWh'}
        </Text>
      ),
      width: 180,
    },
    {
      title: '推荐理由',
      dataIndex: 'reasoning',
      key: 'reasoning',
      render: (v: string) => <Text type="secondary" style={{ fontSize: 13 }}>{v}</Text>,
    },
    {
      title: '有效期至',
      dataIndex: 'valid_until',
      key: 'valid_until',
      render: (v: string) => {
        const daysLeft = dayjs(v).diff(dayjs(), 'day')
        return (
          <Space direction="vertical" size={0}>
            <Text type="secondary" style={{ fontSize: 12 }}>{dayjs(v).format('MM-DD HH:mm')}</Text>
            {daysLeft <= 1 && <Tag color="red">即将过期</Tag>}
            {daysLeft <= 3 && daysLeft > 1 && <Tag color="orange">即将过期</Tag>}
          </Space>
        )
      },
      width: 120,
    },
  ]

  if (loading) return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 100 }} />

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>💡 策略推荐</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
        </Space>
      </div>

      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#fff1f0', border: '1px solid #ffccc7' }}>
            <Space direction="vertical" size={0}>
              <Text type="secondary" style={{ fontSize: 12 }}>高紧急策略</Text>
              <Space>
                {highUrgency > 0 && <Tag color="red">{highUrgency} 条</Tag>}
                {highUrgency === 0 && <Text type="secondary">无</Text>}
                {highUrgency > 0 && <BulbOutlined style={{ color: '#f5222d' }} />}
              </Space>
            </Space>
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#e6f7ff' }}>
            <Space direction="vertical" size={0}>
              <Text type="secondary" style={{ fontSize: 12 }}>购电推荐</Text>
              <Space>
                <Text strong>{buyRecommendations} 条</Text>
                <ArrowDownOutlined style={{ color: '#1890ff' }} />
              </Space>
            </Space>
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#fff7e6' }}>
            <Space direction="vertical" size={0}>
              <Text type="secondary" style={{ fontSize: 12 }}>售电推荐</Text>
              <Space>
                <Text strong>{sellRecommendations} 条</Text>
                <ArrowUpOutlined style={{ color: '#fa8c16' }} />
              </Space>
            </Space>
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Space direction="vertical" size={0}>
              <Text type="secondary" style={{ fontSize: 12 }}>全国均价</Text>
              <Text strong style={{ fontSize: 18 }}>
                {trends.length
                  ? (trends.reduce((s, t) => s + t.current_price, 0) / trends.length).toFixed(1)
                  : '-'} 元/MWh
              </Text>
            </Space>
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Space direction="vertical" size={0}>
              <Text type="secondary" style={{ fontSize: 12 }}>全国最高价</Text>
              <Text strong style={{ fontSize: 18, color: '#f5222d' }}>
                {priceRank[0] ? `${priceRank[0].current_price.toFixed(1)} 元` : '-'}
              </Text>
              {priceRank[0] && <Text type="secondary" style={{ fontSize: 11 }}>{priceRank[0].province}</Text>}
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={12}>
          <Card title="📊 各省当前价格排行（推荐参考）" size="small">
            {priceRank.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={priceRank.slice(0, 12).map((t, i) => ({
                    rank: i + 1,
                    province: t.province,
                    current: t.current_price,
                    avg7d: t.avg_price_7d,
                  }))}
                  margin={{ top: 5, right: 20, left: -10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="province" tick={{ fontSize: 11 }} interval={1} />
                  <YAxis tick={{ fontSize: 11 }} unit="元" domain={[0, 'auto']} />
                  <Tooltip formatter={(v: number, name: string) => [`${v?.toFixed(1)} 元/MWh`, name === 'current' ? '当前价' : '7日均价']} />
                  <Legend />
                  <Bar dataKey="current" name="当前价" fill="#1890ff" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="avg7d" name="7日均价" fill="#52c41a" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暂无价格数据" style={{ padding: '40px 0' }} />
            )}
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title="💡 推荐购电/售电价格区间" size="small">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="province" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} unit="元" domain={[0, 'auto']} />
                  <Tooltip formatter={(v: number, name: string) => [`${v?.toFixed(1)} 元/MWh`, name === 'min' ? '建议最低价' : '建议最高价']} />
                  <Legend />
                  <Bar dataKey="min" name="建议最低价" fill="#1890ff" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="max" name="建议最高价" fill="#ff4d4f" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暂无策略推荐，请确保后端已加载数据" style={{ padding: '40px 0' }} />
            )}
          </Card>
        </Col>
      </Row>

      <Card
        title="📋 策略推荐详情"
        extra={
          <Space>
            <Select allowClear placeholder="策略类型" value={filterType || undefined}
              onChange={v => setFilterType(v || '')} style={{ width: 120 }}>
              <Select.Option value="购电推荐">购电推荐</Select.Option>
              <Select.Option value="售电推荐">售电推荐</Select.Option>
              <Select.Option value="观望">观望</Select.Option>
            </Select>
            <Select allowClear placeholder="目标省份" value={filterProvince || undefined}
              onChange={v => setFilterProvince(v || '')} style={{ width: 110 }}>
              {[...new Set(strategies.map(s => s.target_province))].map(p =>
                <Select.Option key={p} value={p}>{p}</Select.Option>)}
            </Select>
          </Space>
        }
      >
        {strategies.length === 0 ? (
          <Empty description="暂无策略推荐" />
        ) : (
          <Table dataSource={filtered} columns={columns} rowKey={(_, i) => String(i)}
            size="small"
            pagination={{ pageSize: 8, showSizeChanger: true, showTotal: t => `共 ${t} 条` }}
          />
        )}
      </Card>
    </div>
  )
}

export default StrategyPage
