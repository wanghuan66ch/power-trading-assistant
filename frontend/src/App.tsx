import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import PricePage from './pages/PricePage'
import TradePage from './pages/TradePage'
import ForecastPage from './pages/ForecastPage'
import StrategyPage from './pages/StrategyPage'
import RiskPage from './pages/RiskPage'
import LoginPage from './pages/LoginPage'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* 公开路由 */}
        <Route path="/login" element={<LoginPage />} />

        {/* 受保护的路由 */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="price" element={<PricePage />} />
          <Route path="trade" element={<TradePage />} />
          <Route path="forecast" element={<ForecastPage />} />
          <Route path="strategy" element={<StrategyPage />} />
          <Route path="risk" element={<RiskPage />} />
        </Route>

        {/* 兜底重定向 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
