import { useState, useCallback, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export function useChatApi() {
  const [isLoading, setIsLoading] = useState(false)
  const sessionId = useRef(`sess_${Date.now()}_${Math.random().toString(36).slice(2)}`)

  const sendMessage = useCallback(async (message) => {
    setIsLoading(true)
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: sessionId.current,
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }

      return await res.json()
    } catch (err) {
      console.error('Chat API error:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchProducts = useCallback(async (params = {}) => {
    const query = new URLSearchParams(params).toString()
    const res = await fetch(`${API_BASE}/products${query ? `?${query}` : ''}`)
    if (!res.ok) throw new Error('Failed to fetch products')
    return res.json()
  }, [])

  return { sendMessage, fetchProducts, isLoading }
}
