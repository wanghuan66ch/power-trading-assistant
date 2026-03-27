import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const PricePage: React.FC = () => {
  return (
    <div>
      <Title level={2}>📈 价格监控</Title>
      <Card>
        <p>🔍 省份筛选、实时价格表格、价格走势图</p>
        <p>功能开发中...</p>
      </Card>
    </div>
  )
}

export default PricePage
