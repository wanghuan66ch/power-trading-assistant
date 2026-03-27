import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Spin, Typography, Space, Tag } from 'antd'
import { ThunderboltOutlined, RiseOutlined, FallOutlined, BarChartOutlined } from '@ant-design/icons'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import dayjs from 'dayjs'
import { priceApi, tradeApi } from '../api/client'
import type { PriceTrend, TradeStatistics } from '../types/api'

const { Title, Text } = Typography

const Dashboard: React.FC = () => {
  const [trends, setTrends] = useState<PriceTrend[]>([])
  const [stats, setStats] = useState<TradeStatistics | null>(null)
  const [loading, setLoading] = useState(true)
  const today = dayjs().format('YYYY-MM-DD')

  useEffect(() => {
    const fetch = async () => {
      try {
        const [t, s] = await Promise.all([
          priceApi.trend(),
          tradeApi.stats(),
        ])
        setTrends(t)
        setStats(s)
      } catch {
        // ignore
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [])

  if (loading) return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 100 }} />

  // 取价格最高的5个省
  const top5 = [...trends].sort((a, b) => b.current_price - a.current_price).slice(0, 5)
  // 取价格最低的5个省
  const bottom5 = [...trends].filter(t => t.current_price > 0).sort((a, b) => a.current_price - b.current_price).slice(0, 5)

  const nationalAvg = trends.length
    ? trends.reduce((s, t) => s + t.current_price, 0) / trends.length
    : 0

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>📊 总览</Title>
        <Text type="secondary">{today}</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#e6f7ff' }}>
            <Statistic
              title="交易笔数"
              value={stats?.total_trades ?? 0}
              suffix="笔"
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#f6ffed' }}>
            <Statistic
              title="总成交容量"
              value={(stats?.total_capacity_mw ?? 0).toLocaleString()}
              suffix="MW"
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#fff7e6' }}>
            <Statistic
              title="平均电价"
              value={stats?.avg_price ?? 0}
              prefix="¥"
              suffix="/MWh"
              precision={2}
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#f9f0ff' }}>
            <Statistic
              title="全国均价"
              value={nationalAvg}
              prefix="¥"
              suffix="/MWh"
              precision={1}
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#fff1f0' }}>
            <Statistic
              title="最高价省份"
              value={top5[0]?.province ?? '-'}
              suffix={top5[0] ? `${top5[0].current_price.toFixed(0)}元` : ''}
              valueStyle={{ fontSize: 18, color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 价格 + 交易双栏 */}
      <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
        {/* 价格 TOP5 */}
        <Col xs={24} lg={12}>
          <Card title="📈 价格最高的省份" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              {top5.map((t, i) => (
                <div key={t.province} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
                  <Space>
                    <Tag color="red">{i + 1}</Tag>
                    <Text>{t.province}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{t.price_type}</Text>
                  </Space>
                  <Space>
                    <Text strong style={{ color: '#f5222d' }}>{t.current_price.toFixed(1)} 元/MWh</Text>
                    {t.change_pct >= 0
                      ? <RiseOutlined style={{ color: '#f5222d' }} />
                      : <FallOutlined style={{ color: '#52c41a' }} />
                    }
                  </Space>
                </div>
              ))}
            </Space>
          </Card>
        </Col>

        {/* 价格最低5 */}
        <Col xs={24} lg={12}>
          <Card title="📉 价格最低的省份" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              {bottom5.map((t, i) => (
                <div key={t.province} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
                  <Space>
                    <Tag color="green">{i + 1}</Tag>
                    <Text>{t.province}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{t.price_type}</Text>
                  </Space>
                  <Space>
                    <Text strong style={{ color: '#52c41a' }}>{t.current_price.toFixed(1)} 元/MWh</Text>
                    {t.change_pct >= 0
                      ? <RiseOutlined style={{ color: '#f5222d' }} />
                      : <FallOutlined style={{ color: '#52c41a' }} />
                    }
                  </Space>
                </div>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 快捷入口 */}
      <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
        <Col xs={24} lg={6}>
          <Card size="small" hoverable>
            <Space>
              <BarChartOutlined style={{ fontSize: 24, color: '#1890ff' }} />
              <div>
                <Text strong>价格监控</Text>
                <br /><Text type="secondary" style={{ fontSize: 12 }}>{trends.length} 个省份价格</Text>
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={6}>
          <Card size="small" hoverable>
            <Space>
              <ThunderboltOutlined style={{ fontSize: 24, color: '#fa8c16' }} />
              <div>
                <Text strong>功率预测</Text>
                <br /><Text type="secondary" style={{ fontSize: 12 }}>光伏/风电 AI 预测</Text>
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={6}>
          <Card size="small" hoverable>
            <Space>
              <RiseOutlined style={{ fontSize: 24, color: '#52c41a' }} />
              <div>
                <Text strong>交易管理</Text>
                <br /><Text type="secondary" style={{ fontSize: 12 }}>{stats?.active_trades ?? 0} 笔执行中</Text>
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={6}>
          <Card size="small" hoverable>
            <Space>
              <FallOutlined style={{ fontSize: 24, color: '#f5222d' }} />
              <div>
                <Text strong>风险看板</Text>
                <br /><Text type="secondary" style={{ fontSize: 12 }}>合约缺口预警</Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 实时价格条形图 */}
      {trends.length > 0 && (
        <Card title="🌡️ 各省当前价格对比" size="small" style={{ marginBottom: 16 }}>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart
              data={trends.map(t => ({ province: t.province, price: t.current_price, avg: t.avg_price_7d }))}
              margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="province" tick={{ fontSize: 11 }} interval={3} />
              <YAxis tick={{ fontSize: 11 }} unit="元" domain={[0, 'auto']} />
              <Tooltip formatter={(v: number, name: string) => [`${v.toFixed(1)} 元/MWh`, name === 'price' ? '当前价' : '7日均价']} />
              <Legend />
              <Line type="monotone" dataKey="price" name="当前价" stroke="#1890ff" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="avg" name="7日均价" stroke="#52c41a" strokeWidth={1.5} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  )
}

export default Dashboard
