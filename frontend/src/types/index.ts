export interface User {
  id: string
  name: string
  email: string
  createdAt: string
  updatedAt: string
  role: 'patient' | 'doctor'
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface ModelInfo {
  model_name: string
  model_version: string
  architecture: string
  num_classes: number
  class_names: string[]
  training_status: string
  model_path?: string
  experiment_id?: string
  metrics: Record<string, number | string>
}

export interface ModelStatus {
  model_name: string
  model_version: string
  status: string
  available: boolean
}

export interface AnalysisRecord {
  id: string
  user_id: string
  image_name: string
  model_name: string
  predicted_class: string
  confidence: number
  status: 'pending' | 'completed' | 'failed'
  created_at: string
  model_version: string
  class_probabilities: Record<string, number> | null
  explanation_available: boolean
}

export interface PredictionResult {
  predicted_class: string
  predicted_class_index: number
  class_probabilities: Record<string, number>
  confidence: number
  model_name: string
  model_version: string
  timestamp: string
}

export interface ApiError {
  detail: string
}

export type Theme = 'light' | 'dark' | 'system'
