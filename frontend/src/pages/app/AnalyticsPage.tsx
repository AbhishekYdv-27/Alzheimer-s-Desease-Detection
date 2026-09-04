import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { analysisApi } from '@/services/api'
import { BarChart3, PieChart, TrendingUp, Brain, Scan } from 'lucide-react'

interface AnalysisStats {
  total_analyses: number
  by_class: Record<string, number>
  average_confidence: number
}

export default function AnalyticsPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<AnalysisStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadStats = async () => {
      if (!user?.id) {
        setIsLoading(false)
        return
      }

      try {
        const data = await analysisApi.getStats(user.id)
        setStats(data)
      } catch (err) {
        console.error('Failed to load stats:', err)
      } finally {
        setIsLoading(false)
      }
    }
    loadStats()
  }, [user?.id])

  const hasData = stats && stats.total_analyses > 0

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <span className="ml-3 text-muted-foreground">Loading analytics...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="mt-1 text-muted-foreground">
          Visualize model performance and research metrics
        </p>
      </div>

      {/* Summary Stats */}
      {hasData && (
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-border/40 bg-card p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                <Scan className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Analyses</p>
                <p className="text-2xl font-bold">{stats.total_analyses}</p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-border/40 bg-card p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                <Brain className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Avg Confidence</p>
                <p className="text-2xl font-bold">{(stats.average_confidence * 100).toFixed(1)}%</p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-border/40 bg-card p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
                <PieChart className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Classes Used</p>
                <p className="text-2xl font-bold">{Object.keys(stats.by_class).length}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Class Distribution */}
      {hasData && Object.keys(stats.by_class).length > 0 && (
        <div className="rounded-xl border border-border/40 bg-card p-6">
          <div className="flex items-center gap-2">
            <PieChart className="h-5 w-5 text-primary" />
            <h3 className="font-semibold">Class Distribution</h3>
          </div>
          <div className="mt-6 space-y-4">
            {Object.entries(stats.by_class).map(([cls, count]) => {
              const percentage = (count / stats.total_analyses) * 100
              return (
                <div key={cls}>
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{cls}</span>
                    <span className="text-muted-foreground">{count} ({percentage.toFixed(1)}%)</span>
                  </div>
                  <div className="mt-1 h-3 w-full rounded-full bg-secondary">
                    <div
                      className="h-3 rounded-full bg-primary transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Real Model Metrics */}
      <div className="rounded-xl border border-border/40 bg-card p-6">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          <h3 className="font-semibold">Model Performance</h3>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Real metrics from trained models
        </p>
        <div className="mt-6 grid grid-cols-2 gap-4">
          <div className="rounded-lg bg-secondary/30 p-4">
            <p className="text-xs text-muted-foreground">ResNet50 Test Accuracy</p>
            <p className="text-xl font-bold text-green-600">95.52%</p>
          </div>
          <div className="rounded-lg bg-secondary/30 p-4">
            <p className="text-xs text-muted-foreground">ResNet50 Validation Accuracy</p>
            <p className="text-xl font-bold text-green-600">94.80%</p>
          </div>
        </div>
      </div>

      {/* Empty State */}
      {!hasData && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border/40 bg-card py-16">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-secondary">
            <BarChart3 className="h-10 w-10 text-muted-foreground" />
          </div>
          <p className="mt-4 font-medium">No analytics data available</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Analytics will be populated after running analyses
          </p>
          <a
            href="/analysis"
            className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Start Analysis
          </a>
        </div>
      )}

      {/* Disclaimer */}
      <div className="rounded-lg border border-orange-500/30 bg-orange-500/10 p-4">
        <p className="text-xs text-orange-600 dark:text-orange-400">
          <strong>Note:</strong> Analytics are based on your analysis history.
          This platform is for research purposes only.
        </p>
      </div>
    </div>
  )
}