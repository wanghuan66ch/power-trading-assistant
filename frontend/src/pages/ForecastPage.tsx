import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const ForecastPage: React.FC = () => {
  return (
    <div>
      <Title level={2}>🔮 功率预测</Title>
      <Card>
        <p>☀️ 光伏/风电功率预测、气象数据接入、AI 模型推理</p>
        <p>功能开发中...</p>
      </Card>
    </div>
  )
}

export default ForecastPage
