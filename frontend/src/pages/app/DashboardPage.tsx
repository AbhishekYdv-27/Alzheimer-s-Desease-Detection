import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { modelsApi, analysisApi, portalApi } from '@/services/api'
import { ModelInfo } from '@/types'
import { Box, Brain, Database, Scan, AlertCircle, Clock } from 'lucide-react'

interface AnalysisStats {
  total_analyses: number
  by_class: Record<string, number>
  average_confidence: number
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [models, setModels] = useState<ModelInfo[]>([])
  const [stats, setStats] = useState<AnalysisStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [appointments, setAppointments] = useState<{ id: string; appointment_at: string; doctor_name?: string; status: string }[]>([])

  useEffect(() => {
    const loadData = async () => {
      try {
        const modelsData = await modelsApi.getAll()
        setModels(modelsData)

        if (user?.id) {
          const statsData = await analysisApi.getStats(user.id)
          setStats(statsData)
          const appointmentData = await portalApi.myAppointments()
          setAppointments(appointmentData)
        }
      } catch (error) {
        console.error('Failed to load data:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [user?.id])

  const trainedModels = models.filter((m) => m.training_status === 'TRAINED')

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Welcome back, {user?.name || 'Researcher'}</h1>
          <p className="mt-1 text-muted-foreground">
          Your private overview of MRI research, appointments, and care-team activity.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-border/40 bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Analysis Records</p>
              <p className="mt-1 text-2xl font-bold">{stats?.total_analyses ?? 0}</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-500/10">
              <Scan className="h-6 w-6 text-blue-500" />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border/40 bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Models Available</p>
              <p className="mt-1 text-2xl font-bold">{trainedModels.length}</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
              <Brain className="h-6 w-6 text-primary" />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border/40 bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Reports</p>
              <p className="mt-1 text-2xl font-bold">{stats?.total_analyses ?? 0}</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-500/10">
              <Box className="h-6 w-6 text-purple-500" />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border/40 bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Dataset Status</p>
              <p className="mt-1 text-sm font-bold text-green-600">Connected</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-orange-500/10">
              <Database className="h-6 w-6 text-orange-500" />
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border/40 bg-card p-6">
        <div className="flex items-center justify-between gap-4">
          <div><h2 className="text-lg font-semibold">Appointments</h2><p className="mt-1 text-sm text-muted-foreground">Your real appointment requests and care-team updates.</p></div>
          <a href="/appointments" className="text-sm font-medium text-primary hover:underline">View all</a>
        </div>
        {appointments.length === 0 ? <p className="mt-6 text-sm text-muted-foreground">No appointments yet. Use Find Doctors to request a consultation.</p> : <div className="mt-5 space-y-3">{appointments.slice(0, 3).map((appointment) => <div key={appointment.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border/40 bg-secondary/20 p-4"><div><p className="font-medium">{appointment.doctor_name || 'Doctor'}</p><p className="text-sm text-muted-foreground">{new Date(appointment.appointment_at).toLocaleString()}</p></div><span className="rounded-full bg-secondary px-3 py-1 text-xs capitalize">{appointment.status}</span></div>)}</div>}
      </div>

      {/* AI System Status */}
      <div className="rounded-xl border border-border/40 bg-card p-6">
        <h2 className="text-lg font-semibold">AI System Status</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Current status of model architectures
        </p>

        {isLoading ? (
          <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4 animate-spin" />
            Loading model status...
          </div>
        ) : trainedModels.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <AlertCircle className="h-8 w-8 text-muted-foreground" />
            <p className="mt-2 text-sm text-muted-foreground">
              No trained models available
            </p>
          </div>
        ) : (
          <div className="mt-6 space-y-4">
            {trainedModels.map((model) => (
              <div
                key={model.model_name}
                className="flex items-center justify-between rounded-lg border border-border/40 bg-secondary/30 p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Brain className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{model.model_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {model.architecture} - {model.num_classes} classes
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="flex h-2 w-2 rounded-full bg-green-500" />
                  <span className="text-sm font-medium text-green-600">Ready</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Activity */}
      <div className="rounded-xl border border-border/40 bg-card p-6">
        <h2 className="text-lg font-semibold">Recent Activity</h2>

        {stats && stats.total_analyses > 0 ? (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between rounded-lg border border-border/40 bg-secondary/30 p-4">
              <div>
                <p className="font-medium">Total Analyses</p>
                <p className="text-sm text-muted-foreground">{stats.total_analyses} MRI images analyzed</p>
              </div>
              <Scan className="h-6 w-6 text-primary" />
            </div>
            {stats.average_confidence > 0 && (
              <div className="flex items-center justify-between rounded-lg border border-border/40 bg-secondary/30 p-4">
                <div>
                  <p className="font-medium">Average Confidence</p>
                  <p className="text-sm text-muted-foreground">{(stats.average_confidence * 100).toFixed(1)}%</p>
                </div>
                <Brain className="h-6 w-6 text-primary" />
              </div>
            )}
          </div>
        ) : (
          <div className="mt-6 flex flex-col items-center justify-center py-12 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
              <Scan className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="mt-4 font-medium">No analysis activity yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Upload an MRI image to start your first analysis
            </p>
            <a
              href="/analysis"
              className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              Start Analysis
            </a>
          </div>
        )}
      </div>

      {/* Medical Disclaimer */}
      <div className="rounded-lg border border-orange-500/30 bg-orange-500/10 p-4">
        <p className="text-xs text-orange-600 dark:text-orange-400">
          <strong>Research Disclaimer:</strong> This platform is for educational and
          research purposes only. Predictions are made by trained AI models but should not
          replace professional medical diagnosis.
        </p>
      </div>
    </div>
  )
}
