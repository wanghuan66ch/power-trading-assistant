import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const StrategyPage: React.FC = () => {
  return (
    <div>
      <Title level={2}>💡 策略推荐</Title>
      <Card>
        <p>🎯 购电/售电时机建议、合约期限结构优化</p>
        <p>功能开发中...</p>
      </Card>
    </div>
  )
}

export default StrategyPage
