/**
 * 受保护的路由：未登录用户重定向到登录页
 */
import React, { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuth } from '../hooks/useAuth'

interface Props {
  children: React.ReactNode
}

const ProtectedRoute: React.FC<Props> = ({ children }) => {
  const { token, user, checkAuth } = useAuth()

  useEffect(() => {
    if (token && !user) {
      checkAuth()
    }
  }, [])

  if (!token) {
    return <Navigate to="/login" replace />
  }

  if (token && !user) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
      }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  return <>{children}</>
}

export default ProtectedRoute
