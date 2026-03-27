import axios from 'axios'
import type {
  ProvincePrice, PriceTrend, TradeRecord, TradeRecordCreate,
  TradeStatistics, ForecastRecord, ForecastAccuracy, PriceAlert
} from '../types/api'

const API_BASE = 'http://localhost:8000/api/v1'
const api = axios.create({ baseURL: API_BASE, timeout: 15000 })

// ── 价格 API ──────────────────────────────────────────────────

export const priceApi = {
  /** 获取各省最新价格 */
  list: (params?: { province?: string; price_type?: string; limit?: number }) =>
    api.get<ProvincePrice[]>('/price/provinces', { params }).then(r => r.data),

  /** 获取价格趋势（7天统计） */
  trend: (province?: string) =>
    api.get<PriceTrend[]>('/price/trend', { params: { province } }).then(r => r.data),

  /** 触发抓取 */
  refresh: () => api.post('/price/refresh').then(r => r.data),

  /** 测试爬虫 */
  testSpiders: () => api.get('/price/test-spiders').then(r => r.data),

  /** 获取预警 */
  alerts: () => api.get<PriceAlert[]>('/price/alerts').then(r => r.data),
}

// ── 交易 API ──────────────────────────────────────────────────

export const tradeApi = {
  list: (params?: { province?: string; status?: string; trade_type?: string; limit?: number }) =>
    api.get<TradeRecord[]>('/trade/', { params }).then(r => r.data),

  create: (data: TradeRecordCreate) =>
    api.post<TradeRecord>('/trade/', data).then(r => r.data),

  update: (id: number, data: { status?: string; notes?: string }) =>
    api.patch<TradeRecord>(`/trade/${id}`, data).then(r => r.data),

  delete: (id: number) => api.delete(`/trade/${id}`).then(r => r.data),

  stats: () => api.get<TradeStatistics>('/trade/stats/summary').then(r => r.data),
}

// ── 预测 API ──────────────────────────────────────────────────

export const forecastApi = {
  list: (params?: { province?: string; plant_type?: string; limit?: number }) =>
    api.get<ForecastRecord[]>('/forecast/', { params }).then(r => r.data),

  trigger: (plant_id: string, plant_type = '光伏', latitude = 30.0, longitude = 120.0, capacity_mw = 100.0) =>
    api.post('/forecast/predict', null, { params: { plant_id, plant_type, latitude, longitude, capacity_mw } }).then(r => r.data),

  accuracy: (plant_id: string) =>
    api.get<ForecastAccuracy>(`/forecast/accuracy/${plant_id}`).then(r => r.data),

  modelInfo: () => api.get<any>('/forecast/model-info').then(r => r.data),
}

export default api
