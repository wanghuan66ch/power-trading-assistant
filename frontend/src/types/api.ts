// API types matching backend schemas

export interface ProvincePrice {
  id: number
  province: string
  price_type: string
  price: number          // 元/兆瓦时
  capacity_mw: number     // 成交容量 MW
  recorded_at: string
  source: string
  created_at: string
}

export interface PriceTrend {
  province: string
  price_type: string
  current_price: number
  avg_price_7d: number
  max_price_7d: number
  min_price_7d: number
  change_pct: number      // 涨跌幅 %
}

export interface TradeRecord {
  id: number
  trade_no: string
  trade_type: string      // 购电/售电
  counterparty: string
  province: string
  capacity_mw: number
  price: number            // 元/兆瓦时
  start_date: string
  end_date: string
  status: string           // active/completed/cancelled
  notes: string
  created_at: string
  updated_at: string
}

export interface TradeRecordCreate {
  trade_type: string
  counterparty: string
  province: string
  capacity_mw: number
  price: number
  start_date: string
  end_date: string
  notes?: string
}

export interface TradeStatistics {
  total_trades: number
  total_capacity_mw: number
  avg_price: number
  total_amount: number
  active_trades: number
  completed_trades: number
}

export interface ForecastRecord {
  id: number
  plant_id: string
  plant_type: string       // 光伏/风电
  province: string
  forecast_time: string
  predicted_power_mw: number
  actual_power_mw?: number
  weather_condition: string
  irradiance?: number
  wind_speed?: number
  confidence?: number
  created_at: string
}

export interface ForecastAccuracy {
  plant_id: string
  plant_type: string
  accuracy_1h: number
  accuracy_24h: number
  mae: number
  mape: number
}

export interface StrategyRecommendation {
  strategy_type: string
  urgency: string
  target_province: string
  suggested_price_range_min: number
  suggested_price_range_max: number
  reasoning: string
  valid_until: string
}

export interface RiskWarning {
  warning_type: string
  severity: string
  province: string
  description: string
  estimated_loss?: number
  suggestion: string
  created_at: string
}

export interface PriceAlert {
  id: number
  province: string
  alert_type: string
  threshold_price: number
  current_price: number
  message: string
  is_sent: boolean
  created_at: string
}
