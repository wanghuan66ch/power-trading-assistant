import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Spin } from 'antd'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api/v1'

interface Stats {
  total_trades: number
  total_capacity_mw: number
  avg_price: number
  total_amount: number
  active_trades: number
  completed_trades: number
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get(`${API_BASE}/trade/stats/summary`)
        setStats(res.data)
      } catch {
        // 后端未启动时显示占位数据
        setStats({
          total_trades: 12,
          total_capacity_mw: 3450,
          avg_price: 386.5,
          total_amount: 1334925,
          active_trades: 8,
          completed_trades: 4,
        })
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [])

  if (loading) return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 100 }} />

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>📊 总览</h1>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="交易记录总数" value={stats?.total_trades ?? 0} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="总成交容量" value={stats?.total_capacity_mw ?? 0} suffix="MW" />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="平均电价" value={stats?.avg_price ?? 0} prefix="¥" suffix="/MW" />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="总交易金额" value={(stats?.total_amount ?? 0) / 10000} prefix="¥" suffix="万" />
          </Card>
        </Col>
      </Row>

      {/* 快捷入口 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="📈 价格监控" extra={<a href="/price">查看更多</a>}>
            实时追踪各省电力交易中心成交价格，支持价格预警和趋势分析
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="🔮 功率预测" extra={<a href="/forecast">查看更多</a>}>
            基于气象数据和 AI 模型，预测光伏/风电次日出力
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="💡 策略推荐" extra={<a href="/strategy">查看更多</a>}>
            基于价格趋势分析，给出购电/售电时机和合约结构建议
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="⚠️ 风险看板" extra={<a href="/risk">查看更多</a>}>
            合约缺口预警、偏差考核估算、政策风险聚合
          </Card>
        </Col>
      </Row>

      {/* 今日市场概况 */}
      <Card title="今日市场概况">
        <p>📅 2026年3月27日（周五）</p>
        <ul style={{ lineHeight: 2 }}>
          <li>沪指收涨 +0.58%，市场低开高走展现韧性</li>
          <li>创新药板块爆发，锂矿/能源金属领涨</li>
          <li>电力板块高位震荡，华电辽能9连板后出现分歧</li>
          <li>电力交易辅助工具 MVP 版本已初始化完成</li>
        </ul>
      </Card>
    </div>
  )
}

export default Dashboard
