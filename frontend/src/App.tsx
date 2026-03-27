import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import PricePage from './pages/PricePage'
import TradePage from './pages/TradePage'
import ForecastPage from './pages/ForecastPage'
import StrategyPage from './pages/StrategyPage'
import RiskPage from './pages/RiskPage'
import Layout from './components/Layout'

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="price" element={<PricePage />} />
          <Route path="trade" element={<TradePage />} />
          <Route path="forecast" element={<ForecastPage />} />
          <Route path="strategy" element={<StrategyPage />} />
          <Route path="risk" element={<RiskPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
