import { ModelInfo, ModelStatus, AnalysisRecord } from '@/types'

const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token')
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE}${url}`, { ...options, headers })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail)
  }
  if (response.status === 204) return null
  return response.json()
}

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    fetchWithAuth('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (name: string, email: string, password: string) =>
    fetchWithAuth('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }),

  getMe: () => fetchWithAuth('/auth/me'),
  updateMe: (name: string) => fetchWithAuth('/auth/me', {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  }),
  updatePassword: (currentPassword: string, newPassword: string) => fetchWithAuth('/auth/password', {
    method: 'PATCH',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  }),
}

// Models API
export const modelsApi = {
  getAll: (): Promise<ModelInfo[]> => fetchWithAuth('/models'),

  getByName: (name: string): Promise<ModelInfo> =>
    fetchWithAuth(`/models/${name}`),

  getStatus: (): Promise<{ models: ModelStatus[] }> =>
    fetchWithAuth('/models/status'),

  getReadiness: (name: string, version?: string): Promise<any> =>
    fetchWithAuth(`/models/${name}/readiness${version ? `?model_version=${version}` : ''}`),

  compare: (): Promise<any> => fetchWithAuth('/models/compare/'),
}

// Analysis API
export const analysisApi = {
  getRecords: (userId: string): Promise<AnalysisRecord[]> => 
    fetchWithAuth(`/analysis/records?user_id=${encodeURIComponent(userId)}`),

  getRecord: (id: string): Promise<AnalysisRecord> =>
    fetchWithAuth(`/analysis/records/${id}`),

  getReport: (id: string) => fetchWithAuth(`/reports/analysis/${id}`),

  saveRecord: (record: {
    user_id: string
    image_name: string
    model_name: string
    predicted_class: string
    confidence: number
    status?: string
    model_version?: string
    class_probabilities?: Record<string, number> | null
    explanation_available?: boolean
  }): Promise<AnalysisRecord> =>
    fetchWithAuth('/analysis/records', {
      method: 'POST',
      body: JSON.stringify(record),
    }),

  getStats: (userId: string): Promise<{
    total_analyses: number
    by_class: Record<string, number>
    average_confidence: number
  }> => fetchWithAuth(`/analysis/stats?user_id=${encodeURIComponent(userId)}`),

  predict: async (file: File, modelName: string, modelVersion = '1.0') => {
    const token = localStorage.getItem('token')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('model_name', modelName)
    formData.append('model_version', modelVersion)

    const response = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error_message: 'Prediction failed' }))
      throw new Error(error.error_message || 'Prediction failed')
    }
    return response.json()
  },

  explain: async (file: File, modelName: string, modelVersion = '1.0', targetClass?: number) => {
    const token = localStorage.getItem('token')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('model_name', modelName)
    formData.append('model_version', modelVersion)
    if (targetClass !== undefined) {
      formData.append('target_class', targetClass.toString())
    }

    const response = await fetch(`${API_BASE}/explain`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error_message: 'Explanation failed' }))
      throw new Error(error.error_message || 'Explanation failed')
    }
    return response.json()
  },

  downloadReport: async (recordId: string) => {
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE}/reports/analysis/${recordId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Report download failed' }))
      throw new Error(error.detail || 'Report download failed')
    }
    return response.blob()
  },
}

export const portalApi = {
  doctors: (city = '', specialization = '') => fetchWithAuth(`/portal/doctors?city=${encodeURIComponent(city)}&specialization=${encodeURIComponent(specialization)}`),
  availability: (doctorId: string, date = '') => fetchWithAuth(`/portal/doctors/${doctorId}/availability${date ? `?date=${encodeURIComponent(date)}` : ''}`),
  createAvailability: (data: { date: string; start_time: string; end_time: string; interval_minutes: number }) => fetchWithAuth('/portal/doctor/availability', { method: 'POST', body: JSON.stringify(data) }),
  doctorProfile: () => fetchWithAuth('/portal/doctor/profile'),
  saveDoctorProfile: (profile: Record<string, unknown>) => fetchWithAuth('/portal/doctor/profile', { method: 'PUT', body: JSON.stringify(profile) }),
  bookAppointment: (doctor_id: string, appointment_at: string, reason: string, slot_id?: string) => fetchWithAuth('/portal/appointments', { method: 'POST', body: JSON.stringify({ doctor_id, appointment_at, slot_id, reason }) }),
  myAppointments: () => fetchWithAuth('/portal/appointments/me'),
  doctorAppointments: () => fetchWithAuth('/portal/doctor/appointments'),
  doctorPatients: () => fetchWithAuth('/portal/doctor/patients'),
  createDoctorNote: (patient_id: string, content: string, follow_up: string) => fetchWithAuth('/portal/doctor/notes', { method: 'POST', body: JSON.stringify({ patient_id, content, follow_up }) }),
  updateAppointment: (id: string, status: string) => fetchWithAuth(`/portal/appointments/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  progress: () => fetchWithAuth('/portal/progress'),
  notifications: () => fetchWithAuth('/portal/notifications'),
  markNotificationRead: (id: string) => fetchWithAuth(`/portal/notifications/${id}/read`, { method: 'PATCH' }),
}

// Health API
export const healthApi = {
  check: (): Promise<{ status: string }> => fetch(`${API_BASE}/health`).then(res => res.json()),
}
