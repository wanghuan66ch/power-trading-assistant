import React, { useEffect, useState, useCallback } from 'react'
import {
  Card, Row, Col, Table, Select, Button, Space, Tag, Typography,
  Statistic, Spin, message, Modal, Alert
} from 'antd'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts'
import { ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { priceApi } from '../api/client'
import type { ProvincePrice, PriceTrend, PriceAlert } from '../types/api'

const { Title, Text } = Typography

const PROVINCES = [
  '全国','广东','山东','山西','江苏','浙江','安徽','福建','河南','湖北',
  '湖南','江西','四川','云南','贵州','陕西','甘肃','新疆','上海','北京',
  '天津','河北南网','冀北','辽宁','吉林','黑龙江','重庆','广西','海南','青海','宁夏','蒙西'
]

const PRICE_TYPES = ['综合均价', '日前', '实时', '尖峰', '高峰', '平段', '低谷', '集中竞价均价']

// 各省固定颜色
const PROVINCE_COLORS: Record<string, string> = {
  '广东': '#f5222d', '山东': '#fa8c16', '江苏': '#1890ff',
  '浙江': '#52c41a', '山西': '#722ed1', '四川': '#13c2c2',
  '全国': '#000000',
}
const PricePage: React.FC = () => {
  const [prices, setPrices] = useState<ProvincePrice[]>([])
  const [trends, setTrends] = useState<PriceTrend[]>([])
  const [alerts, setAlerts] = useState<PriceAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [spiderStatus, setSpiderStatus] = useState<any>(null)
  const [filterProvince, setFilterProvince] = useState<string>('')
  const [filterType, setFilterType] = useState<string>('')
  const [chartProvinces, setChartProvinces] = useState<string[]>(['广东', '山东', '山西'])
  const [showSpiderModal, setShowSpiderModal] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [p, t, a] = await Promise.all([
        priceApi.list({ limit: 200 }),
        priceApi.trend(),
        priceApi.alerts(),
      ])
      setPrices(p)
      setTrends(t)
      setAlerts(a)
    } catch {
      message.error('获取价格数据失败，请检查后端服务')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await priceApi.refresh()
      message.success('抓取完成，正在刷新...')
      setTimeout(() => fetchData(), 500)
    } catch {
      message.error('抓取失败')
    } finally {
      setRefreshing(false)
    }
  }

  // 过滤后的价格列表
  const filteredPrices = prices.filter(p => {
    if (filterProvince && p.province !== filterProvince) return false
    if (filterType && p.price_type !== filterType) return false
    return true
  })

  // 趋势图数据（展示当前选中省份的最新价格对比）
  const trendChartData = chartProvinces.map(province => {
    const t = trends.find(t => t.province === province)
    return {
      province,
      current: t?.current_price ?? 0,
      avg7d: t?.avg_price_7d ?? 0,
      max7d: t?.max_price_7d ?? 0,
      min7d: t?.min_price_7d ?? 0,
      changePct: t?.change_pct ?? 0,
    }
  })

  const columns = [
    {
      title: '省份',
      dataIndex: 'province',
      key: 'province',
      render: (prov: string) => <Tag color={PROVINCE_COLORS[prov] ? undefined : 'default'}>{provinceTag(prov)}</Tag>,
      width: 100,
    },
    {
      title: '价格类型',
      dataIndex: 'price_type',
      key: 'price_type',
      width: 120,
    },
    {
      title: '价格 (元/MWh)',
      dataIndex: 'price',
      key: 'price',
      render: (v: number) => <Text strong style={{ color: v > 500 ? '#f5222d' : v < 250 ? '#52c41a' : undefined }}>{v.toFixed(1)}</Text>,
      sorter: (a: ProvincePrice, b: ProvincePrice) => a.price - b.price,
    },
    {
      title: '容量 (MW)',
      dataIndex: 'capacity_mw',
      key: 'capacity_mw',
      render: (v: number) => v > 0 ? v.toLocaleString('zh-CN', { maximumFractionDigits: 0 }) : '-',
      sorter: (a: ProvincePrice, b: ProvincePrice) => a.capacity_mw - b.capacity_mw,
    },
    {
      title: '记录时间',
      dataIndex: 'recorded_at',
      key: 'recorded_at',
      render: (v: string) => dayjs(v).format('MM-DD HH:mm'),
      width: 110,
    },
    {
      title: '数据来源',
      dataIndex: 'source',
      key: 'source',
      ellipsis: true,
      render: (v: string) => <Text type="secondary" style={{ fontSize: 12 }}>{v}</Text>,
    },
  ]

  // 价格热力色
  const getPriceColor = (price: number) => {
    if (price < 250) return '#52c41a'
    if (price < 350) return '#1890ff'
    if (price < 450) return '#fa8c16'
    return '#f5222d'
  }

  if (loading) return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 100 }} />

  return (
    <div style={{ padding: 0 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>📈 价格监控</Title>
        <Space>
          <Button icon={<ReloadOutlined />} loading={refreshing} onClick={handleRefresh}>
            刷新数据
          </Button>
          <Button onClick={() => setShowSpiderModal(true)}>
            爬虫状态
          </Button>
        </Space>
      </div>

      {/* 预警提示 */}
      {alerts.length > 0 && (
        <Alert
          message={`⚠️ 当前有 ${alerts.length} 条价格预警`}
          description={alerts[0]?.message}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 统计卡片 */}
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="监测省份"
              value={trends.length}
              suffix="个"
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="最高价 (7日)"
              value={trends.length ? Math.max(...trends.map(t => t.max_price_7d)) : 0}
              suffix="元/MWh"
              valueStyle={{ fontSize: 20, color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="最低价 (7日)"
              value={trends.length ? Math.min(...trends.filter(t => t.min_price_7d > 0).map(t => t.min_price_7d)) : 0}
              suffix="元/MWh"
              valueStyle={{ fontSize: 20, color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="全国均价"
              value={trends.length ? (trends.reduce((s, t) => s + t.current_price, 0) / trends.length) : 0}
              suffix="元/MWh"
              precision={1}
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="价格记录数"
              value={prices.length}
              suffix="条"
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
      </Row>

      {/* 价格对比图 */}
      <Card
        title="各省价格对比"
        style={{ marginBottom: 16 }}
        extra={
          <Select
            mode="multiple"
            placeholder="选择省份对比"
            value={chartProvinces}
            onChange={setChartProvinces}
            style={{ width: 280 }}
            maxTagCount={3}
            options={PROVINCES.slice(1).map(p => ({ label: p, value: p }))}
          />
        }
      >
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={trendChartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="province" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, 'auto']} tick={{ fontSize: 12 }} unit="元" />
            <Tooltip
              formatter={(v: number, name: string) => [`${v.toFixed(1)} 元/MWh`, name]}
              labelFormatter={(l) => `省份: ${l}`}
            />
            <Legend />
            <Line type="monotone" dataKey="current" name="当前价" stroke="#1890ff" strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="avg7d" name="7日均价" stroke="#52c41a" strokeWidth={1.5} strokeDasharray="5 5" />
            <Line type="monotone" dataKey="max7d" name="7日最高" stroke="#ff4d4f" strokeWidth={1} strokeDasharray="2 2" />
            <Line type="monotone" dataKey="min7d" name="7日最低" stroke="#52c41a" strokeWidth={1} strokeDasharray="2 2" />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* 价格分省热力图（简易版） */}
      <Card title="各省当前价格（颜色 = 价格高低）" style={{ marginBottom: 16 }}>
        <Row gutter={[8, 8]}>
          {trends.map(t => (
            <Col key={t.province} xs={12} sm={8} md={6} lg={4}>
              <div style={{
                background: `${getPriceColor(t.current_price)}18`,
                border: `1px solid ${getPriceColor(t.current_price)}60`,
                borderRadius: 8,
                padding: '8px 12px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <Text strong style={{ fontSize: 13 }}>{t.province}</Text>
                <Space size={4} direction="vertical" style={{ textAlign: 'right' }}>
                  <Text strong style={{ color: getPriceColor(t.current_price), fontSize: 14 }}>
                    {t.current_price.toFixed(0)}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {t.change_pct >= 0 ? '↑' : '↓'}{Math.abs(t.change_pct).toFixed(1)}%
                  </Text>
                </Space>
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 价格记录表 */}
      <Card
        title="价格成交记录"
        extra={
          <Space>
            <Select allowClear placeholder="筛选省份" value={filterProvince || undefined} onChange={v => setFilterProvince(v || '')} style={{ width: 120 }}>
              {PROVINCES.map(p => <Select.Option key={p} value={p}>{p}</Select.Option>)}
            </Select>
            <Select allowClear placeholder="价格类型" value={filterType || undefined} onChange={v => setFilterType(v || '')} style={{ width: 130 }}>
              {PRICE_TYPES.map(t => <Select.Option key={t} value={t}>{t}</Select.Option>)}
            </Select>
          </Space>
        }
      >
        <Table
          dataSource={filteredPrices}
          columns={columns}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 15, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
          scroll={{ x: 800 }}
        />
      </Card>

      {/* 爬虫状态弹窗 */}
      <Modal
        title="🕷️ 爬虫状态"
        open={showSpiderModal}
        onCancel={() => setShowSpiderModal(false)}
        footer={null}
        width={600}
      >
        <pre style={{ fontSize: 12, background: '#f5f5f5', padding: 16, borderRadius: 8, maxHeight: 400, overflow: 'auto' }}>
          {JSON.stringify(spiderStatus || { loading: '点击测试...' }, null, 2)}
        </pre>
        <Button
          style={{ marginTop: 12 }}
          onClick={async () => {
            try {
              const d = await priceApi.testSpiders()
              setSpiderStatus(d.spiders)
            } catch { message.error('测试失败') }
          }}
        >
          测试连通性
        </Button>
      </Modal>
    </div>
  )
}

// 省份显示简化
const provinceTag = (p: string) => {
  const map: Record<string, string> = {
    '广东': '粤', '山东': '鲁', '江苏': '苏', '浙江': '浙', '山西': '晋',
    '四川': '川', '安徽': '皖', '福建': '闽', '河南': '豫', '湖北': '鄂',
    '湖南': '湘', '江西': '赣', '云南': '滇', '贵州': '黔', '陕西': '陕',
    '甘肃': '甘', '新疆': '新', '上海': '沪', '北京': '京', '天津': '津',
    '河北南网': '河北南', '冀北': '冀北', '辽宁': '辽', '吉林': '吉',
    '黑龙江': '黑', '重庆': '渝', '广西': '桂', '海南': '琼', '青海': '青',
    '宁夏': '宁', '蒙西': '蒙西',
  }
  return map[p] || p
}

export default PricePage
