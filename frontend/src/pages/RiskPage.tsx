import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const RiskPage: React.FC = () => {
  return (
    <div>
      <Title level={2}>⚠️ 风险看板</Title>
      <Card>
        <p>🚨 合约缺口预警、偏差考核估算、政策风险聚合</p>
        <p>功能开发中...</p>
      </Card>
    </div>
  )
}

export default RiskPage
