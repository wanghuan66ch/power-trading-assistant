/**
 * 认证状态管理 (Zustand)
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import axios from 'axios'

const API_BASE = '/api/v1'

interface User {
  id: string
  email: string
  username: string
  is_active: boolean
}

interface AuthState {
  token: string | null
  user: User | null
  isLoading: boolean
  error: string | null

  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, username: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const formData = new URLSearchParams()
          formData.append('username', email)
          formData.append('password', password)

          const res = await axios.post(`${API_BASE}/auth/login`, formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          })
          const token = res.data.access_token
          // 获取当前用户信息
          const userRes = await axios.get(`${API_BASE}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          set({ token, user: userRes.data, isLoading: false })
        } catch (err: any) {
          set({
            isLoading: false,
            error: err?.response?.data?.detail || '登录失败，请检查邮箱和密码',
          })
          throw err
        }
      },

      register: async (email: string, password: string, username: string) => {
        set({ isLoading: true, error: null })
        try {
          await axios.post(`${API_BASE}/auth/register`, {
            email,
            password,
            username,
          })
          // 注册后自动登录
          await get().login(email, password)
        } catch (err: any) {
          set({
            isLoading: false,
            error: err?.response?.data?.detail || '注册失败',
          })
          throw err
        }
      },

      logout: () => {
        set({ token: null, user: null, error: null })
      },

      checkAuth: async () => {
        const { token } = get()
        if (!token) return
        try {
          const res = await axios.get(`${API_BASE}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          set({ user: res.data })
        } catch {
          // token 失效，清除
          get().logout()
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
)

// 封装 axios 实例，自动附加 token
export const authAxios = () => {
  const token = useAuth.getState().token
  return axios.create({
    baseURL: API_BASE,
    headers: {
      Authorization: token ? `Bearer ${token}` : '',
    },
  })
}
