import React from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { Layout as AntLayout, Menu, Dropdown, Avatar, Typography } from 'antd'
import {
  DashboardOutlined,
  LineChartOutlined,
  FileTextOutlined,
  ExperimentOutlined,
  BulbOutlined,
  WarningOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useAuth } from '../hooks/useAuth'

const { Sider, Content, Header } = AntLayout
const { Text } = Typography

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
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenu = {
    items: [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        danger: true,
        onClick: handleLogout,
      },
    ],
  }

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
        {/* 顶部导航栏：右侧用户信息 */}
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          borderBottom: '1px solid #f0f0f0',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}>
          <Dropdown menu={userMenu} placement="bottomRight">
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: 6,
              transition: 'background 0.2s',
            }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#f5f5f5')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <Avatar size="small" icon={<UserOutlined />} style={{ background: '#1677ff' }} />
              <Text strong>{user?.username || user?.email}</Text>
            </div>
          </Dropdown>
        </Header>

        <Content style={{ margin: '24px 16px', overflow: 'initial' }}>
          <div style={{
            background: '#fff',
            borderRadius: 8,
            minHeight: 'calc(100vh - 48px - 64px)',
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
