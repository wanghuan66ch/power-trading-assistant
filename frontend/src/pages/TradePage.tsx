import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const TradePage: React.FC = () => {
  return (
    <div>
      <Title level={2}>📝 交易管理</Title>
      <Card>
        <p>📋 交易记录列表、新增交易、统计分析</p>
        <p>功能开发中...</p>
      </Card>
    </div>
  )
}

export default TradePage
