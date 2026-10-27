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

export interface ModelReadiness {
  model_name: string
  model_version: string
  ready: boolean
  checks: Array<{ check: string; passed: boolean; message: string }>
}

export interface ModelComparison {
  status: string
  message?: string
  comparison?: Array<{
    model_name: string
    model_version: string
    training_status: string
    accuracy: number | null
    macro_f1: number | null
    weighted_f1: number | null
  }> | null
  table?: string
}

export interface DoctorProfile {
  user_id?: string
  specialization?: string
  qualifications?: string
  experience_years?: number
  clinic_name?: string
  address?: string
  city?: string
  state?: string
  bio?: string
  consultation_info?: string
  availability?: string
  phone?: string
  [field: string]: string | number | undefined
}

export interface DoctorNote {
  id: string
  doctor_id: string
  patient_id: string
  appointment_id: string | null
  note_type: string
  content: string
  follow_up: string
  created_at: string
  doctor_name: string
}

export interface PatientProgress {
  analyses: AnalysisRecord[]
  notes: DoctorNote[]
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
