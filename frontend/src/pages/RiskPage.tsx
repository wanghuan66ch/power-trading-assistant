import React, { useEffect, useState, useCallback } from 'react'
import {
  Card, Row, Col, Table, Tag, Space, Typography, Spin, Alert,
  Progress, Select, Badge, Statistic, Button, message
} from 'antd'
import {
  WarningOutlined, ThunderboltOutlined,
  ReloadOutlined, ExclamationCircleOutlined
} from '@ant-design/icons'
import {
  PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip
} from 'recharts'
import dayjs from 'dayjs'
import axios from 'axios'
import { useAuth } from '../hooks/useAuth'
import type { RiskWarning } from '../types/api'

const { Title, Text } = Typography

const API_BASE = '/api/v1'

const RiskPage: React.FC = () => {
  const { token } = useAuth()
  const [warnings, setWarnings] = useState<RiskWarning[]>([])
  const [dashboard, setDashboard] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [filterProvince, setFilterProvince] = useState<string>('')
  const [filterSeverity, setFilterSeverity] = useState<string>('')

  const authHeaders = () => ({ headers: { Authorization: `Bearer ${token}` } })

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [w, d] = await Promise.all([
        axios.get(`${API_BASE}/risk/warnings`, authHeaders()).then(r => r.data),
        axios.get(`${API_BASE}/risk/dashboard`, authHeaders()).then(r => r.data),
      ])
      setWarnings(w)
      setDashboard(d)
    } catch {
      message.error('获取风险数据失败，请先登录')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { fetchData() }, [fetchData])

  const filtered = warnings.filter(w => {
    if (filterProvince && w.province !== filterProvince) return false
    if (filterSeverity && w.severity !== filterSeverity) return false
    return true
  })

  const pieData = [
    { name: '高风险', value: dashboard?.high_risk_count ?? 0, color: '#f5222d' },
    { name: '中风险', value: dashboard?.medium_risk_count ?? 0, color: '#fa8c16' },
    { name: '低风险', value: dashboard?.low_risk_count ?? 0, color: '#52c41a' },
  ].filter(d => d.value > 0)

  const byType: Record<string, number> = {}
  filtered.forEach(w => {
    const label = w.warning_type === 'contract_gap' ? '合约缺口' :
      w.warning_type === 'penalty' ? '偏差考核' :
        w.warning_type === 'policy' ? '政策风险' : w.warning_type
    byType[label] = (byType[label] || 0) + 1
  })
  const barData = Object.entries(byType).map(([name, count]) => ({ name, count }))

  const byProvince: Record<string, { high: number; medium: number; low: number }> = {}
  filtered.forEach(w => {
    if (!byProvince[w.province]) byProvince[w.province] = { high: 0, medium: 0, low: 0 }
    const key = w.severity as keyof typeof byProvince[string]
    if (key in byProvince[w.province]) byProvince[w.province][key]++
  })

  const columns = [
    {
      title: '风险类型',
      dataIndex: 'warning_type',
      key: 'warning_type',
      render: (v: string) => {
        const map: Record<string, { text: string; color: string }> = {
          contract_gap: { text: '⚡ 合约缺口', color: 'blue' },
          penalty: { text: '💰 偏差考核', color: 'orange' },
          policy: { text: '📋 政策风险', color: 'purple' },
        }
        const m = map[v] || { text: v, color: 'default' }
        return <Tag color={m.color}>{m.text}</Tag>
      },
      width: 120,
    },
    {
      title: '等级',
      dataIndex: 'severity',
      key: 'severity',
      render: (v: string) => (
        <Badge status={v === '高' ? 'error' : v === '中' ? 'warning' : 'success'} text={v} />
      ),
      width: 80,
    },
    {
      title: '省份',
      dataIndex: 'province',
      key: 'province',
      render: (v: string) => <Text strong>{v}</Text>,
      width: 100,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (v: string) => <Text style={{ fontSize: 13 }}>{v}</Text>,
    },
    {
      title: '预估损失',
      dataIndex: 'estimated_loss',
      key: 'estimated_loss',
      render: (v?: number) => v != null
        ? <Text type="danger" strong>¥ {v.toLocaleString('zh-CN', { maximumFractionDigits: 0 })}</Text>
        : '-',
      width: 140,
    },
    {
      title: '建议',
      dataIndex: 'suggestion',
      key: 'suggestion',
      render: (v: string) => <Text type="secondary" style={{ fontSize: 12 }}>{v}</Text>,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => dayjs(v).format('MM-DD HH:mm'),
      width: 110,
    },
  ]

  if (loading) return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 100 }} />

  const provinces = [...new Set(warnings.map(w => w.province))]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>⚠️ 风险看板</Title>
        <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
      </div>

      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#fff1f0', border: '1px solid #ffccc7' }}>
            <Statistic title="高风险" value={dashboard?.high_risk_count ?? 0}
              prefix={<WarningOutlined />} valueStyle={{ fontSize: 22, color: '#f5222d' }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#fff7e6', border: '1px solid #ffd591' }}>
            <Statistic title="中风险" value={dashboard?.medium_risk_count ?? 0}
              prefix={<ExclamationCircleOutlined />} valueStyle={{ fontSize: 22, color: '#fa8c16' }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small" style={{ background: '#f6ffed', border: '1px solid #b7eb8f' }}>
            <Statistic title="低风险" value={dashboard?.low_risk_count ?? 0}
              valueStyle={{ fontSize: 22, color: '#52c41a' }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Statistic title="执行中合约" value={dashboard?.active_contracts ?? 0}
              suffix="笔" prefix={<ThunderboltOutlined />} valueStyle={{ fontSize: 22 }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Statistic title="本月预估偏差考核" value={dashboard?.estimated_penalty_monthly ?? 0}
              prefix="¥" precision={0} valueStyle={{ fontSize: 20, color: '#f5222d' }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card size="small">
            <Statistic title="最近更新"
              value={dashboard?.last_updated ? dayjs(dashboard.last_updated).format('HH:mm') : '-'}
              suffix="更新" valueStyle={{ fontSize: 18 }} />
          </Card>
        </Col>
      </Row>

      {warnings.length > 0 ? (
        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          <Col xs={24} md={8}>
            <Card title="📊 风险等级分布" size="small">
              {pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}>
                      {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip formatter={(v: number) => [`${v} 条`, '风险数']} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0', color: '#52c41a' }}>
                  <div style={{ fontSize: 32 }}>✅</div>
                  <Text type="secondary">暂无风险预警</Text>
                </div>
              )}
            </Card>
          </Col>

          <Col xs={24} md={8}>
            <Card title="📋 风险类型统计" size="small">
              {barData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={barData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                    <Tooltip formatter={(v: number) => [`${v} 条`, '风险数']} />
                    <Bar dataKey="count" fill="#1890ff" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0' }}><Text type="secondary">无数据</Text></div>
              )}
            </Card>
          </Col>

          <Col xs={24} md={8}>
            <Card title="🗺️ 省份风险概览" size="small" style={{ overflow: 'hidden' }}>
              <div style={{ maxHeight: 200, overflow: 'auto' }}>
                {Object.entries(byProvince).map(([prov, counts]) => {
                  const total = counts.high + counts.medium + counts.low
                  const pct = total > 0 ? (counts.high / total * 100) : 0
                  return (
                    <div key={prov} style={{ marginBottom: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                        <Text strong style={{ fontSize: 12 }}>{prov}</Text>
                        <Space size={4}>
                          {counts.high > 0 && <Tag color="red">{counts.high}</Tag>}
                          {counts.medium > 0 && <Tag color="orange">{counts.medium}</Tag>}
                          {counts.low > 0 && <Tag color="green">{counts.low}</Tag>}
                        </Space>
                      </div>
                      <Progress
                        percent={Math.round(pct)}
                        success={{ percent: Math.round(100 - pct) }}
                        strokeColor={counts.high > 0 ? '#f5222d' : counts.medium > 0 ? '#fa8c16' : '#52c41a'}
                        size="small" showInfo={false}
                      />
                    </div>
                  )
                })}
                {Object.keys(byProvince).length === 0 && <Text type="secondary" style={{ fontSize: 12 }}>暂无数据</Text>}
              </div>
            </Card>
          </Col>
        </Row>
      ) : (
        <Alert
          message="🎉 当前无风险预警"
          description="系统未检测到合约缺口、偏差考核异常或价格异常风险。"
          type="success" showIcon style={{ marginBottom: 16 }}
        />
      )}

      <Card
        title="🚨 风险预警详情"
        extra={
          <Space>
            <Select allowClear placeholder="筛选省份" value={filterProvince || undefined}
              onChange={v => setFilterProvince(v || '')} style={{ width: 120 }}>
              {provinces.map(p => <Select.Option key={p} value={p}>{p}</Select.Option>)}
            </Select>
            <Select allowClear placeholder="风险等级" value={filterSeverity || undefined}
              onChange={v => setFilterSeverity(v || '')} style={{ width: 100 }}>
              <Select.Option value="高">高</Select.Option>
              <Select.Option value="中">中</Select.Option>
              <Select.Option value="低">低</Select.Option>
            </Select>
          </Space>
        }
      >
        <Table dataSource={filtered} columns={columns} rowKey={(_, i) => String(i)}
          size="small"
          pagination={{ pageSize: 10, showSizeChanger: true, showTotal: t => `共 ${t} 条` }}
          locale={{ emptyText: '✨ 暂无风险预警' }}
        />
      </Card>
    </div>
  )
}

export default RiskPage
