import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { analysisApi } from '@/services/api'
import { AnalysisRecord } from '@/types'
import { Search, Filter, FolderOpen, Brain, Clock, AlertCircle } from 'lucide-react'

export default function CasesPage() {
  const { user } = useAuth()
  const [records, setRecords] = useState<AnalysisRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    const loadRecords = async () => {
      if (!user?.id) {
        setIsLoading(false)
        return
      }

      try {
        const data = await analysisApi.getRecords(user.id)
        setRecords(data)
      } catch (err) {
        console.error('Failed to load records:', err)
        setError('Failed to load analysis records')
      } finally {
        setIsLoading(false)
      }
    }
    loadRecords()
  }, [user?.id])

  const filteredRecords = records.filter((record) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      record.predicted_class.toLowerCase().includes(query) ||
      record.model_name.toLowerCase().includes(query) ||
      record.image_name.toLowerCase().includes(query)
    )
  })

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Cases</h1>
        <p className="mt-1 text-muted-foreground">
          Manage and review your analysis records
        </p>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by class, model, or image name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-10 w-full rounded-lg border border-border/40 bg-background pl-9 pr-4 text-sm placeholder:text-muted-foreground focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <button className="flex items-center justify-center gap-2 rounded-lg border border-border/40 bg-card px-4 py-2 text-sm font-medium transition-colors hover:bg-secondary">
          <Filter className="h-4 w-4" />
          Filters
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/50 bg-red-500/10 px-4 py-3 text-sm text-red-600">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <span className="ml-3 text-muted-foreground">Loading records...</span>
        </div>
      ) : filteredRecords.length === 0 ? (
        /* Empty State */
        <div className="flex flex-col items-center justify-center rounded-xl border border-border/40 bg-card py-16">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-secondary">
            <FolderOpen className="h-10 w-10 text-muted-foreground" />
          </div>
          <p className="mt-4 font-medium">No cases yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {searchQuery ? 'No records match your search' : 'Analysis records will appear here after you run your first analysis'}
          </p>
          {!searchQuery && (
            <a
              href="/analysis"
              className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              Start Analysis
            </a>
          )}
        </div>
      ) : (
        /* Records Table */
        <div className="rounded-xl border border-border/40 bg-card overflow-hidden">
          <table className="w-full">
            <thead className="border-b border-border/40 bg-secondary/30">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Date</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Image</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Model</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Prediction</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Confidence</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {filteredRecords.map((record) => (
                <tr key={record.id} className="hover:bg-secondary/20 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      {formatDate(record.created_at)}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">{record.image_name}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Brain className="h-4 w-4 text-primary" />
                      <span className="text-sm">{record.model_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-primary/10 px-2 py-1 text-sm font-medium text-primary">
                      {record.predicted_class}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{(record.confidence * 100).toFixed(1)}%</td>
                  <td className="px-4 py-3">
                    <span className={`rounded px-2 py-1 text-xs font-medium ${
                      record.status === 'completed'
                        ? 'bg-green-500/10 text-green-600'
                        : record.status === 'failed'
                        ? 'bg-red-500/10 text-red-600'
                        : 'bg-yellow-500/10 text-yellow-600'
                    }`}>
                      {record.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Record Count */}
      {filteredRecords.length > 0 && (
        <p className="text-sm text-muted-foreground">
          Showing {filteredRecords.length} of {records.length} records
        </p>
      )}
    </div>
  )
}