import React from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu } from 'antd'
import {
  DashboardOutlined,
  LineChartOutlined,
  FileTextOutlined,
  ExperimentOutlined,
  BulbOutlined,
  WarningOutlined,
} from '@ant-design/icons'

const { Sider, Content } = AntLayout

const navItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: <Link to="/dashboard">总览</Link> },
  { key: '/price', icon: <LineChartOutlined />, label: <Link to="/price">价格监控</Link> },
  { key: '/trade', icon: <FileTextOutlined />, label: <Link to="/trade">交易管理</Link> },
  { key: '/forecast', icon: <ExperimentOutlined />, label: <Link to="/forecast">功率预测</Link> },
  { key: '/strategy', icon: <BulbOutlined />, label: <Link to="/strategy">策略推荐</Link> },
  { key: '/risk', icon: <WarningOutlined />, label: <Link to="/risk">风险看板</Link> },
]

const Layout: React.FC = () => {
  const location = useLocation()

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth="0">
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: 18,
          fontWeight: 'bold',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          ⚡ 电力交易助手
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={navItems}
        />
      </Sider>
      <AntLayout>
        <Content style={{ margin: '24px 16px', overflow: 'initial' }}>
          <div style={{
            background: '#fff',
            borderRadius: 8,
            minHeight: 'calc(100vh - 48px)',
            padding: 24,
          }}>
            <Outlet />
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
